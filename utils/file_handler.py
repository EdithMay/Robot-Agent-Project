'''
#这个代码实现 了以下功能：
1. 获取文件的md5值：通过计算文件的md5值，可以唯一标识文件内容的变化，避免重复处理相同的文件。
2. 列出指定类型的文件：可以返回文件夹下指定类型的文件列表，方便后续处理。
3. 加载pdf和txt文档：提供了加载pdf和txt文档的函数，方便后续对文档内容进行处理。
'''
import os.path
import hashlib

from langchain_community.document_loaders import PyPDFLoader, TextLoader

from agent_project.utils.logger_handler import logger


def get_file_md5_hex(file_path):
    '''
    获取文件的md5值
    :return:
    '''
    if not os.path.exists(file_path):
        logger.error(f"[md5计算]文件{file_path}不存在")
        return
    if not os.path.isfile(file_path):
        logger.error(f"[md5计算]{file_path}不属于文件")
        return
    md5_obj = hashlib.md5()
    chunk_size = 4096 #4KB分片，避免文件过大
    try:
        with open(file_path, "rb") as f:
            # 使用 walrus 运算符（:=）在 while 循环中读取文件分片，并将其赋值给 chunk 变量。
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)
        return md5_obj.hexdigest()  #返回16进制的md5值
    except Exception as e:
        logger.error(f"[md5计算]计算文件{file_path}的md5值时发生错误: {str(e)}")
        return


def listdir_with_allowed_type(file_path:str, allowed_types:tuple[str]):
    '''
    返回文件夹下指定类型的文件列表
    allowed_types: 允许的文件类型，例如(".pdf", ".txt")
    :return:
    '''
    files=[]
    if not os.path.isdir(file_path):
        logger.error(f"[文件列表]文件夹{file_path}不存在,或者不是一个文件夹")
        return allowed_types
    for item in os.listdir(file_path):
        files.append(os.path.join(file_path,item))
    return tuple(files)

def pdf_loader(file_path,password = None):
    '''
    加载pdf的文档
    :return:
    '''
    #PyPDFLoader是一个用于加载PDF文档的工具类，可以从指定的PDF文件中提取文本内容。
    return PyPDFLoader(file_path,password=password).load()
def txt_loader(file_path):
    '''
    加载txt的文档
    :return:
    '''
    return TextLoader(file_path,encoding="utf-8").load()