import langchain
from langchain.chains import LLMMathChain
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI

langchain.debug = True

# llm = ChatOpenAI(temperature=0.5, model="thebloke__open-llama-7b-open-instruct-ggml__open-llama-7b-open-instruct.ggmlv3.q4_0.bin", openai_api_base='http://127.0.0.1:8080/v1')
llm = ChatOpenAI(temperature=0.5, model="thebloke__airoboros-m-7b-3.1.2-gguf__airoboros-m-7b-3.1.2.q5_k_m.gguf", openai_api_base='http://127.0.0.1:8080/v1')
# llm = ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo-0613")
llm_math_chain = LLMMathChain.from_llm(llm=llm, verbose=True)
tools = [
    Tool(
        name="Calculator",
        func=llm_math_chain.run,
        description="useful for when you need to answer questions about math"
    )
]

mrkl = initialize_agent(tools, llm, agent=AgentType.OPENAI_MULTI_FUNCTIONS, verbose=True)

aaa = mrkl.run("what is the square root of thirty six times the number of days in a week?")
# aaa = mrkl.run("Hello, how are you doing?")

print(aaa)
