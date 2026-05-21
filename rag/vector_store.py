'''
向量存储服务
'''
import os.path

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_classic.retrievers  import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from agent_project.utils.config_handler import chroma_conf
from agent_project.model.factory import embedding_model,chat_model
from agent_project.utils.path_tool import get_abs_path
from agent_project.utils.file_handler import pdf_loader, txt_loader, get_file_md5_hex, listdir_with_allowed_type
from agent_project.utils.logger_handler import logger
from agent_project.utils.mysql_handler import check_document_exists, add_document_record

class VectorStoreService:
    '''
    向量存储服务类，负责管理向量的存储和检索
    '''
    def __init__(self,):
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            persist_directory=get_abs_path(chroma_conf["persist_directory"]),
            embedding_function=embedding_model
        )
        #文本分割的工具，指定了分割文本的大小、重叠部分和分割符号等参数。
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap= chroma_conf["chunk_overlap"],
            separators= chroma_conf["separators"],
            length_function = len,  #   指定计算文本长度的函数，这里使用内置的len函数
        )
    def get_retriever(self):
        '''
            返回一个混合检索器 (Ensemble Retriever)：
            结合了 Chroma 向量检索 (语义匹配) 和 BM25 (关键词字面匹配)
        '''
        # 1. 初始化原有的向量检索器
        vector_retriever = self.vector_store.as_retriever(
            search_kwargs={"k": chroma_conf["k"]}
        )
        # 2. 获取 Chroma 库中现有的所有数据
        db_data = self.vector_store.get()
        docs = db_data.get('documents', [])
        metadatas = db_data.get('metadatas', [])
        # 如果库是空的，直接返回向量检索器（防报错）
        if not docs:
            logger.warning("[混合检索] 向量库目前为空，降级为纯向量检索。")
            return vector_retriever
        # 3. 将取出的纯文本数据重新组装成 LangChain 的 Document 对象
        bm25_docs = [
                Document(page_content=doc, metadata=meta)
                for doc, meta in zip(docs, metadatas)
            ]
        # 4. 初始化 BM25 检索器
        bm25_retriever = BM25Retriever.from_documents(bm25_docs)
        bm25_retriever.k = chroma_conf["k"]  # 保证 BM25 召回的数量与向量召回一致
        # 5. 组合成混合检索器
        # weights=[0.5, 0.5] 表示语义和关键词的权重各占一半。
        # 如果发现报错代码(如Err-01)搜不准，可以把 BM25 的权重调高，如 [0.7, 0.3]
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[0.5, 0.5]
        )
        logger.info("[混合检索] EnsembleRetriever (BM25 + Chroma) 初始化成功")
        return ensemble_retriever

    def load_document(self):
        '''
        加载文档读取数据，然后将这些数据转为向量添加到向量存储中。
        :return:
        '''
        def get_file_document(read_path:str):
            #根据文件的扩展名来判断文件类型，并调用相应的加载函数来读取文件内容。
            if read_path.endswith(".pdf"):
                return pdf_loader(read_path)
            elif read_path.endswith(".txt"):
                return txt_loader(read_path)
            return []#  如果文件类型不受支持，就返回一个空列表，表示没有加载到任何文档。
        #1.使用 listdir_with_allowed_type 函数获取指定目录下所有允许的文件类型的文件路径列表。
        allowed_files_path: list[str] = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_konwledge_file_type"])
        )
        #2.计算文件的MD5值
        for path in allowed_files_path:
            # 计算文件 MD5
            md5_hex = get_file_md5_hex(path)
            # 获取单纯的文件名，例如 "user_manual.pdf"
            file_name = os.path.basename(path)

            # 👇 核心改造：使用 MySQL 检查文件是否已存在
            if check_document_exists(md5_hex):
                logger.info(f"[向量存储] 文件 {file_name} 已在数据库中记录，跳过加载")
                continue

            try:
                documents = get_file_document(path)
                if not documents:
                    logger.warning(f"[向量存储] 文件 {path} 不存在有效内容，跳过加载")
                    continue

                split_document = self.splitter.split_documents(documents)
                if not split_document:
                    logger.warning(f"[向量存储] 文件 {path} 分割后没有得到有效文本块，跳过加载")
                    continue

                self.vector_store.add_documents(split_document)

                # 👇 核心改造：存入 Chroma 成功后，将元数据写入 MySQL
                add_document_record(file_name, md5_hex, status="processed")
                logger.info(f"[向量存储] 文件 {file_name} 成功加载并入库！")

            except Exception as e:
                logger.error(f"[向量存储] 加载文件 {path} 时发生错误: {str(e)}", exc_info=True)
                # 记录失败状态到数据库
                add_document_record(file_name, md5_hex, status="failed")
                continue


    def load_single_document(self, file_path: str) -> bool:
        """
        专门用于处理单个上传文件的加载、切片和向量化
        """
        def get_file_document(read_path: str):
            if read_path.endswith(".pdf"):
                from agent_project.utils.file_handler import pdf_loader
                return pdf_loader(read_path)
            elif read_path.endswith(".txt"):
                from agent_project.utils.file_handler import txt_loader
                return txt_loader(read_path)
            return []

        try:
            documents = get_file_document(file_path)
            if not documents:
                logger.warning(f"[向量存储] 单文件 {file_path} 不存在有效内容")
                return False

            split_document = self.splitter.split_documents(documents)
            if not split_document:
                logger.warning(f"[向量存储] 单文件 {file_path} 分割后无有效文本块")
                return False

            # 关键：确保分块的 metadata 中包含 source（文件路径），这样以后我们才能根据路径删除它们
            for doc in split_document:
                doc.metadata["source"] = file_path

            self.vector_store.add_documents(split_document)
            logger.info(f"[向量存储] 单文件 {file_path} 成功加载并入库！")
            return True

        except Exception as e:
            logger.error(f"[向量存储] 加载单文件 {file_path} 时发生错误: {str(e)}", exc_info=True)
            return False

if __name__ == '__main__':
    vs = VectorStoreService()
    vs.load_document()
    retriever = vs.get_retriever()
    res = retriever.invoke("机器人无法控制")
    for r in res:
        print(r.page_content)
        print("*"*20)

