'''
向量存储服务
'''
import os.path

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from agent_project.utils.config_handler import chroma_conf
from agent_project.model.factory import embedding_model,chat_model
from agent_project.utils.path_tool import get_abs_path
from agent_project.utils.file_handler import pdf_loader, txt_loader, get_file_md5_hex, listdir_with_allowed_type
from agent_project.utils.logger_handler import logger

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
        返回一个 LangChain retriever：上层问问题时，它会：
        把 query 做 embedding
        去向量库做相似度搜索
        返回 Top-K 个最相关的文本块（k 来自配置
        :return:
        '''
        # 返回一个检索器对象，可以根据指定的top_k参数来控制返回的结果数量。
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_conf["k"]})

    def load_document(self):
        '''
        加载文档读取数据，然后将这些数据转为向量添加到向量存储中。
        :return:
        '''
        def check_mad5_hex(md5_for_check:str):
            if not  os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                # 如果存储MD5值的文件不存在，就创建一个空文件来存储MD5值，并返回False，表示这个文件没有被处理过。
                open(get_abs_path(chroma_conf["md5_hex_store"]),"w",encoding="utf-8").close()
                return False
            with open(get_abs_path(chroma_conf["md5_hex_store"]),"r",encoding="utf-8") as f:
                for line in f.readlines():
                    if line.strip() == md5_for_check:
                        return True #如果在文件中找到匹配的MD5值，代表这个文件以及被处理过

        def save_md5_hex(md5_hex:str):
            with open(get_abs_path(chroma_conf["md5_hex_store"]),"a",encoding="utf-8") as f:
                f.write(md5_hex + "\n")#把新的MD5值追加到文件中，每个MD5值占一行

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

            md5_hex = get_file_md5_hex(path)
            #3.检查md5是否已存在
            if check_mad5_hex(md5_hex):
                logger.info(f"[向量存储]文件{path}已处理过，跳过加载")
                continue
            try:
                #4.通过get_file_document加载文件内容
                documents = get_file_document(path)
                if not documents:
                    logger.warning(f"[向量存储]文件{path}不存在有效内容，跳过加载")
                    continue
                #5.使用文本分割工具将加载的文档内容进行分割，得到一个包含多个文本块的列表。
                split_document = self.splitter.split_documents(documents)
                if  not split_document:
                    logger.warning(f"[向量存储]文件{path}分割后没有得到有效文本块，跳过加载")
                    continue
                #6.将分割好的文本块存入向量库
                self.vector_store.add_documents(split_document)
                #7.将文件的MD5值保存到存储MD5值的文件中，以便下次加载时进行检查，避免重复处理同一个文件。
                save_md5_hex(md5_hex)
            except Exception as e:
                logger.error(f"[向量存储]加载文件{path}时发生错误: {str(e)}",exc_info=True)
                continue

if __name__ == '__main__':
    vs = VectorStoreService()
    vs.load_document()
    retriever = vs.get_retriever()
    res = retriever.invoke("机器人无法控制")
    for r in res:
        print(r.page_content)
        print("*"*20)

