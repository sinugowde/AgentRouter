"""LangChain Integration Example with AgentRouter."""

import os
from agentrouter.langchain_adapter import ChatAgentRouter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

api_key = os.environ.get("AGENTROUTER_API_KEY", "sk-***")

# Initialize LangChain Chat Model
llm = ChatAgentRouter(
    api_key=api_key,
    model="gpt-6-astra",
    temperature=0.7
)

# Build a LCEL pipeline
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an assistant that summarizes concepts into exactly 3 bullet points."),
    ("user", "Explain the concept of: {topic}")
])

chain = prompt | llm | StrOutputParser()

result = chain.invoke({"topic": "Retrieval-Augmented Generation (RAG)"})
print("LangChain Pipeline Output:\n")
print(result)
