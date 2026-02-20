import chromadb
from typing import Annotated
from pydantic import Field
from agent_framework import tool
from random import randint
import asyncio
import os
from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from agent_framework.azure import AzureOpenAIResponsesClient

# 1. ChromaDB 클라이언트 설정 (메모리 모드)
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="mvp_tour_info")

# 2. 테스트용 사내 지식 데이터 추가
collection.add(
    documents=[
        "시애틀 투어 패키지: 3박 4일 일정으로 스페이스 니들 입장권이 포함되어 있습니다.",
        "MVPTour 특별 환전 서비스: 본사 1층에서 오전 9시부터 오후 4시까지 우대 환율을 제공합니다.",
        "예약 취소 규정: 여행 7일 전까지는 100% 환불 가능하며, 이후에는 50% 수수료가 발생합니다."
    ],
    ids=["doc1", "doc2", "doc3"]
)
print("📦 사내 지식 베이스 구축 완료!")


# [도구 1] 날씨 조회 함수
@tool(approval_mode="never_require")
def get_weather(
    location: Annotated[str, Field(description="날씨를 확인하려는 도시 또는 지역명")]
) -> str:
    """지정된 지역의 현재 날씨 정보를 가져옵니다."""
    conditions = ["맑음", "흐림", "비", "폭풍우"]
    print(f"🔍 [시스템] 날씨 도구 호출 중: {location}") # 호출 확인용
    return f"{location}의 날씨는 {conditions[randint(0, 3)]}이며, 기온은 {randint(10, 30)}°C입니다."

# [도구 2] 환율 조회 함수
@tool(approval_mode="never_require")
def get_exchange_rate(
    base_currency: Annotated[str, Field(description="기준 통화 코드 (예: USD, EUR)")],
    target_currency: Annotated[str, Field(description="대상 통화 코드 (예: KRW, JPY)")]
) -> str:
    """두 통화 간의 실시간 환율 정보를 가져옵니다."""
    print(f"🔍 [시스템] 환율 도구 호출 중: {base_currency} -> {target_currency}")
    
    if target_currency == "KRW":
        rate = randint(130000, 145000) / 100
    else:
        rate = randint(80, 150) / 100
        
    return f"현재 {base_currency} 대비 {target_currency}의 환율은 {rate}입니다."

@tool(approval_mode="never_require")
def search_travel_docs(
    query: Annotated[str, Field(description="여행 상품이나 회사 규정에 대해 검색할 키워드")]
) -> str:
    """사내 지식베이스(ChromaDB)에서 여행 상품 및 정책 정보를 검색합니다."""
    print(f"🔍 [RAG] 지식베이스 검색 중: '{query}'")
    
    # 유사도 기반 검색 수행 (가장 관련 있는 데이터 1건 추출)
    results = collection.query(query_texts=[query], n_results=1)
    
    if results['documents'][0]:
        return f"관련 정보 검색 결과: {results['documents'][0][0]}"
    else:
        return "관련된 정보를 찾을 수 없습니다."

load_dotenv()
deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")

print(deployment_name)
print(project_endpoint)

# 2. Azure CLI를 통한 인증 (로컬 개발 시 편리)
credential = AzureCliCredential()

print(credential)

# 3. 클라이언트 설정
client = AzureOpenAIResponsesClient(
    credential=credential,
    deployment_name=deployment_name,
    project_endpoint=project_endpoint
)

# 에이전트 생성 (기존 도구 + RAG 도구 추가)
agent = client.as_agent(
    instructions="""
    당신은 여행사 'MVPTour'의 상담원입니다. 
    날씨, 환율뿐만 아니라 사내 상품 정보나 규정에 대해서도 'search_travel_docs'를 통해 답변하세요.
    항상 '즐거운 여행의 시작, MVPTour입니다!'로 끝맺음하세요.
    """,
    name="MVPTour-Assistant",
    tools=[get_weather, get_exchange_rate, search_travel_docs]
)

async def main():
    print(f"✅ 멀티 능력을 갖춘 '{agent.name}'가 준비되었습니다.")
    
    # 3. 세션 생성 (대화 맥락 유지)
    session = agent.create_session()

    # 테스트 1: 외부 도구(날씨) 호출
    user_input = "시애틀 날씨 알려주세요."
    result = await agent.run(user_input, session=session)
    print(f"Agent: {result}\n")
    
    # 테스트 2: 내부 지식(RAG) 호출 - 상품 정보
    user_input = "시애틀 투어 패키지 구성은 어떻게 되나요?"
    result = await agent.run(user_input, session=session)
    print(f"Agent: {result}\n")

    # 테스트 3: 내부 지식(RAG) 호출 - 규정 확인
    user_input = "여행을 취소하면 환불을 얼마나 받을 수 있나요?"
    result = await agent.run(user_input, session=session)
    print(f"Agent: {result}\n")        

if __name__ == "__main__":
    asyncio.run(main())    