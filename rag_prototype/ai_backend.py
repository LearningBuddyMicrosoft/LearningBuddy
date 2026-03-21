from langchain_community.chat_models import ChatOllama

llm = ChatOllama(model = "llama3.1")

def ai_query(input : str) -> str:
    return llm.invoke(input).content