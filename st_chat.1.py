from __future__ import annotations
from pydantic import BaseModel
import streamlit as st
from classes.utils import stFileManager, stInjectCSS, stClock, stChat, stGetterSetter
from typing import Optional
from classes.flask_client import FlaskClient

## INITIALIZE REMOTE PROCESS EXECUTION
class ChatBotClient(FlaskClient, stGetterSetter):
    def __init__(self, chat_control: stChat, clock: stClock, llm: str):
        FlaskClient.__init__(self)
        stGetterSetter.__init__(self, "ChatBotClient")
        self.asynchronous = False
        self.add_event_listener("send_response", self.require_input)
        self.chat_control = chat_control
        self.clock = clock
        self.llm = llm
        running = self.get("is_running")
        if running == None:  # 1 page loaded
            self.set("is_running", False)
            self.require_input("Ready")
        elif running == True:  # 2 we are running
            self.listen_once()

    def stop_process(self):
        self.set("is_running", False)
        self.clock.stop()

    def set_llm(self, llm: str):
        previous_llm = self.llm
        self.llm = llm
        if self.get("is_running") == True and previous_llm != self.llm:
            self.run_remote_server()

    def return_input(self, value: str):
        if value is None or value == "" and self.get("is_running") == True:
            self.chat_control.get_input("", "assistant", self.return_input)
            return
        if self.get("is_running") != True:
            self.run_remote_server()
        print("- User Input received:", value)
        self.fire_event("send_msg", value)

    def require_input(self, prompt):
        print("- Input required ", prompt)
        if isinstance(prompt, str):
            prompt = {"content": prompt, "role": "assistant"}
        elif isinstance(prompt, list):
            prompt = prompt[0]
        print("- Input required ", prompt)
        self.chat_control.get_input(prompt["content"], prompt["role"], self.return_input)
        print("- Input required")

    def run_remote_server(self):
        self.set("is_running", True)
        self.fire_event("backend_run", self.llm)
        self.clock.start()

## INITIALIZE UI
st.set_page_config(layout="wide")
stInjectCSS("custom.css")

# Creating columns
col_chat = st.columns(1)[0]


# Initializing chat control
chat = stChat("chat_control", col_chat, 652)
clock = stClock(10, "clock", True)
controller = ChatBotClient(chat, clock, "gpt-4o")
