from typing import Annotated
from pydantic import Field
from agent_framework import tool
from random import randint
import asyncio
import os
from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from agent_framework.azure import AzureOpenAIResponsesClient

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

# ... (클라이언트 설정 생략) ...

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

agent = client.as_agent(
    instructions="""
    당신은 여행사 'MVPTour'의 상담원입니다. 
    고객에게 정중하게 인사하고, 여행 계획에 대해 도움을 줄 준비가 되었음을 알리세요.
    날씨나 환율 정보를 물어보면 제공된 도구를 사용하여 정확한 정보를 안내하세요.
    답변 끝에는 항상 '즐거운 여행의 시작, MVPTour입니다!'라는 문구를 붙여주세요.
    """,
    name="MVPTour-Assistant",
    tools=[get_weather, get_exchange_rate] # 작성한 도구들을 연결!
)

async def main():
    print(f"✅ 도구가 장착된 '{agent.name}'가 준비되었습니다.")

    # 테스트 입력
    user_input = "지금 원화 대비 달러의 환율은 어떤가요?"
    print(f"\n[나]: {user_input}")
    
    # 에이전트 실행 (도구가 필요하다고 판단되면 자동으로 함수를 실행합니다)
    result = await agent.run(user_input)
    print(f"\n[MVPTour 상담원]: {result}")

if __name__ == "__main__":
    asyncio.run(main())