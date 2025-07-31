from langgraph.graph import StateGraph, START, END
from langgraph.cache.memory import InMemoryCache
from langgraph.types import CachePolicy
from typing_extensions import TypedDict


class State(TypedDict):
    input: str
    output: str


def generate_answer(state: State):
    # 비용이 많이 드는 작업 시뮬레이션
    import time

    time.sleep(2)
    return {"output": f"Generated: {state['input']}"}


def get_cache_key(state: State):
    return state["input"]


# 캐시 설정
cache = InMemoryCache()

# 그래프 구축
builder = StateGraph(State)
builder.add_node(
    "generate_answer",
    generate_answer,
    cache_policy=CachePolicy(ttl=120, key_func=get_cache_key),
)

builder.add_edge(START, "generate_answer")
builder.add_edge("generate_answer", END)

# 캐시와 함께 컴파일
graph = builder.compile(cache=cache)

# 사용
result = graph.invoke({"input": "Hello"})
print(result)  # {'output': 'Generated: Hello'})
