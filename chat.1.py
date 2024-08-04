import asyncio
from classes.flask_client import FlaskClient
from classes.agents_factory import AgentFactory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import StrOutputParser
from langchain.chains import LLMChain

class ChatbotServer(FlaskClient):
    def __init__(self):
        super().__init__(asynchronous = True)
        self.add_event_listener("send_msg", self.handle_chat_msg)
        self.add_event_listener("backend_run", self.handle_backend_run)
        self.start_listening()

    def handle_backend_run(self, llm):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            MessagesPlaceholder(variable_name="history"),
            ("user", "{question}")
        ])
        self.history = []
        llm = AgentFactory().buildLLM(model=llm, temp=0.0)
        print(f"Backend running with LLM: {llm}")
        self.chain = prompt | llm | StrOutputParser()

    def handle_chat_msg(self, question):
        print(f"Received question: {question}")
        self.history.append(("user", question))
        history = [{"role": role, "content": content} for role, content in self.history]
        response = self.chain.invoke({"history": history, "question": question})
        self.history.append(("assistant", response))
        self.fire_event("send_response", {"role": "assistant", "content": response})

if __name__ == "__main__":
    client = ChatbotServer()

    loop = asyncio.get_event_loop()
    loop.run_forever()
