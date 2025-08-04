import json
import sqlite3
from datetime import datetime
from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict

import mysql.connector
import fakeredis
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode


import os

# API 키를 환경변수로 관리하기 위한 설정 파일
from dotenv import load_dotenv

# API 키 정보 로드
load_dotenv()

# =============================================================================
# 1. 상태 정의 (메모리 아키텍처)
# =============================================================================


class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    user_info: Dict[str, Any]
    current_goal: str
    rag_context: List[str]
    tool_outputs: List[Dict[str, Any]]
    memory_candidates: List[Dict[str, Any]]


# =============================================================================
# 2. 메모리 시스템 (단기 + 장기)
# =============================================================================


class MemorySystem:
    def __init__(self):

        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")

        # 단기 메모리 (Redis)
        self.short_term = fakeredis.FakeRedis(decode_responses=True)

        # 장기 메모리 (MySQL + Chroma)
        self.mysql_conn = mysql.connector.connect(
            host="localhost",
            user=self.user,
            password=self.password,
            database="context_db",
        )

        # 벡터 저장소 (Chroma)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_store = Chroma(
            embedding_function=self.embeddings, persist_directory="./chroma_db"
        )

        self._setup_database()

    def _setup_database(self):
        cursor = self.mysql_conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_facts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255),
                fact_type VARCHAR(100),
                content TEXT,
                importance_score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self.mysql_conn.commit()

    def store_short_term(self, session_id: str, key: str, value: Any, ttl: int = 3600):
        """단기 메모리에 저장 (1시간 TTL)"""
        self.short_term.setex(f"{session_id}:{key}", ttl, json.dumps(value))

    def get_short_term(self, session_id: str, key: str) -> Optional[Any]:
        """단기 메모리에서 조회"""
        data = self.short_term.get(f"{session_id}:{key}")
        return json.loads(data) if data else None

    def store_long_term(self, user_id: str, fact: Dict[str, Any]):
        """중요한 정보를 장기 메모리에 저장"""
        cursor = self.mysql_conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_facts (user_id, fact_type, content, importance_score)
            VALUES (%s, %s, %s, %s)
        """,
            (user_id, fact["type"], fact["content"], fact["importance"]),
        )
        self.mysql_conn.commit()

        # 벡터 저장소에도 추가
        doc = Document(
            page_content=fact["content"],
            metadata={"user_id": user_id, "type": fact["type"]},
        )
        self.vector_store.add_documents([doc])


# =============================================================================
# 3. 정보 중요도 평가기
# =============================================================================


class ImportanceEvaluator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.weights = {
            "explicit": 0.30,
            "stable": 0.25,
            "reuse": 0.20,
            "novelty": 0.15,
            "recurrence": 0.10,
        }

    def evaluate(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """정보의 중요도를 다차원으로 평가"""

        # 명시적 신호 (사용자가 "기억해", "중요해" 등 언급)
        explicit_score = self._check_explicit_cues(text)

        # 안정성 (시간이 지나도 변하지 않는 정보)
        stability_score = self._check_stability(text)

        # 재사용 가능성 (LLM으로 평가)
        reuse_score = self._predict_reuse_likelihood(text, context)

        # 새로움 (기존 메모리와 중복되지 않음)
        novelty_score = self._check_novelty(text, context)

        # 반복성 (대화 내에서 여러 번 언급)
        recurrence_score = self._check_recurrence(text, context)

        # 최종 중요도 점수 계산
        total_score = (
            self.weights["explicit"] * explicit_score
            + self.weights["stable"] * stability_score
            + self.weights["reuse"] * reuse_score
            + self.weights["novelty"] * novelty_score
            + self.weights["recurrence"] * recurrence_score
        )

        return {
            "total_score": total_score,
            "components": {
                "explicit": explicit_score,
                "stable": stability_score,
                "reuse": reuse_score,
                "novelty": novelty_score,
                "recurrence": recurrence_score,
            },
            "should_store": total_score >= 0.60,
        }

    def _check_explicit_cues(self, text: str) -> float:
        explicit_keywords = ["기억해", "메모해", "중요해", "저장해", "잊지마"]
        return 1.0 if any(keyword in text for keyword in explicit_keywords) else 0.0

    def _check_stability(self, text: str) -> float:
        # 간단한 휴리스틱 - 실제로는 더 정교한 NER 사용
        stable_patterns = ["생일", "주소", "전화번호", "이름", "선호도"]
        return 1.0 if any(pattern in text for pattern in stable_patterns) else 0.0

    def _predict_reuse_likelihood(self, text: str, context: Dict[str, Any]) -> float:
        prompt = ChatPromptTemplate.from_template(
            """
        다음 정보가 향후 대화에서 재사용될 가능성이 높은지 평가해주세요.
        
        정보: {text}
        현재 맥락: {context}
        
        0(전혀 재사용 안됨) ~ 1(매우 자주 재사용됨) 사이의 점수로 답해주세요.
        점수만 숫자로 답하세요.
        """
        )

        try:
            response = self.llm.invoke(prompt.format(text=text, context=str(context)))
            return float(response.content.strip())
        except:
            return 0.5  # 기본값

    def _check_novelty(self, text: str, context: Dict[str, Any]) -> float:
        # 기존 메모리와의 유사도 체크 (간단한 키워드 기반)
        existing_facts = context.get("existing_facts", [])
        if not existing_facts:
            return 1.0

        # 실제로는 임베딩 유사도 계산
        keywords = text.lower().split()
        for fact in existing_facts:
            fact_keywords = fact.lower().split()
            overlap = len(set(keywords) & set(fact_keywords))
            if overlap > len(keywords) * 0.5:
                return 0.0
        return 1.0

    def _check_recurrence(self, text: str, context: Dict[str, Any]) -> float:
        recent_messages = context.get("recent_messages", [])
        if len(recent_messages) < 2:
            return 0.0

        # 키워드 기반 반복 체크
        keywords = set(text.lower().split())
        mention_count = 0
        for msg in recent_messages[-5:]:  # 최근 5개 메시지만 체크
            msg_keywords = set(msg.lower().split())
            if keywords & msg_keywords:
                mention_count += 1

        return 1.0 if mention_count >= 2 else 0.0


# =============================================================================
# 4. RAG 시스템
# =============================================================================


class RAGRetriever:
    def __init__(self, memory_system: MemorySystem):
        self.memory = memory_system

    def retrieve_relevant_context(
        self, query: str, user_id: str, k: int = 3
    ) -> List[str]:
        """사용자 질의에 관련된 컨텍스트 검색"""

        # 벡터 검색
        docs = self.memory.vector_store.similarity_search(
            query, k=k, filter={"user_id": user_id}
        )

        # MySQL에서 최근 중요한 사실들도 가져오기
        cursor = self.memory.mysql_conn.cursor()
        cursor.execute(
            """
            SELECT content FROM user_facts 
            WHERE user_id = %s AND importance_score > 0.7
            ORDER BY last_used DESC LIMIT 3
        """,
            (user_id,),
        )

        mysql_facts = [row[0] for row in cursor.fetchall()]

        # 결합
        context = [doc.page_content for doc in docs] + mysql_facts
        return list(set(context))  # 중복 제거


# =============================================================================
# 5. 메인 에이전트 시스템 (LangGraph)
# =============================================================================


class ContextEngineeringAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        self.memory = MemorySystem()
        self.evaluator = ImportanceEvaluator(self.llm)
        self.rag = RAGRetriever(self.memory)

        # LangGraph 워크플로우 구성
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(ConversationState)

        # 노드 정의
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("evaluate_memory", self._evaluate_memory_node)
        workflow.add_node("update_memory", self._update_memory_node)

        # 플로우 정의
        workflow.set_entry_point("retrieve_context")
        workflow.add_edge("retrieve_context", "generate_response")
        workflow.add_edge("generate_response", "evaluate_memory")
        workflow.add_edge("evaluate_memory", "update_memory")
        workflow.add_edge("update_memory", END)

        return workflow.compile()

    def _retrieve_context_node(self, state: ConversationState) -> ConversationState:
        """1단계: 관련 컨텍스트 검색"""
        last_message = state["messages"][-1].content if state["messages"] else ""
        user_id = state.get("user_info", {}).get("user_id", "default")

        # RAG 검색
        rag_context = self.rag.retrieve_relevant_context(last_message, user_id)

        # 단기 메모리에서 세션 정보 가져오기
        session_id = state.get("user_info", {}).get("session_id", "default")
        session_context = self.memory.get_short_term(session_id, "context") or []

        state["rag_context"] = rag_context + session_context
        return state

    def _generate_response_node(self, state: ConversationState) -> ConversationState:
        """2단계: 컨텍스트를 활용한 응답 생성"""

        # 컨텍스트 조합
        context_str = "\n".join(state["rag_context"])
        messages_str = "\n".join([msg.content for msg in state["messages"][-3:]])

        prompt = ChatPromptTemplate.from_template(
            """
        당신은 도움이 되는 AI 어시스턴트입니다.
        
        관련 컨텍스트:
        {context}
        
        최근 대화:
        {messages}
        
        사용자의 현재 질문에 컨텍스트를 활용해서 도움이 되는 답변을 해주세요.
        """
        )

        response = self.llm.invoke(
            prompt.format(context=context_str, messages=messages_str)
        )

        # 응답을 메시지에 추가
        from langchain_core.messages import AIMessage

        state["messages"].append(AIMessage(content=response.content))

        return state

    def _evaluate_memory_node(self, state: ConversationState) -> ConversationState:
        """3단계: 메모리 저장 가치 평가"""

        candidates = []
        recent_messages = [msg.content for msg in state["messages"][-3:]]

        for msg_content in recent_messages:
            if len(msg_content.strip()) > 10:  # 너무 짧은 메시지 제외
                evaluation = self.evaluator.evaluate(
                    msg_content,
                    {
                        "recent_messages": recent_messages,
                        "current_goal": state.get("current_goal", ""),
                        "existing_facts": [],  # 실제로는 기존 사실들 로드
                    },
                )

                if evaluation["should_store"]:
                    candidates.append(
                        {
                            "content": msg_content,
                            "evaluation": evaluation,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        state["memory_candidates"] = candidates
        return state

    def _update_memory_node(self, state: ConversationState) -> ConversationState:
        """4단계: 메모리 업데이트"""

        user_id = state.get("user_info", {}).get("user_id", "default")
        session_id = state.get("user_info", {}).get("session_id", "default")

        # 단기 메모리 업데이트
        session_context = [msg.content for msg in state["messages"][-5:]]
        self.memory.store_short_term(session_id, "context", session_context)

        # 장기 메모리 업데이트
        for candidate in state["memory_candidates"]:
            fact = {
                "type": "user_interaction",
                "content": candidate["content"],
                "importance": candidate["evaluation"]["total_score"],
            }
            self.memory.store_long_term(user_id, fact)

        return state

    def chat(
        self, user_input: str, user_id: str = "default", session_id: str = "default"
    ) -> str:
        """메인 채팅 인터페이스"""

        from langchain_core.messages import HumanMessage

        initial_state = ConversationState(
            messages=[HumanMessage(content=user_input)],
            user_info={"user_id": user_id, "session_id": session_id},
            current_goal="general_chat",
            rag_context=[],
            tool_outputs=[],
            memory_candidates=[],
        )

        # 워크플로우 실행
        final_state = self.workflow.invoke(initial_state)

        # 마지막 AI 메시지 반환
        ai_messages = [
            msg
            for msg in final_state["messages"]
            if hasattr(msg, "type") and msg.type == "ai"
        ]
        return (
            ai_messages[-1].content
            if ai_messages
            else "죄송합니다. 응답을 생성할 수 없습니다."
        )


if __name__ == "__main__":
    print("main")
    ms = MemorySystem()
