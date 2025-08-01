from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from bazica import Bazica
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get your OpenAI API key from https://beta.openai.com/account/api-keys
# and set it as an environment variable in a .env file.
# OPENAI_API_KEY="your-api-key"

llm = ChatOpenAI(temperature=0)
conversation = ConversationChain(llm=llm, verbose=True)

def get_saju(year, month, day, hour):
    bazi = Bazica(datetime.datetime(year, month, day, hour))
    return bazi.get_bazi()

def main():
    print("사주팔자 챗봇에 오신 것을 환영합니다!")
    print("생년월일시를 입력해주세요 (예: 1990 1 1 12)")
    
    while True:
        try:
            year, month, day, hour = map(int, input("You: ").split())
            saju_data = get_saju(year, month, day, hour)
            print(f"당신의 사주팔자: {saju_data}")
            
            # Now, let's use the chatbot to interpret the Saju
            prompt = f"이 사주팔자에 대해 설명해주세요: {saju_data}"
            response = conversation.predict(input=prompt)
            print(f"Bot: {response}")
            break

        except ValueError:
            print("잘못된 형식입니다. 다시 입력해주세요.")
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")
            break

    print("\n대화를 시작합니다. 종료하려면 'quit' 또는 'exit'을 입력하세요.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        response = conversation.predict(input=user_input)
        print(f"Bot: {response}")

if __name__ == "__main__":
    main()
