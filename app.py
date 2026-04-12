import sys
import os
import streamlit as st
import json  # 👈 新增导入 json
# 2. 欺骗路径，将上一级目录加入环境变量（这行必须紧跟在 import 后面）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 3. 然后再导入你自己项目里的模块（现在就不会报错了）
from agent_project.agent.react_agent import ReactAgent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_project.agent.react_agent import ReactAgent

HISTORY_FILE = "chat_history.json" # 将历史记录保存在当前目录下的 JSON 文件中
def load_history():
    """从本地读取历史记录"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [] # 如果文件不存在，返回空列表

def save_history(messages):
    """将历史记录保存到本地"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


# ==========================================
# 1. 页面基本配置与粉色主题 CSS 注入
# ==========================================
st.set_page_config(page_title="🌸 RAG 智能助手", page_icon="🌸", layout="centered")

# 使用 Markdown 注入自定义 CSS 实现粉色主题
st.markdown("""
<style>
    /* 全局背景色：淡粉色 */
    [data-testid="stAppViewContainer"] {
        background-color: #FFF0F5; 
    }
    /* 顶部透明，适配背景 */
    [data-testid="stHeader"] {
        background-color: transparent;
    }
    /* 聊天气泡背景色微调，使其在粉色背景下更柔和 */
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 228, 225, 0.6); 
        border-radius: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.title("🌸 专属 RAG 智能助手")
st.caption("基于 LangGraph 与大模型构建的业务分析助手")

# ==========================================
# 2. 初始化 Session State (状态保持)
# ==========================================
# 存储历史对话
if "messages" not in st.session_state:
    st.session_state.messages = load_history() # 👈 这里变了

# 全局单例实例化 Agent，避免每次交互都重新加载模型和工具
if "agent" not in st.session_state:
    st.session_state.agent = ReactAgent()

# ==========================================
# 3. 渲染历史对话记录
# ==========================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 4. 底部对话框与流式处理逻辑
# ==========================================
# st.chat_input 会自动固定在页面底部
if prompt := st.chat_input("想问点什么？(例如：生成我的使用报告 / 机器人连不上WIFI)"):

    # 4.1 立即在界面上显示用户的输入，并存入状态
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_history(st.session_state.messages)  # 👈 新增：保存用户提问
    with st.chat_message("user"):
        st.markdown(prompt)

    # 4.2 智能体开始处理并响应
    with st.chat_message("assistant"):
        # 创建一个占位符，用于后续实现类似打字机的流式视觉效果
        message_placeholder = st.empty()
        full_response = ""

        # 使用 st.spinner 触发思考时的转圈图标

        #with st.spinner("✨ 智能体正在努力思考与检索中..."):
        #    try:
                # 遍历 Agent 的 execute_stream 方法
                # 根据你在 react_agent.py 中的 stream_mode="values" 设定，
                # 每次 yield 的是一整个状态阶段的最新 content，所以这里采用直接覆盖的方式刷新文本
        #        for chunk in st.session_state.agent.execute_stream(prompt):
        #            full_response = chunk
                    # 加上闪烁光标 ▌ 增强流式打字感
        #            message_placeholder.markdown(full_response + " ▌")

        # 使用 st.spinner 触发思考时的转圈图标
        # 【修复点】使用占位符显示思考状态，而不是 st.spinner()
        message_placeholder.markdown("✨ *智能体正在努力思考与检索中...*")
        try:
            # 开始流式输出，直接覆盖前面的思考状态
            for chunk in st.session_state.agent.execute_stream(st.session_state.messages):
                full_response = chunk
                # 加上闪烁光标 ▌ 增强流式打字感
                message_placeholder.markdown(full_response + " ▌")
        except Exception as e:
            full_response = f"**执行过程中发生错误：** {str(e)}"

            # 思考完成后，去掉光标，渲染最终完整的回答
        message_placeholder.markdown(full_response)

        # 4.3 将大模型的最终回答存入历史对话
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_history(st.session_state.messages)