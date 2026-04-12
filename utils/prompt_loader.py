from agent_project.utils.config_handler import prompt_conf
from agent_project.utils.path_tool import get_abs_path
from agent_project.utils.logger_handler import logger
'''
提示词加载器
1.加载系统提示词
2.加载RAG提示词
3.加载报告提示词  
'''

def load_system_prompts() ->str:
    '''
    加载系统提示词
    :return:
    '''
    try:
        system_prompt_path = get_abs_path(prompt_conf["main_prompt_path"])
    except  KeyError as e :
        logger.error("[load_system_prompts]在 prompts.yml 中没有找到 main_prompt_path 的配置项")
        raise e
    try:
        return open(system_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_system_prompts]系统提示词出错：{str(e)}")
        raise e

def load_rag_prompts() ->str:
    try:
        rag_prompt_path = get_abs_path(prompt_conf["rag_summarize_prompt_path"])
    except  KeyError as e :
        logger.error("[load_rag_prompts]在 prompts.yml 中没有找到 rag_summarize_prompt_path 的配置项")
        raise e
    try:
        return open(rag_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_rag_prompts]RAG提示词出错：{str(e)}")
        raise e

def load_report_prompts() ->str:
    try:
        report_prompt_path = get_abs_path(prompt_conf["report_prompt_path"])
    except  KeyError as e :
        logger.error("[load_report_prompts]在 prompts.yml 中没有找到 report_prompt_path 的配置项")
        raise e
    try:
        return open(report_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_report_prompts]report提示词出错：{str(e)}")
        raise e

if __name__ == '__main__':
    print(load_system_prompts())
    print(load_rag_prompts())
    print(load_report_prompts())