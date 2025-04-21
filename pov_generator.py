from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

def create_pov_from_text(text, mode):
    # modes: opposing, neutral, empathic
    llm = AzureChatOpenAI(
        azure_deployment="gpt-4.1",
        openai_api_version="2024-12-01-preview",
        temperature=0,
        max_retries=2
    )
    
    messages = [
        SystemMessage(content=f"You are an assistant that given a text generates a different point of view of the same topic. The interpretation needs to be from a {mode} point of view. The response must be in JSON format like this:\n{{\"mode\": \"{mode}\", \"alternativePov\": \"Text of the generated point of view\"}}")
        HumanMessage(content=f"Give me an alternative interpretation of this topic from an {mode} point of view:\n\n{text}\nThe response needs to be in JSON format:\n{{\"mode\": \"{mode}\", \"alternativePov\": \"Text of the generated point of view\"}}")
    ]

    response = llm.invoke(messages).content
    return response
