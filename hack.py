import streamlit as st
from classes.utils import stInjectCSS, stClock, stChat, stGetterSetter
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import StrOutputParser
from langchain.chains import LLMChain
from classes.agents_factory import AgentFactory

class ChatBotClient(stGetterSetter):
    def __init__(self, chat_control: stChat, llm:str):
        stGetterSetter.__init__(self, "ChatBotClient")
        self.asynchronous = False
        self.chat_control = chat_control
        # self.clock = clock
        self.llm = llm
        self.history = []
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            MessagesPlaceholder(variable_name="history"),
            ("user", "{question}")
        ])
        self.llm_model = AgentFactory().buildLLM(model=llm, temp=0.0)
        self.chain = self.prompt | self.llm_model | StrOutputParser()

    def return_input(self, value: str):
        if value is None or value == "" and self.get("is_running") == True:
            self.chat_control.get_input("Please provide input", "assistant", self.return_input)
            return
        if(self.get("is_running") != True):
            self.run_chatbot()
        print("- User Input received:", value)
        response = self.handle_chat_msg(value)
        self.chat_control.add_message("assistant", response)

    def handle_chat_msg(self, question):
        self.history.append(("user", question))
        history = [{"role": role, "content": content} for role, content in self.history]
        response = self.chain.invoke({"history": history, "question": question})
        self.history.append(("assistant", response))
        return response

    def require_input(self, prompt):
        print("- Input required ", prompt)
        if isinstance(prompt, str):
            prompt = {"content": prompt, "role": "assistant"}
        elif isinstance(prompt, list):
            prompt = prompt[0]
        print("- Input required ", prompt)
        self.chat_control.get_input(prompt["content"], prompt["role"], self.return_input)
        print("- Input required")

    def run_chatbot(self):
        self.set("is_running", True)
        # self.clock.start()

## INITIALIZE UI
st.set_page_config(layout="wide")
stInjectCSS("custom.css")

# Creating columns
col_chat = st.columns(1)[0]

# TOOLBAR
go_col, spc_col, rst_col = col_chat.columns([2, 6, 2])

reset_button = rst_col.button("Reset")

# Initializing chat control
chat = stChat("chat_control", col_chat, 652)
# clock = stClock(10, "clock", True)
controller = ChatBotClient(chat, "gpt-4o")

if reset_button:
    chat.reset()
    controller.stop_process()

controller.require_input("Ready")
