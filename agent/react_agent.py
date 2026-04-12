from langchain.agents import create_agent

from agent_project.agent.tools.agent_tools import rag_summarize,get_weather, get_user_location, get_user_id, get_current_month, fetch_external_data,fill_context_for_report
from agent_project.agent.tools.middleware import monitor_tool,  log_before_model, report_prompt_switch
from agent_project.model.factory import chat_model
from agent_project.utils.prompt_loader import load_system_prompts


class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt= load_system_prompts(),
            tools=[rag_summarize,get_weather, get_user_location, get_user_id, get_current_month,fetch_external_data,fill_context_for_report ],
            middleware=[monitor_tool,log_before_model, report_prompt_switch]
        )
    '''
    def execute_stream(self,query):
        input_dict = {
            "messages":[
                {"role":"user","content": query},
            ]
        }
        # 设置stream_mode为"values"，同时在上下文中设置'report'键的值为False，表示当前不需要使用报告相关的提示词。
        for chunk in self.agent.stream(input_dict,stream_mode="values",context = {"report":False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                # strip()方法用于去除字符串首尾的空白字符（包括空格、制表符、换行符等）。
                # 去除掉首尾的空白字符后，再加上一个换行符"\n"，以便在输出时每条消息占一行。
                yield latest_message.content.strip()+"\n"
    '''

    def execute_stream(self, messages_history):
        # 直接把历史对话列表塞给模型
        input_dict = {
            "messages": messages_history
        }
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"
if __name__ == '__main__':
    agent=ReactAgent()
    for chunk in  agent.execute_stream("机器人连不上WIFI"):
        print(chunk,end="",flush=True)