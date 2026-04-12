from typing import Callable

from langchain.agents import AgentState
from langchain.agents.middleware import wrap_tool_call, before_model, dynamic_prompt, ModelRequest
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command
from langgraph.runtime import Runtime
from agent_project.utils.logger_handler import logger
from agent_project.utils.prompt_loader import load_report_prompts, load_system_prompts


@wrap_tool_call
def monitor_tool(request:ToolCallRequest,handle:Callable[[ToolCallRequest],ToolMessage|Command])-> ToolMessage|Command:
    '''
    监控工具执行
    request:请求的数据封装（函数的入参）
    handle:执行的函数本身
    '''
    logger.info(f"[tool monitor]工具 {request.tool_call['name']} 开始执行，参数：{request.tool_call['args']}")
    try:
        result = handle(request)
        logger.info(f"[tool monitor]工具 {request.tool_call['name']} 执行成功，结果：{result}")
        #如果工具调用的名称是'fill_context_for_report'，则在运行时环境的上下文中设置一个键为'report'，值为True。
        # 这种机制允许在工具执行后，根据工具的不同，动态地调整运行时环境中的上下文信息，以便后续的模型执行可以根据这些上下文信息做出相应的决策。
        if request.tool_call['name'] == 'fill_context_for_report':
            request.runtime.context['report'] = True
        return result
    except Exception as e:
        logger.error(f"[tool monitor]工具 {request.tool_call['name']} 执行失败，错误：{str(e)}")
        raise e

@before_model
def log_before_model(state:AgentState,runtime:Runtime):
    '''
    在模型执行前输出日志
    state:  当前的Agent状态，包含了工具调用的历史记录、模型的输入输出等信息。
    runtime: 运行时环境，提供了模型执行的上下文信息。
    :return:
    '''
    logger.info(f"[log_before_model]模型即将执行，带有{len(state)}条消息")
    logger.debug(f"[log_before_model]{type(state['messages'][-1]).__name__}|{state['messages'][-1].content.strip()}")
    return None

@dynamic_prompt
def report_prompt_switch(request:ModelRequest):
    '''
    agent每一次“准备生成 prompt / 发起模型调用”之前，
    框架都会调用这个函数，让你“动态提供 prompt”
    :return:
    '''
    #从运行时环境的上下文中获取'report'键的值，如果没有找到该键，则默认为False。
    is_report = request.runtime.context.get('report',False)
    if is_report:#  如果is_report为True，说明需要使用报告相关的提示词。
        return load_report_prompts()
    return load_system_prompts()#不需要使用报告相关的提示词，返回系统相关的提示词。
