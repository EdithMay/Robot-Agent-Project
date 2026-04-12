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
@tool(description="获取当前定位城市的天气情况,消息以字符串的形式返回")
def get_weather(city:str)-> str:
        """
        使用高德 API 获取真实天气。
        入参 city 可以是城市中文名（如"北京市"、"杭州市"）或 adcode。
        """
        url = "https://restapi.amap.com/v3/weather/weatherInfo?parameters"
        params = {
            "key":  agent_conf["AMAP_API_KEY"],
            "city": city,
            "extensions": "base",  # base: 实时天气, all: 预报天气
            "output": "JSON"
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            # 高德 API 成功状态码 status 为 "1"
            if data.get("status") == "1" and data.get("lives"):
                live_weather = data["lives"][0]

                # 提取需要的字段
                weather = live_weather.get("weather", "未知")
                temperature = live_weather.get("temperature", "未知")
                humidity = live_weather.get("humidity", "未知")
                winddirection = live_weather.get("winddirection", "未知")
                windpower = live_weather.get("windpower", "未知")

                return f"{city}的实时天气情况是：{weather}，温度{temperature}摄氏度，湿度{humidity}%，{winddirection}风{windpower}级。"
            else:
                error_info = data.get('info', '未知错误')
                logger.error(f"[get_weather] 高德天气API查询失败: {error_info}")
                return f"抱歉，暂时无法获取 {city} 的天气数据。"

        except Exception as e:
            logger.error(f"[get_weather] 请求高德天气API发生网络异常: {e}")
            return f"获取 {city} 天气时网络异常，请稍后再试。"
@tool(description="获取用户所在城市的名称，以字符串的形式返回")
def get_user_location():
    url = "https://restapi.amap.com/v3/ip?parameters"
    params = {
        "key": agent_conf["AMAP_API_KEY"],
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data.get("status") == "1":
            # 如果是直辖市，city 字段可能是空的，需要取 province 字段
            city = data.get("city")
            if not city or isinstance(city, list):  # 高德有时空数据会返回 []
                city = data.get("province", "未知")
            return f"{city}"

        logger.warning(f"[get_user_location] 高德IP定位失败: {data}")
        return "北京"

    except Exception as e:
        logger.error(f"[get_user_location] 请求高德IP定位发生异常: {e}")
        return "北京"
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

