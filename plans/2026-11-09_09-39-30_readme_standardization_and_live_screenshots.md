# CinemaAgent README 标准化重构与实机全模块无头浏览器实时截图计划

## 1. 计划归档与变更范围

```markdown
[变更计划]
- 计划文档路径：plans/2026-11-09_09-39-30_readme_standardization_and_live_screenshots.md
- 记录时间戳：2026-11-09 09:39:30
- 前端目标文件：无（零业务代码侵入）
- 后端目标文件：无（零业务代码侵入）
- 文档与截图目标文件：
  - README.md（重构为工业级标准化项目白皮书，补充立项背景、多云盘聚合说明、小型商家/私人影院/农家乐等适用领域、全栈技术栈矩阵表、系统架构与双轨部署指引）
  - docs/screenshots/01_portal_hall_and_carousel.png（实机实时采集：沉浸式剧场大厅、16:9 焦点轮播与多云盘直连剧集展架）
  - docs/screenshots/02_player_dual_mode_and_rag.png（实机实时采集：16:9/9:16 双模态播放器、多模态时间轴 RAG 剧情伴读与秒级跳转胶囊）
  - docs/screenshots/03_social_comments_and_coin_tip.png（实机实时采集：二级嵌套评论树、点赞互动与短剧金币投币打赏毛玻璃弹窗）
  - docs/screenshots/04_user_bento_vip_and_pet.png（实机实时采集：Bento 风格个人空间、金币钱包、VIP 卡密核销与 Codex 观影灵宠太空舱）
  - docs/screenshots/05_admin_bi_cockpit.png（实机实时采集：管控中台 BI 全景智能驾驶舱、Holt-Winters 流量预测与 Bass 爆款潜力榜）
  - docs/screenshots/06_multi_agent_tactical_and_roundtable.png（实机实时采集：九大智能体战术大屏、沉浸式协同圆桌会议与实时分镜交付物抽屉）
  - docs/screenshots/07_rag_evaluation_and_graph.png（实机实时采集：RAG 知识中台、RAGAS 四维雷达跑分大屏与评测基准流水线）
  - docs/screenshots/08_drama_shelf_and_cloud_sync.png（实机实时采集：短剧媒资编目治理、多海报画廊与多云盘双模同步控制台）
  - docs/screenshots/09_danmaku_moderation_and_agent4.png（实机实时采集：DFA 敏感词互动合规风控台与 4 号合规审片官人机协同仲裁）
- 测试与截图脚本：
  - tests/e2e/capture_readme_live_screenshots.py（Playwright 无头浏览器实机登录与全模块实时截图采集脚本，含 MD5 去重校验）
```

---

## 2. 核心评估指标

### 2.1 可行性与把握度评估
- **把握度：98%**
- **潜在技术风险点与应对**：
  - **之前截图重复的根因**：此前截图脚本在访问 `/admin`、`/profile` 等受保护路由时未注入有效登录态 Token，导致 Vue Router 路由守卫全部重定向至 `/login` 登录页（造成 5 张图全是同一张登录页，3 张图全是未登录首页）。
  - **解决方案**：在 `tests/e2e/capture_readme_live_screenshots.py` 中，先通过真实登录流程（或 API 获取管理员/用户 JWT Token 并注入 `localStorage`），等待各视图异步接口与 ECharts 画布渲染完毕，切换对应子标签页（Tab），再逐一截取高清实机画面，并对所有生成的 PNG 文件执行文件大小与 MD5 哈希比对，**强制断言任意两张截图的 MD5 哈希绝不相同**。

### 2.2 存量功能与三方体验影响分析
- **用户体验（UX）**：访问 GitHub/Gitee 仓库时，首屏即可通过清晰的结构读懂项目为什么做、解决什么痛点、适用于哪些线下实体（私人影院、农院山庄、农家乐聚会场地、点播影咖）与线上场景，并看到 9 张完全不重复的真实系统运行高清截图。
- **开发者与运维体验（DX）**：提供精确到版本号的七层技术栈表格、物理隔离目录树以及 Windows 本地 + Docker 容器化双轨部署命令。
- **AI 代理体验（AX）**：结构化表格与 Mermaid 拓扑图提升跨轮次检索准确度。
- **存量保护**：零修改前后端源码，100% 保障现有业务功能不受影响。

