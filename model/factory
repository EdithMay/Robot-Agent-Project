from abc import ABC, abstractmethod
from typing import Optional

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI

from agent_project.utils.config_handler import rag_conf


# 模型工厂接口
class BaseModelFactory(ABC):
    @abstractmethod
    #  返回一个生成器，可以是Embeddings或BaseChatModel
    def generator(self) ->Optional[Embeddings | BaseChatModel]:
        pass
class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatOpenAI(
            model=rag_conf["chat_model_name"],
            api_key=rag_conf["api_key"],
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
class EmbeddingModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return DashScopeEmbeddings(
            model=rag_conf["embedding_model_name"],
            dashscope_api_key=rag_conf["api_key"],
        )
chat_model = ChatModelFactory().generator()
embedding_model = EmbeddingModelFactory().generator()
