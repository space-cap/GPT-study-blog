import PyPDF2
import pandas as pd
import re
from typing import List, Dict
import json


class PDFToKnowledgeConverter:
    def __init__(self):
        self.knowledge_base = []

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 텍스트 추출"""
        text = ""
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def extract_tables_from_pdf(self, pdf_path: str) -> List[pd.DataFrame]:
        """PDF에서 표 추출 (tabula-py 사용)"""
        try:
            import tabula

            tables = tabula.read_pdf(pdf_path, pages="all", multiple_tables=True)
            return tables
        except ImportError:
            print("tabula-py가 설치되지 않았습니다. pip install tabula-py")
            return []

    def clean_text(self, text: str) -> str:
        """텍스트 정제"""
        # 불필요한 공백, 특수문자 제거
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s가-힣.,?!]", " ", text)
        return text.strip()

    def split_into_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """텍스트를 청크로 분할"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
        return chunks

    def table_to_qa_pairs(self, table: pd.DataFrame) -> List[Dict]:
        """표를 Q&A 쌍으로 변환"""
        qa_pairs = []

        # 각 행을 질문-답변으로 변환
        for index, row in table.iterrows():
            for col in table.columns:
                if pd.notna(row[col]):
                    question = f"{col}에 대해 알려주세요."
                    answer = f"{col}은(는) {row[col]}입니다."

                    qa_pairs.append(
                        {
                            "question": question,
                            "answer": answer,
                            "source": "table",
                            "metadata": {"table_row": index, "column": col},
                        }
                    )

        return qa_pairs

    def text_to_knowledge_structure(self, text_chunks: List[str]) -> List[Dict]:
        """텍스트 청크를 지식 구조로 변환"""
        knowledge_items = []

        for i, chunk in enumerate(text_chunks):
            # 간단한 제목 추출 (첫 문장을 제목으로 사용)
            sentences = chunk.split(".")
            title = (
                sentences[0][:50] + "..." if len(sentences[0]) > 50 else sentences[0]
            )

            knowledge_item = {
                "id": f"doc_chunk_{i}",
                "title": title,
                "content": chunk,
                "type": "document",
                "metadata": {"chunk_index": i, "word_count": len(chunk.split())},
            }
            knowledge_items.append(knowledge_item)

        return knowledge_items

    def process_pdf(self, pdf_path: str) -> Dict:
        """PDF 전체 처리 파이프라인"""
        result = {"document_knowledge": [], "table_qa_pairs": [], "summary": {}}

        # 1. 텍스트 추출 및 처리
        print("텍스트 추출 중...")
        raw_text = self.extract_text_from_pdf(pdf_path)
        cleaned_text = self.clean_text(raw_text)
        text_chunks = self.split_into_chunks(cleaned_text)

        # 2. 텍스트를 지식 구조로 변환
        print("텍스트 지식 구조 생성 중...")
        result["document_knowledge"] = self.text_to_knowledge_structure(text_chunks)

        # 3. 표 추출 및 Q&A 쌍 생성
        print("표 추출 및 Q&A 생성 중...")
        tables = self.extract_tables_from_pdf(pdf_path)

        for table_idx, table in enumerate(tables):
            if not table.empty:
                qa_pairs = self.table_to_qa_pairs(table)
                for qa in qa_pairs:
                    qa["metadata"]["table_index"] = table_idx
                result["table_qa_pairs"].extend(qa_pairs)

        # 4. 요약 정보
        result["summary"] = {
            "total_text_chunks": len(text_chunks),
            "total_tables": len(tables),
            "total_qa_pairs": len(result["table_qa_pairs"]),
            "total_knowledge_items": len(result["document_knowledge"]),
        }

        return result

    def save_knowledge_base(self, knowledge_data: Dict, output_path: str):
        """지식 베이스를 JSON 파일로 저장"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
        print(f"지식 베이스가 {output_path}에 저장되었습니다.")


# 사용 예시
if __name__ == "__main__":
    # 필요한 패키지 설치
    # pip install PyPDF2 pandas tabula-py

    converter = PDFToKnowledgeConverter()

    # PDF 파일 경로
    pdf_file = ".\20250630_더존비즈온.pdf"

    try:
        # PDF 처리
        knowledge_data = converter.process_pdf(pdf_file)

        # 결과 출력
        print("\n=== 처리 결과 요약 ===")
        print(f"텍스트 청크 수: {knowledge_data['summary']['total_text_chunks']}")
        print(f"추출된 표 수: {knowledge_data['summary']['total_tables']}")
        print(f"생성된 Q&A 쌍 수: {knowledge_data['summary']['total_qa_pairs']}")

        # 지식 베이스 저장
        converter.save_knowledge_base(knowledge_data, "knowledge_base.json")

        # 샘플 출력
        if knowledge_data["document_knowledge"]:
            print("\n=== 문서 지식 샘플 ===")
            print(knowledge_data["document_knowledge"][0])

        if knowledge_data["table_qa_pairs"]:
            print("\n=== 표 Q&A 샘플 ===")
            print(knowledge_data["table_qa_pairs"][0])

    except Exception as e:
        print(f"처리 중 오류 발생: {e}")
