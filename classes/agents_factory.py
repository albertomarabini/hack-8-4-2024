import os
from typing import TYPE_CHECKING, Any, Dict, Optional
from langchain_core.pydantic_v1 import BaseModel, Field

## MODELS
from langchain_openai import ChatOpenAI

## EMBEDDINGS
from langchain_openai.embeddings import OpenAIEmbeddings

os.environ["OPENAI_API_KEY"] = "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"

# Testing for Bosch
# from langchain_experimental.llms.ollama_functions import OllamaFunctions

class AgentFactory:
    def buildLLM(self, model: str, temp: float = 0.0, **kwargs) -> any:
        match model:
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
