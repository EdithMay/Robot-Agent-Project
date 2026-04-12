# 🌸 Intelligent Floor Cleaning Robot Agent (智能扫地机器人助手)

本项目是一个基于大语言模型 (LLM) 和 LangChain 构建的智能扫地机器人专属助手。它集成了 **ReAct 智能体架构**、**RAG (检索增强生成)**、**多工具调用 (Tool Use)** 以及 **Streamlit 沉浸式流式交互**，能够为用户提供设备故障排查、环境天气查询以及专属清洁报告生成等全方位服务。

## ✨ 核心特性

* 🎨 **定制化交互界面**: 基于 Streamlit 构建的高颜值粉色主题 UI，支持打字机流式输出与思考状态展示，自带本地 `chat_history.json` 历史记录持久化机制。
* 🧠 **ReAct 智能体引擎**: 能够自主推理并决定调用哪些工具来完成复杂任务。
* 📚 **强大的 RAG 知识检索**: 
  * 内置 Chroma 向量数据库进行本地持久化存储。
  * 自动扫描并加载 PDF、TXT 格式的知识库文件（如产品说明书）。
  * 具备 **MD5 哈希校验机制**，避免文档重复灌库，提升系统效率。
* 🛠️ **丰富的外部工具链**:
  * **高德地图 API 接入**: `get_weather` / `get_user_location`，动态获取用户所在地的实时天气，辅助决策机器人清扫计划。
  * **外部数据源解析**: `fetch_external_data` 自动解析本地 CSV/TXT 数据，获取用户在特定月份的设备使用特征与清洁效率。
* 🔀 **智能中间件 (Middleware)**: 
  * 工具调用日志拦截 (`monitor_tool` & `log_before_model`)。
  * **动态提示词切换** (`report_prompt_switch`): 当识别到用户需要生成报告时，通过 `fill_context_for_report` 工具触发上下文变量注入，让 Agent 动态切换至专属的“报告生成 Prompt”，极大地提高了回答的专业性。

## 🚀 快速开始

### 1. 环境准备
确保你的系统中已安装 Python 3.9+。
\`\`\`bash
# 克隆项目仓库
git clone https://github.com/EdithMay/Intelligent-Floor-Cleaning-Robot-Agent-Project.git
cd Intelligent-Floor-Cleaning-Robot-Agent-Project

# 创建并激活虚拟环境 (可选但推荐)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖项 (请确保项目根目录有 requirements.txt)
pip install -r requirements.txt
\`\`\`

### 2. 配置密钥与参数
项目依赖外部 API 和配置文件，请确保在对应的环境变量/配置文件中提供以下参数：
* **大模型 API 密钥**: 你所使用的 LLM 的 API Key。
* **高德地图 API 密钥**: 用于获取定位和天气，配置在 `agent_conf["AMAP_API_KEY"]` 中。
* **文件路径配置**: 确保 `chroma_conf` 中的持久化路径 (`persist_directory`) 和知识库路径 (`data_path`) 已正确设置。

### 3. 初始化本地知识库 (RAG)
将机器人的说明书、排障指南（支持 `.pdf`, `.txt`）放入配置的数据目录中。然后单独运行一次向量存储服务来构建索引：
\`\`\`bash
python agent_project/rag/vector_store.py
\`\`\`
*该脚本会自动处理文件分割并使用 MD5 记录已处理文件。*

### 4. 启动应用
在项目根目录运行以下命令启动 Web 界面：
\`\`\`bash
streamlit run app.py
\`\`\`
应用启动后，在浏览器访问 `http://localhost:8501` 即可体验。

## 💡 典型交互用例

1. **RAG 故障排查**: 
   * *"我的机器人连不上 WIFI 怎么办？"* (触发 `rag_summarize`)
2. **环境感知**: 
   * *"今天杭州的天气怎么样？适合开窗通风让机器人扫地吗？"* (触发 `get_weather`)
3. **数据分析与报告**:
   * *"帮我生成本月的扫地机器人使用报告。"* (触发 `get_current_month` -> `fetch_external_data` -> 动态切换提示词)

## 🤝 贡献与支持
如果您有任何建议或发现了 Bug，欢迎提交 Issue 或 Pull Request！