### 2.3 Playwright 自动化回环测试与实时截图验证方案
- **服务拉起**：确认或启动后端 FastAPI 服务（`127.0.0.1:8000`）与前端服务（`127.0.0.1:5173`）。
- **无头浏览器配置**：使用 Playwright Chromium `headless=True`，视口设定为 `1920x1080`（`device_scale_factor=1.5` 高清采样）。
- **9 大实机场景采集与断言**：
  1. **场景 1（剧场大厅与焦点轮播）**：访问首页，等待轮播图与剧集卡片封面加载完成，截取 `01_portal_hall_and_carousel.png`；
  2. **场景 2（双模态播放器与 AI 时间轴伴读）**：进入剧集播放页，展开右侧 AI 剧情伴读面板并展示时间戳跳转胶囊，截取 `02_player_dual_mode_and_rag.png`；
  3. **场景 3（二级嵌套评论与金币打赏弹窗）**：在播放页滚动至评论区或触发投币打赏毛玻璃弹窗，截取 `03_social_comments_and_coin_tip.png`；
  4. **场景 4（个人中心 Bento 资产、VIP 兑换与灵宠太空舱）**：以登录态进入 `/profile` 个人空间，展示金币钱包、VIP 尊享特权卡、兑换码中心与 Codex 观影灵宠太空舱，截取 `04_user_bento_vip_and_pet.png`；
  5. **场景 5（企业级管控中台 BI 智能驾驶舱）**：以超级管理员身份进入 `/admin` 的「BI 智能驾驶舱」标签页，等待 Holt-Winters 趋势图与 Bass 爆款榜渲染完成，截取 `05_admin_bi_cockpit.png`；
  6. **场景 6（九大智能体战术大屏与沉浸式协同圆桌）**：切换至 `/admin` 的「九大智能体 & 战术大屏」，展示战术大屏与沉浸协同圆桌分镜工件抽屉，截取 `06_multi_agent_tactical_and_roundtable.png`；
  7. **场景 7（RAG 知识中台与 RAGAS 四维评测大屏）**：切换至 `/admin` 的「RAG 知识与评测」，展示四维雷达跑分大屏与评测流水线，截取 `07_rag_evaluation_and_graph.png`；
  8. **场景 8（短剧媒资编目治理与多云盘同步）**：切换至 `/admin` 的「短剧资产编目」，展示多云盘剧集列表与上下架治理面板，截取 `08_drama_shelf_and_cloud_sync.png`；
  9. **场景 9（内容安全合规风控台与 4 号审片官）**：切换至 `/admin` 的「互动合规风控」，展示 DFA 敏感词拦截队列与 4 号合规风控智能体工作台，截取 `09_danmaku_moderation_and_agent4.png`。
- **防重复硬性断言**：脚本结束前计算 9 张图的 MD5 哈希值，若存在任意重复则立即抛出异常熔断。

---

## 3. README.md 标准化重构章节规范

重构后的 `README.md` 严格包含以下 10 个标准化章节：
1. **项目名称、定位标语与核心能力徽章矩阵**
2. **一、立项背景与为什么做这个项目（Why CinemaAgent）**
   - 深度剖析：中小实体观影业态硬件存储成本高昂、多云盘资源孤岛、微短剧研创协同割裂、视听内容检索缺乏帧级定位与大模型幻觉、弹幕评论合规审核成本高等五大痛点及本项目的破局之道。
3. **二、适用领域与典型落地场景（Applicable Domains & Scenarios）**
   - **场景 1：小型商业观影与线下聚会娱乐业态（私人影院、点播影咖、足浴影音包厢、农院山庄、农家乐聚会场地、民宿轰趴馆、露营营地）**——零机房改造，直接挂载夸克、阿里、百度、联通沃盘、天翼、移动、115、OneDrive、WebDAV 等全网主流云盘，低成本构建专属院线点播系统；
   - **场景 2：微短剧/漫剧工作室与 MCN 机构 AIGC 协同研创中台**；
   - **场景 3：垂直流媒体互动社区与会员经济运营平台**；
   - **场景 4：AI Agent 多智能体协同与多模态 RAG 工程教学/科研标杆**。
4. **三、作品核心功能全景（What It Does）**
   - 涵盖多云盘 HTTP 206 流式直连、16:9/9:16 双模态播放与时间轴 RAG 伴读、二级评论与金币/VIP 经济闭环、Codex 观影灵宠、10 大智能体圆桌协同、BI 驾驶舱与 DFA 合规风控。
5. **四、标准化全栈技术栈矩阵（Tech Stack）**
   - 七大架构分层（前端表现层、后端服务层、多智能体与大模型网关层、多模态检索与评测层、多云盘聚合与流媒体层、数据持久化与安全风控层、容器化编排与自动化测试层）完整表格。
6. **五、系统全局架构与工作流设计（System Architecture）**
   - 内嵌 Mermaid 全栈分层架构图 + `docs/cinema_agent_architecture.drawio` 四大专题架构说明。
7. **六、系统实机运行全景展示（Live Screenshots）**
   - 嵌入并详解 9 张现场无头浏览器实时采集的高清实机截图（无任何重复画面）。
8. **七、工程物理目录拓扑结构（Project Structure）**
   - 展示清晰隔离的 `frontend/`、`backend/`、`tests/`、`docs/`、`docker-compose.yml` 目录树。
9. **八、快速启动与生产级 Docker 容器化部署指南（Quick Start & Docker Deployment）**
   - 同时提供 Windows 本地启动步骤与 Docker Compose 五容器一键部署流程（含 OpenList 与本地 Ollama 模型迁移指南链接）。
10. **九、全链路自动化测试与工程文档索引（Testing & Documentation Index）**

---

## 4. 原子实施清单（已于 2026-11-09 09:57:30 全部完成）

```markdown
实施清单：
1. [已完成] [编写测试脚本 tests/e2e/capture_readme_live_screenshots.py - 实现无头浏览器自动登录、9大核心模块实机渲染等待、高清截图采集至 docs/screenshots/ 与 tests/screenshots/，并内置 MD5 唯一性校验]
2. [已完成] [启动前后端服务并执行 Playwright 无头浏览器实时截图脚本，校验 9 张实机截图 100% 真实有效且零重复]
3. [已完成] [重构根目录 README.md - 写入完整的十章标准化文档，涵盖多云盘支持、私人影院/农院山庄/农家乐等适用领域、为什么做、做什么、分层技术栈表格及 9 张最新实机截图]
4. [已完成] [执行 Git 状态检查、提交 README.md 与最新实机截图并推送至远端仓库]
```
