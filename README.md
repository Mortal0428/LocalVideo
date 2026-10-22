# 🎬 CinemaAgent - 多媒体短剧视听与 AI 伴读赋能平台

CinemaAgent 是一套专为**竖屏短剧、微综艺与沉浸式多媒体视听内容**打造的生产级全栈流媒体与 AI Agent 互动系统。
项目深度融合**中国联通云盘（沃盘）大容量存储驱动（基于 OpenList 网关）**，提供流畅的 HTTP 206 视频切片流媒体点播、9:16 移动端拟态暗黑影院播放器、低延迟 WebSocket 实时弹幕、DFA 高效敏感词机审阻断，以及融合本地大语言模型（Ollama / Qwen2.5）的多模态时间轴视频伴读 Agent。

---

## 🌟 核心功能特性

1. **☁️ 沃盘对象存储桥接（OpenList REST/WebDAV 驱动）**
   - 突破本地小容量磁盘限制，直连中国联通云盘（沃盘）海量视频资源库。
   - 实现标准 **HTTP Range 206 Partial Content** 流媒体分片代理，支持秒级 Seek 任意拖拽与断点续传。

2. **📤 大文件分片上传与自动化转码流水线**
   - 支持大视频文件并发切片上传（Init -> Chunk -> Complete）。
   - 集成 **FFmpeg** 异步元数据解析与高分辨率首帧封面抽取，处理完成后自动持久化回传沃盘云端，零冗余磁盘开销。

3. **📱 Vue 3 拟态 9:16 移动端胶囊播放器（暗黑影院风格）**
   - 现代玻璃拟态（Glassmorphism）与暗夜荧光质感，自适应大屏与移动端。
   - 具备**短剧连载剧集平滑切换**、点赞动态微动画、防重复点赞、实时评论上屏与播放进度记忆断点续播。

4. **⚡ WebSocket 实时弹幕引擎 & 毫秒级 DFA 敏感词机审过滤**
   - 分集房间轻量级 WebSocket 实时双向弹幕广播，4 轨道动态避碰与柔和透明度渐变。
   - 内置 **DFA 确定有限状态自动机** 算法，敏感词与违禁发言 100% 毫秒级阻断拦截，自动归档进入 `ContentReview` 人审复核控制台。

5. **🤖 视频多模态时间轴知识库 RAG & 剧情伴读 Agent**
   - 剧集结构化多模态解析（时间戳分段、剧情摘要、人物出场、高能转折镜头）。
   - 挂载本地开源大语言模型（Ollama / Qwen2.5:7b，具备高可用离线规则降级）。
   - **智能时间戳点击跳转**：在伴读问答流中点击 `[00:XX 跳转]` 胶囊标签，播放器自动高亮并毫秒级 Seek 到对应精彩镜头！

---

## 🛠️ 技术技术栈

- **后端业务与代理层**：Python 3.12 + FastAPI + Uvicorn + WebSockets + Httpx
- **数据持久化与审核中台**：MySQL 8.0 + SQLAlchemy 2.0 ORM + Alembic
- **云盘中继网关**：OpenList (沃盘原生 API 驱动，默认端口 5244)
- **多媒体处理**：FFmpeg (ffprobe / 音视频转码 / 智能帧提取)
- **前端交互视窗**：Vue 3 + TypeScript + Vite + Pinia + Element Plus
- **AI 智能体引擎**：LangChain / Ollama Qwen2.5 + 自定义时间轴 RAG 检索器
- **端到端质量保障**：Playwright 异步自动化无头测试套件（Edge / Chromium 100% 验收覆盖）

---

## 🚀 极速启动指南

### 方式一：Windows 双击一键启动（强烈推荐）

1. 双击根目录下的 **`一键启动多媒体平台.bat`**。
2. 脚本将自动检测 OpenList 云盘网关与 FastAPI 业务服务，并在启动完成后自动唤起浏览器打开：
   👉 **`http://127.0.0.1:8000/`**

---

### 方式二：手动分步启动

#### 步骤 1：启动中国联通云盘网关 (OpenList)
在根目录双击 **`启动云盘OpenList.bat`**（或进入 OpenList 目录执行）：
```cmd
openlist.exe server
```
- OpenList 管理后台地址：`http://127.0.0.1:5244`（初次使用可检查中国联通云盘挂载状态是否为“工作中”）。

#### 步骤 2：启动 FastAPI 业务后端与影院前端
在项目根目录打开终端（PowerShell 或 CMD）：
```cmd
cd backend
python main.py
```
- 服务默认监听：`http://127.0.0.1:8000`
- API 交互式文档 (Swagger UI)：`http://127.0.0.1:8000/docs`

---

## 🧪 自动化测试套件 (Playwright E2E)

项目全流程遵循严格的测试驱动规范，所有核心业务均包含 Playwright 无头端到端测试：

```bash
# 步骤 1：沃盘流式点播与 HTTP 206 校验
python backend/tests/e2e/test_step1_stream.py

# 步骤 2：切片上传与 FFmpeg 封面转码校验
python backend/tests/e2e/test_step2_upload.py

# 步骤 3：9:16 移动播放器、选集与互动测试
python backend/tests/e2e/test_step3_player.py

# 步骤 4：WebSocket 弹幕广播与 DFA 敏感词机审阻断测试
python backend/tests/e2e/test_step4_danmaku_review.py

# 步骤 5：视频知识库 RAG 伴读 Agent 与时间戳跳转测试
python backend/tests/e2e/test_step5_agent.py
```
所有测试均已通过，可随时独立回归运行。
