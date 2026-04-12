import logging
import os
from datetime import datetime

from agent_project.utils.path_tool import get_abs_path

#日志保存的根目录
LOG_ROOT = get_abs_path("logs")
#确保目录存在
os.makedirs(LOG_ROOT,exist_ok=True)
#日志格式
'''
    %(asctime)s：日志记录的时间
    %(levelname)s：日志级别
    %(message)s：日志消息
    %(name)s：日志记录器的名称
    '''
DEFAULT_LOG_FORMAT = logging.Formatter(

    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
#日志核心,函数返回的是一个日志器对象logging.Logger
def get_logger(name:str = "agent",
               console_level:int = logging.INFO,
               file_level:int = logging.DEBUG,
               log_file = None) ->logging.Logger:
    logger = logging.getLogger(name)#获取一个名为 "name" 的日志器对象
    logger.setLevel(logging.DEBUG)
    #如果这个 logger 已经绑定过处理器（handler）了，就直接返回，不要再重复添加。
    #handler：处理器，负责把日志输出到控制台、文件等地方
    if logger.handlers:
        return logger
    #配置输出到控制台的 handler
    console_handler = logging.StreamHandler()#创建一个控制台处理器
    console_handler.setLevel(console_level)#控制台 handler 的日志级别
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)#设置日志输出格式
    logger.addHandler(console_handler)#把控制台 handler 挂到 logger 上。

    #配置文件handler
    if not log_file: #
        #日志的存放路径
        log_file = os.path.join(LOG_ROOT,f"{name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    file_handler = logging.FileHandler(log_file,encoding='utf-8')#创建一个文件处理器，指定日志文件路径和编码
    file_handler.setLevel(file_level)#文件 handler 的日志级别
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)#设置日志输出格式
    logger.addHandler(file_handler)#把文件 handler 挂到 logger 上。
    return logger

logger = get_logger()#创建一个默认的日志器对象
if __name__ == '__main__':
    logger.info("信息日志")
    logger.debug("调试日志")
    logger.warning("警告日志")
    logger.error("错误日志")