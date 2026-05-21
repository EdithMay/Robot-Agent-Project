import os
import shutil
from agent_project.utils.mysql_handler import check_document_exists, add_document_record
from agent_project.rag.vector_store import VectorStoreService
from agent_project.utils.logger_handler import logger
from agent_project.utils.file_handler import get_file_md5_hex
from agent_project.utils.mysql_handler import fetch_all_documents

class KnowledgeService:
    def __init__(self):
        self.vector_store_service = VectorStoreService()
        # 预留存放上传文件的临时目录
        self.upload_dir = "./data"
        os.makedirs(self.upload_dir, exist_ok=True)

    def process_new_upload(self, file_name: str, file_content: bytes):
        """
        处理前端上传的新文件：保存 -> MD5校验 -> 向量化 -> MySQL记录
        """
        file_path = os.path.join(self.upload_dir, file_name)

        try:
            # 1. 暂存文件到本地
            with open(file_path, "wb") as f:
                f.write(file_content)

            # 2. 计算 MD5 并查重
            md5_hex = get_file_md5_hex(file_path)
            if check_document_exists(md5_hex):
                logger.info(f"文件 {file_name} 已存在，跳过处理。")
                return {"status": "skipped", "message": "文件已存在知识库中"}

            # 3. 通知 VectorStoreService 解析该单一文件 (需要你在 vector_store.py 补充这个单文件解析方法)
            success = self.vector_store_service.load_single_document(file_path)

            if success:
                # 4. 写入 MySQL 成功记录
                add_document_record(file_name, md5_hex, status="processed")
                return {"status": "success", "message": f"{file_name} 知识库构建完成"}
            else:
                add_document_record(file_name, md5_hex, status="failed")
                return {"status": "error", "message": "文档解析或切片失败"}

        except Exception as e:
            logger.error(f"处理上传文件 {file_name} 失败: {e}")
            return {"status": "error", "message": str(e)}

    def get_document_list(self):
        """
        获取当前知识库的文件列表
        """
        # 你需要在 mysql_handler.py 中补充一个 fetch_all_documents() 函数

        return fetch_all_documents()

    def delete_document(self, file_name: str, md5_hash: str):
        """
        执行危险的删除操作：同时删除 Chroma 向量和 MySQL 记录
        """
        try:
            # 1. 删除 Chroma 中的向量块 (根据 metadata 中的 source)
            self.vector_store_service.vector_store.delete(where={"source": os.path.join(self.upload_dir, file_name)})

            # 2. 删除 MySQL 记录 (需要在 mysql_handler.py 中补充 delete_document_record 函数)
            from agent_project.utils.mysql_handler import delete_document_record
            delete_document_record(md5_hash)

            return True
        except Exception as e:
            logger.error(f"删除文件 {file_name} 失败: {e}")
            return False
