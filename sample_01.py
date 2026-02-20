import asyncio
import os
from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from agent_framework.azure import AzureOpenAIResponsesClient

# 1. .env 파일로부터 환경 변수 로드
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

# 4. MVPTour 상담원(Agent) 생성
# as_agent 메서드는 지침과 이름을 가진 에이전트 객체를 반환합니다.
agent = client.as_agent(
    instructions="""
    당신은 여행사 'MVPTour'의 상담원입니다. 
    고객에게 정중하게 인사하고, 여행 계획에 대해 도움을 줄 준비가 되었음을 알리세요.
    답변 끝에는 항상 '즐거운 여행의 시작, MVPTour입니다!'라는 문구를 붙여주세요.
    """,
    name="MVPTour-Assistant"
)

async def main():
    print(f"✅ 에이전트 '{agent.name}'가 준비되었습니다.")

    # 5. 사용자 입력 구성
    user_input = "안녕하세요! 도쿄 여행 패키지 추천해 주세요."
    print(f"\n[나]: {user_input}")
    
    # 6. 에이전트 실행 (Non-streaming 방식)
    # 별도의 스레드 생성 단계 없이 agent.run()으로 즉시 답변을 받아옵니다.
    result = await agent.run(user_input)
    
    print(f"\n[MVPTour 상담원]: {result}")

if __name__ == "__main__":
    asyncio.run(main())