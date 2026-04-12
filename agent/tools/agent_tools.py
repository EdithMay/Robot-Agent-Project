import os.path
import requests
from langchain_core.tools import tool
from agent_project.utils.config_handler import agent_conf
from agent_project.rag.rag_services import RagSummarizeService
from agent_project.utils.path_tool import get_abs_path
from agent_project.utils.logger_handler import logger
from datetime import datetime
rag = RagSummarizeService()#创建一个RAG总结服务的实例
external_data={}
@tool(description="从向量存储中检索参考文献")
def rag_summarize(query):
        return rag.rag_summarizes(query)
@tool(description="获取城市的天气情况,消息以字符串的形式返回")
def get_weather(city:str):
    return f"{city}的天气情况是：晴天，温度25摄氏度，湿度60%，风速10公里每小时。"
@tool(description="获取用户所在城市的名称，以字符串的形式返回")
def get_user_location():
    try:
        # 使用免费的 IP 解析 API
        # 注意：部分外网 API 可能受网络环境影响，你可以替换为高德、百度的 IP 定位 API
        response = requests.get("http://ip-api.com/json/?lang=zh-CN", timeout=5)
        data = response.json()

        if data.get("status") == "success":
            city = data.get("city", "未知")
            return f"{city}"
        return "定位失败"
    except Exception as e:
        logger.error(f"[get_user_location] 获取地理位置失败: {e}")
        return "北京"  # 如果断网或报错，给一个默认的兜底城市
@tool(description="获取用户的id，以字符串形式返回")
def get_user_id():
    return "1005"
@tool(description="获取系统当前月份（以字符串形式返回）。仅当用户要求生成报告且未明确说明是哪个月份时调用。")
def get_current_month():
    # 获取当前系统时间
    now = datetime.now()

    # 方式A：如果你想要返回纯数字的月份（如 "6月"）
    #return f"{now.month}月"

    # 方式B：如果你想要返回带年份的标准格式（如 "2026-04"），推荐使用这种，更严谨！
    return now.strftime("%Y-%m")

def generate_external_data():
    '''
    {
        "user_id":{
        "month":{"特征":xxx,"效率":xxx},
        "month":{"特征":xxx,"效率":xxx},
        "month":{"特征":xxx,"效率":xxx},
        },
        "user_id":{
        "month":{"特征":xxx,"效率":xxx},
        "month":{"特征":xxx,"效率":xxx},
        "month":{"特征":xxx,"效率":xxx},
        },
        ...
    }
    :return:
    '''
    if not external_data:
        # 获取外部数据文件的绝对路径
        external_data_path = get_abs_path(agent_conf["external_data_path"])
        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"{external_data_path}外部数据路径不存在")
        with open(external_data_path,"r",encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                arr = line.strip().split(",")
                user_id = arr[0].replace('"',"")#去掉空格
                feature =  arr[1].replace('"',"")#去掉空格
                efficiency = arr[2].replace('"',"")#去掉空格
                consumables =   arr[3].replace('"',"")#去掉空格
                comparsion =    arr[4].replace('"',"")#去掉空格
                time =      arr[5].replace('"',"")#去掉空格

                #如果用户ID不在external_data字典中，就创建一个新的键值对，键是用户ID，值是一个空字典。
                if user_id not in external_data:
                    external_data[user_id]= {}
                #在external_data字典中，使用用户ID作为键，时间作为子键，存储一个包含特征、效率、耗材和对比信息的字典。
                external_data[user_id][time] = {
                        "特征":   feature,
                        "清洁效率":   efficiency,
                        "耗材": consumables,
                        "对比":   comparsion
                }


@tool(description= "从外部系统中获取指定月份（或当前月份）对应用户的使用记录，月份严格按照YYYY-MM的格式，以纯字符串形式返回，如果未检测到返回空字符串")
def fetch_external_data(user_id, month):
    generate_external_data()
    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(f"[fetch_external_data]未找到用户ID {user_id} 在 {month} 的使用记录")
        return ""

@tool(description="无入参，无返回值，调用后触发中间件，自动为报告生成的场景动态注入上下文信息，为后续的提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report"