import os
from typing import TYPE_CHECKING, Any, Dict, Optional
from crewai import Crew, Process, Agent, Task
from langchain_core.pydantic_v1 import BaseModel, Field

## MODELS
from langchain_openai import ChatOpenAI
from langchain_community.llms import HuggingFaceEndpoint
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama
from langchain_mistralai import ChatMistralAI

## EMBEDDINGS
from langchain_openai.embeddings import OpenAIEmbeddings

os.environ["TAVILY_API_KEY"]='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'
os.environ["OPENAI_API_KEY"] = "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"
os.environ["GROQ_API_KEY"]= "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"
os.environ["ANTHROPIC_API_KEY"] ="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"
os.environ["MISTRAL_API_KEY"] ="FO03izNumFoz6ACIUAS2DVXKZHnOnxWI"

# Testing for Bosch
# from langchain_experimental.llms.ollama_functions import OllamaFunctions

class AgentFactory:
    def buildLLM(self, model: str, temp: float = 0.0, **kwargs) -> any:
        match model:
            case _ if model.startswith("HuggingFace"):
                api_key = os.environ["HUGGINGFACE_API_KEY"]
                llm = HuggingFaceEndpoint(
                    temperature=temp,
                    repo_id=model.replace("HuggingFace ", ""),
                    huggingfacehub_api_token=api_key,
                    **kwargs
                )
            case _ if "mistral" in model.lower() or "open" in model.lower():
                llm = ChatMistralAI(temperature=temp, model=model, **kwargs)
            case _ if model.startswith("llama") or model.startswith("mixtral"):
                llm = ChatGroq(temperature=temp, model_name=model, **kwargs)
            case _ if model.startswith("claude"):
                llm = ChatAnthropic(temperature=temp, model=model, **kwargs)
            case _ if model.startswith("ollama"):
                llm = ChatOllama(
                    temperature=temp,
                    model=model.replace("ollama ", ""),
                    base_url="http://localhost:11434",
                    **kwargs
                )
            case _ if model == "gpt-4o":
                llm = ChatOpenAI(
                    temperature=temp, model = "gpt-4o-2024-05-13", **kwargs
                )
            case _:
                llm = ChatOpenAI(
                    temperature=temp, model = "gpt-3.5-turbo-0125" # #model ="gpt-3.5-turbo" # model="gpt-4-turbo" #  #
                    , **kwargs
                )  # model="gpt-4-turbo-preview")
        return llm

            # case _ if model.startswith("Bosch"):
            #     # llm = OllamaFunctions(
            #     #     endpoint="https://dev-mixtral-msp.de.bosch.com/v1",
            #     #     # mistral_api_key="none",
            #     #     temperature=temp,
            #     #     max_tokens=5000,
            #     #     format="json",
            #     #     model="mistralai/Mixtral-8x7B-Instruct-v0.1"
            #     # )
            #     # llm = ChatMistralAI(
            #     #     temperature=temp,
            #     #     model = "mistralai/Mixtral-8x7B-Instruct-v0.1",
            #     #     endpoint = "https://ews-emea.api.bosch.com/knowledge/insight-and-analytics/llms/d/v1"
            #     # )

class ReflectionAgentsFactory(AgentFactory):
    class AgentProps(BaseModel):
        role: str
        backstory: str
        goal: str
        llm: str
        temperature: float
        tools: Optional[list] = []

    def __init__(self):
        self.crewmgr_llm = ChatOpenAI(
            temperature=0, model="gpt-4-turbo"
        )  # model="gpt-4-turbo-preview")

    def initialize_agents(
        self,
        mgr_props: "ReflectionAgentsFactory.AgentProps",
        ast_props: "ReflectionAgentsFactory.AgentProps",
        mgr_callbacks: list = [],
        ast_callbacks: list = [],
        tools: dict = {},
    ):
        mgr_tools = []
        for tool in mgr_props.tools:
            if tool in tools:
                print("- Adding Mgr tool: ", tool)
                mgr_tools.append(tools[tool])

        self.mgr = Agent(
            role=mgr_props.role,
            backstory=mgr_props.backstory,
            goal=mgr_props.goal,
            tools=mgr_tools,
            llm=self.buildLLM(mgr_props.llm, mgr_props.temperature),
            callbacks=mgr_callbacks,
            __name__="Supervisor",
        )

        ast_tools = []
        for tool in ast_props.tools:
            if tool in tools:
                print("- Adding ast tool: ", tool)
                ast_tools.append(tools[tool])

        self.ast = Agent(
            role=ast_props.role,
            backstory=ast_props.backstory,
            goal=ast_props.goal,
            tools=ast_tools,
            llm=self.buildLLM(ast_props.llm, ast_props.temperature),
            callbacks=ast_callbacks,
            __name__="Assistant",
        )

    def initialize_crew(self, task_mgr, task_ast, hierarchical: bool):
        if not hierarchical:
            task_mgr = (
                """
                For the following task you will be using an assistent (the only one on your list).
                Please provide the task description and the expected output.
                This is your specific task: """
                + task_mgr
            )
        self.mgr_task = Task(
            description=task_mgr,
            agent=self.mgr,
            expected_output="The expected output should have been provided in the description of the task",
        )

        self.ast_task = Task(
            description=task_ast,
            agent=self.ast,
            expected_output="The expected output  should have been provided in the description of the task or wild be provided during the interaction",
        )

        self.crew = Crew(
            tasks=[self.mgr_task, self.ast_task],
            agents=[self.mgr, self.ast],
            manager_llm=self.crewmgr_llm if hierarchical else None,
            process=Process.hierarchical if hierarchical else Process.sequential,
            verbose=5,
            memory=True,
            # full_output=True,
            # embedder={
            #         "provider": "openai",
            #         "config":{
            #                 "model": 'text-embedding-3-small'
            #         }
            # }
        )
