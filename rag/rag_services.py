'''
RAG总结服务:
1.用户提问
2.搜索参考资料
2.将提问和参考资料提交给模型。进行总结回复
'''
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from agent_project.model.factory import chat_model
from agent_project.rag.vector_store import VectorStoreService
from agent_project.utils.prompt_loader import load_rag_prompts

def print_prompt(prompt):
    print("提示词内容：")
    print(prompt)
    print("*"*20)
    return prompt

class RagSummarizeService(object):
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever =self.vector_store.get_retriever() # 获取检索器对象
        self.promt_text = load_rag_prompts()#加载RAG提示词文本
        # 创建一个提示模板对象，使用加载的RAG提示词文本作为模板内容
        self.promt_template = PromptTemplate.from_template(self.promt_text)
        self.model= chat_model #使用工厂模式创建一个聊天模型实例
        self.chain =self._init_chain()
    def _init_chain(self):
        chain = self.promt_template | print_prompt |self.model | StrOutputParser() # 将提示模板和聊天模型组合成一个链式调用对象
        return chain

    def retriever_docs(self,query):
        # 调用检索器对象的invoke方法，传入用户的查询文本，获取相关文档
        return self.retriever.invoke(query)
    def rag_summarizes(self,query):
        # 获取相关文档
        print(f"检索词为{query}")
        docs = self.retriever_docs(query)
        # 将用户的查询文本和相关文档作为输入，传递给链式调用对象进行处理，得到总结结果
        context =""
        num = 0
        for doc in docs:
            num+=1
            context+=f"{doc.page_content} | 参考元数据：{doc.metadata}\n"
        print(f"共检索到{num}条相关文档，作为上下文传递给模型进行总结")
        return self.chain.invoke(
            {
                "input":query,
                "context":context
            }
        )

if __name__ == '__main__':
    rag = RagSummarizeService()
    print(rag.rag_summarizes("机器人连不上WIFI"))