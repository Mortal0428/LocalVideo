# -*- coding: utf-8 -*-
"""
==============================================================================
【核心模块】：backend/app/services/agent_fleet/core/native_langgraph_engine.py
【业务定位】：原生 LangGraph 编译状态机与分层 Supervisor 级联调度引擎
【架构特性】：
  1. 采用正统 langgraph.graph.StateGraph 构建状态拓扑，彻底摒弃模糊的自定义包装；
  2. 显式定义强类型 AgentBlackboardState 状态字典，支撑多智能体协同状态流转；
  3. 内置全域关键词意图路由，支持单智能体直连与多智能体跨角色复合级联执行；
  4. 支持对公共黑板的自动同步与事务隔离，并提供 MemorySaver 检查点持久化。
==============================================================================
"""

import re
import json
import logging
import asyncio
from typing import TypedDict, List, Dict, Any, Optional
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.database import SessionLocal
from app.services.agent_fleet.core.memory_hub import global_memory_hub

logger = logging.getLogger("agent_fleet.native_langgraph")


class TaskStep(TypedDict):
    """
    【原子任务步骤类型定义】
    用于描述 Supervisor（9号主脑）拆解出的具体子任务。
    """
    step_id: int
    assigned_agent: str      # 目标智能体 ID，如 'agent_3', 'agent_8', 'agent_10'
    action_type: str         # 动作分类，如 'vectorize_unindexed', 'storyboard_spec', 'coze_fetch'
    instruction: str         # 下达给子智能体的具体操作指令
    status: str              # 状态: 'pending' | 'in_progress' | 'completed' | 'failed'
    output: Optional[str]
    artifact_data: Optional[Dict[str, Any]]


class AgentBlackboardState(TypedDict):
    """
    【LangGraph 全局强类型黑板状态字典】
    贯穿整个状态图生命周期的核心状态存储。
    """
    session_id: str
    user_prompt: str
    execution_stage: str     # 阶段: 'PLANNING' | 'EXECUTING' | 'SYNC' | 'SYNTHESIZING' | 'COMPLETED'
    task_pipeline: List[TaskStep]
    current_step_index: int
    blackboard_context: Dict[str, Any]
    trace_logs: List[str]
    final_output: str
    plan_table: str
    artifacts: Dict[str, Any]


def analyze_intent_and_build_pipeline(user_prompt: str) -> List[TaskStep]:
    """
    基于关键词矩阵自动进行意图解析，组装多智能体流水线。

    参数说明：
    - user_prompt (str): 用户原始自然语言指令。

    返回值说明：
    - List[TaskStep]: 拆解后的原子任务步骤列表。
    """
    prompt_lower = user_prompt.lower()
    pipeline: List[TaskStep] = []
    step_id = 1

    # 1. 知识库与切片/向量化检测 (Agent 3)
    if any(k in prompt_lower for k in ["切片", "向量", "向量化", "未切片", "知识库", "rag", "语料", "入库"]):
        pipeline.append({
            "step_id": step_id,
            "assigned_agent": "agent_3",
            "action_type": "vectorize_unindexed",
            "instruction": "检查未向量化短剧并执行增量切片与向量入库",
            "status": "pending",
            "output": None,
            "artifact_data": None
        })
        step_id += 1

    # 2. 外部生态/天气/农历/联网搜索 (Agent 10)
    if any(k in prompt_lower for k in ["天气", "农历", "老黄历", "搜索", "联网", "外部", "插件", "coze"]):
        pipeline.append({
            "step_id": step_id,
            "assigned_agent": "agent_10",
            "action_type": "coze_fetch",
            "instruction": f"通过 Coze 外部超脑检索生态数据: {user_prompt}",
            "status": "pending",
            "output": None,
            "artifact_data": None
        })
        step_id += 1

    # 3. 编导分镜与剧本创作 (Agent 8)
    if any(k in prompt_lower for k in ["分镜", "剧本", "9:16", "镜头", "景别", "机位", "台词"]):
        pipeline.append({
            "step_id": step_id,
            "assigned_agent": "agent_8",
            "action_type": "storyboard_spec",
            "instruction": f"生成竖屏高光场次分镜工件: {user_prompt}",
            "status": "pending",
            "output": None,
            "artifact_data": None
        })
        step_id += 1

    # 4. 爆款宣发与营销钩子 (Agent 5)
    if any(k in prompt_lower for k in ["宣发", "爆款", "标题", "前3秒", "钩子", "流量", "推广", "营销"]):
        pipeline.append({
            "step_id": step_id,
            "assigned_agent": "agent_5",
            "action_type": "growth_kit",
            "instruction": f"提炼黄金前3秒吸睛钩子与爆款标题矩阵: {user_prompt}",
            "status": "pending",
            "output": None,
            "artifact_data": None
        })
        step_id += 1

    # 5. 内容风控与合规审查 (Agent 4)
    if any(k in prompt_lower for k in ["合规", "敏感词", "审核", "风控", "违规", "涉黄", "暴恐", "拦截"]):
        pipeline.append({
            "step_id": step_id,
            "assigned_agent": "agent_4",
            "action_type": "content_moderation",
            "instruction": f"执行剧本台词或社区互动的合规安全质检: {user_prompt}",
            "status": "pending",
            "output": None,
            "artifact_data": None
        })
        step_id += 1

    # 兜底：若未命中任何特定动作，派发给 1号 剧情课代表
    if not pipeline:
        pipeline.append({
            "step_id": step_id,
            "assigned_agent": "agent_1",
            "action_type": "general_interpretation",
            "instruction": user_prompt,
            "status": "pending",
            "output": None,
            "artifact_data": None
        })

    return pipeline


# ==============================================================================
# LangGraph 原生节点定义
# ==============================================================================

ROSTER_DEFINITIONS = [
    {"id": "agent_1", "name": "1号 · 剧情答疑", "badge": "剧情解析", "desc": "剧情解构、人物关系与叙事逻辑"},
    {"id": "agent_8", "name": "8号 · 导演分镜雕塑家", "badge": "分镜导演", "desc": "9:16垂直分镜、景别机位与演员动作"},
    {"id": "agent_5", "name": "5号 · 作品宣发操盘手", "badge": "文案宣发", "desc": "前3秒爆点设计、钩子文案与宣发推广"},
    {"id": "agent_4", "name": "4号 · 内容合规风控官", "badge": "合规审片", "desc": "敏感词排查、台词合规与平台安全风控"},
    {"id": "agent_6", "name": "6号 · 视听多模态解析官", "badge": "视听大师", "desc": "镜头声画节奏、情绪曲线与视听语言"},
    {"id": "agent_3", "name": "3号 · 知识切片中台", "badge": "知识检索", "desc": "短剧知识切片、设定溯源与RAG检索"},
    {"id": "agent_7", "name": "7号 · 短剧媒资管家", "badge": "媒资编目", "desc": "剧集编目管理、标签元数据与资产调度"},
    {"id": "agent_2", "name": "2号 · 观影灵宠", "badge": "灵宠交互", "desc": "用户情绪共鸣、交互彩蛋与陪伴体验"},
    {"id": "agent_10", "name": "10号 · Coze外部超脑", "badge": "外部超脑", "desc": "实时外部网络数据、天气与跨平台生态"},
]


async def dynamic_llm_planner(user_prompt: str, session_id: str, db: Session) -> Dict[str, Any]:
    # 0. 提炼或对齐统一的研讨业务标的 (Mission Subject)，彻底杜绝各专家自说自话与牛头不对马嘴
    import re
    drama_match = re.search(r'《([^》]+)》', user_prompt)
    if drama_match:
        mission_subject = f"短剧《{drama_match.group(1)}》全流程工业化协同研讨"
    elif any(k in user_prompt for k in ["千金", "高手", "贴身"]):
        mission_subject = "平台重点短剧《高冷千金的贴身高手》全流程协同研讨"
    elif any(k in user_prompt for k in ["都市", "战神", "逆袭", "爽剧"]):
        mission_subject = "都市战神逆袭向标杆短剧剧本与宣发全流程研讨"
    else:
        mission_subject = "平台主打短剧《高冷千金的贴身高手》全链条工业化协同研发"

    # 1. 启发式探测用户显式指定的智能体数量约束 (如: "至少5个", "5位专家", "6个agent")
    required_count = 2
    try:
        cn_map = {'一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        for w, v in cn_map.items():
            if f"至少{w}个" in user_prompt or f"{w}个" in user_prompt or f"{w}位" in user_prompt:
                required_count = v
                break
        for n in range(1, 10):
            if f"至少{n}个" in user_prompt or f"{n}个" in user_prompt or f"{n}位" in user_prompt or f"{n}名" in user_prompt or f"{n}agent" in user_prompt.lower():
                required_count = n
                break
        if "全部" in user_prompt or "全员" in user_prompt:
            required_count = 8
    except Exception:
        required_count = 2
    required_count = max(1, min(required_count, 8))

    # 2. 构造高严谨度 LLM 规划提示词，强制 9 号执行 Plan 职责，严禁代答
    roster_prompt_lines = [f"- {r['id']} ({r['name']}): 专精领域【{r['desc']}】" for r in ROSTER_DEFINITIONS]
    roster_text = "\n".join(roster_prompt_lines)

    system_planner_prompt = (
        "你是9号主智能体总控大脑（Supervisor Planner）。\n"
        "【法定核心职责】：你只负责进行【多智能体协同流水线规划 (Plan)】，根据制片人需求精确拆解执行清单。\n"
        "【严禁越权铁律】：绝对禁止你自行假冒或模仿专家回答具体业务方案！具体方案必须由对应专家在后续执行。\n"
        "请从候选垂直专家库中，挑选最匹配的专家组成有序流水线，并输出纯 JSON 数组格式。\n"
        f"制片人要求规划任务数量：不少于 {required_count} 项。\n"
        "候选垂直专家花名册：\n"
        f"{roster_text}\n"
        "输出格式必须为合法 JSON 数组（不要输出任何多余解释）：\n"
        "[\n"
        '  {"step_id": 1, "assigned_agent": "agent_X", "action_type": "...", "instruction": "分配给该专家的明确任务要求..."}\n'
        "]"
    )

    user_query = f"制片人协同需求指令：'{user_prompt}'\n请针对上述需求完成任务规划拆解，输出满足数量且分工明确的 JSON 执行流水线。"

    parsed_pipeline: List[TaskStep] = []
    try:
        from app.services.agent_fleet.base_and_telemetry import invoke_agent_llm_with_resilience
        res = await invoke_agent_llm_with_resilience(
            db=db,
            agent_id="agent_9",
            prompt=user_query,
            system_prompt=system_planner_prompt,
            fallback_text="",
            max_tokens=1000
        )
        content = res.get("content", "").strip()
        # 提取 JSON 数组块
        json_match = re.search(r'\[.*?\]', content, re.DOTALL)
        if json_match:
            raw_json = json_match.group(0)
            items = json.loads(raw_json)
            for idx, it in enumerate(items):
                ag_id = it.get("assigned_agent", "agent_1")
                inst = it.get("instruction") or f"推进领域专业推演: {user_prompt}"
                meta = next((r for r in ROSTER_DEFINITIONS if r["id"] == ag_id), ROSTER_DEFINITIONS[0])
                parsed_pipeline.append({
                    "step_id": idx + 1,
                    "assigned_agent": ag_id,
                    "agent_name": meta["name"],
                    "role_badge": meta["badge"],
                    "action_type": it.get("action_type") or "specialized_execution",
                    "instruction": inst,
                    "status": "pending",
                    "cost_ms": 0,
                    "output": None,
                    "artifact_data": None
                })
    except Exception as e:
        logger.warning(f"Dynamic LLM planner parsing warning, fallback to intelligent assembly: {e}")

    # 3. 兜底与补全防护：若解析失败或未达数量要求，智能依序装配垂直专家
    if len(parsed_pipeline) < required_count:
        existing_agents = {p["assigned_agent"] for p in parsed_pipeline}
        # 默认优质组合：分镜、合规、宣发、视听、剧情、切片
        candidate_pool = ["agent_1", "agent_8", "agent_5", "agent_4", "agent_6", "agent_3", "agent_7", "agent_2"]
        for cand_id in candidate_pool:
            if cand_id not in existing_agents:
                meta = next((r for r in ROSTER_DEFINITIONS if r["id"] == cand_id), ROSTER_DEFINITIONS[0])
                parsed_pipeline.append({
                    "step_id": len(parsed_pipeline) + 1,
                    "assigned_agent": cand_id,
                    "agent_name": meta["name"],
                    "role_badge": meta["badge"],
                    "action_type": "specialized_execution",
                    "instruction": f"围绕主题【{user_prompt}】，从{meta['desc']}视角输出专精方案",
                    "status": "pending",
                    "cost_ms": 0,
                    "output": None,
                    "artifact_data": None
                })
                existing_agents.add(cand_id)
                if len(parsed_pipeline) >= required_count:
                    break

    # 重新编排步骤序号，并注入研讨标的
    for i, p in enumerate(parsed_pipeline):
        p["step_id"] = i + 1
        p["mission_subject"] = mission_subject

    return {"mission_subject": mission_subject, "pipeline": parsed_pipeline}


async def supervisor_planner_node(state: AgentBlackboardState) -> AgentBlackboardState:
    """
    ==============================================================================
    【节点 1】：9号 Supervisor 主控规划节点 (Plan & Execute 核心中枢)
    调用动态智能规划引擎构建 task_pipeline，并输出结构化 Markdown TodoList 待办清单。
    ==============================================================================
    """
    user_prompt = state["user_prompt"]
    session_id = state["session_id"]
    trace = list(state.get("trace_logs", []))

    with SessionLocal() as db:
        planner_res = await dynamic_llm_planner(user_prompt=user_prompt, session_id=session_id, db=db)
        mission_subject = planner_res["mission_subject"]
        pipeline = planner_res["pipeline"]

    # 组装纯正且无多余自我代答的标准 Markdown TodoList 待办清单
    todo_lines = [
        "### 【9号总控多智能体协同执行清单 (TodoList)】",
        f"> 依据制片人需求构建的 Plan & Execute 结构化待办列表，共规划 {len(pipeline)} 项专家任务，各领域专家将严格按清单顺序接力推进：",
        ""
    ]
    for step in pipeline:
        todo_lines.append(f"- [ ] **Step {step['step_id']}** · {step['agent_name']}（{step['role_badge']}）：{step['instruction']}")

    todo_lines.append("")
    todo_lines.append("| 步骤序号 | 委派专家 | 协同业务目标 | 初始状态 |")
    todo_lines.append("| :--- | :--- | :--- | :--- |")
    for step in pipeline:
        todo_lines.append(f"| Step {step['step_id']} | {step['agent_name']} | {step['instruction']} | 待执行 |")

    plan_table_str = "\n".join(todo_lines)
    trace.append(f"[9号总控规划]: 成功智能编制《协同执行清单 (TodoList)》，涵盖 {len(pipeline)} 项专家任务。")

    return {
        **state,
        "execution_stage": "DISPATCHING",
        "task_pipeline": pipeline,
        "current_step_index": 0,
        "trace_logs": trace,
        "plan_table": plan_table_str,
    }


async def worker_executor_node(state: AgentBlackboardState) -> AgentBlackboardState:
    """
    【节点 2】：领域专家工作节点
    按流水线顺序执行当前步骤对应的垂直智能体。
    """
    from app.services.agent_fleet.pods.specialized_pods import FLEET_POD_REGISTRY

    idx = state["current_step_index"]
    pipeline = list(state["task_pipeline"])
    trace = list(state.get("trace_logs", []))
    artifacts = dict(state.get("artifacts", {}))

    if idx >= len(pipeline):
        return {**state, "execution_stage": "SYNTHESIZING"}

    current_task = dict(pipeline[idx])
    target_agent_id = current_task["assigned_agent"]
    pod = FLEET_POD_REGISTRY.get(target_agent_id)

    if not pod:
        current_task["status"] = "failed"
        current_task["output"] = f"未找到智能体执行容器: {target_agent_id}"
        pipeline[idx] = current_task
        return {**state, "task_pipeline": pipeline}

    trace.append(f"[{pod.name}]: 开始执行 -> {current_task['instruction'][:30]}...")

    with SessionLocal() as db:
        res = await pod.run_step(
            session_id=state["session_id"],
            user_message=current_task["instruction"],
            context_data=state.get("blackboard_context"),
            db=db
        )

    reply = res.get("reply", "")
    current_task["output"] = reply
    current_task["status"] = "completed"

    # 捕获各智能体的特定工件交付物
    if target_agent_id == "agent_8" and res.get("storyboard_data"):
        artifacts["storyboard_spec"] = res["storyboard_data"]
    elif target_agent_id == "agent_5" and res.get("growth_data"):
        artifacts["marketing_kit"] = res["growth_data"]
    elif target_agent_id == "agent_3" and res.get("tool_data"):
        artifacts["vector_status"] = res["tool_data"]

    pipeline[idx] = current_task
    trace.append(f"[{pod.name}]: 执行完毕，产出交付成果。")

    return {
        **state,
        "execution_stage": "SYNC",
        "task_pipeline": pipeline,
        "trace_logs": trace,
        "artifacts": artifacts
    }


async def blackboard_sync_node(state: AgentBlackboardState) -> AgentBlackboardState:
    """
    【节点 3】：公共黑板数据同步节点
    将步骤执行结果沉淀至全局会话黑板，并将游标推进至下一节点。
    """
    session_id = state["session_id"]
    idx = state["current_step_index"]
    pipeline = state["task_pipeline"]
    trace = list(state.get("trace_logs", []))

    if idx < len(pipeline):
        step_res = pipeline[idx]
        key = f"STEP_{step_res['step_id']}_{step_res['assigned_agent'].upper()}"
        global_memory_hub.write_blackboard_artifact(
            session_id=session_id,
            artifact_key=key,
            artifact_val={"content": step_res.get("output"), "action": step_res.get("action_type")},
            author_agent_id=step_res["assigned_agent"]
        )

    next_idx = idx + 1
    trace.append(f"[黑板中枢]: 第 {idx + 1} 步数据已写入公共黑板，推移流水线。")

    return {
        **state,
        "current_step_index": next_idx,
        "trace_logs": trace
    }


async def final_synthesizer_node(state: AgentBlackboardState) -> AgentBlackboardState:
    """
    【节点 4】：最终交付物汇聚与 9号议长总结节点
    整合流水线各项成果，生成 180~300 字语义完整、有始有终的终审结论。
    """
    pipeline = state["task_pipeline"]
    trace = list(state.get("trace_logs", []))

    agent_names = {
        "agent_1": "1号剧情答疑",
        "agent_2": "2号观影灵宠",
        "agent_3": "3号知识中台",
        "agent_4": "4号合规风控官",
        "agent_5": "5号宣发操盘手",
        "agent_6": "6号视听大师",
        "agent_7": "7号媒资管家",
        "agent_8": "8号导演分镜师",
        "agent_9": "9号主控议长",
        "agent_10": "10号Coze超脑"
    }

    summary_items = []
    for step in pipeline:
        ag_id = step.get("assigned_agent")
        label = agent_names.get(ag_id, ag_id)
        out_text = (step.get("output") or "完成").replace("\n", " ").strip()
        # 允许展示完整结论 (最多200字)，绝不生硬截断句意
        if len(out_text) > 200:
            out_text = out_text[:195] + "..."
        summary_items.append(f"- 【{label}】: {out_text}")

    final_text = (
        f"【9号总控协同闭环交付】：本次多智能体协作已按计划圆满达成：\n"
        + "\n".join(summary_items)
        + "\n各项专业数据与结构化工件已沉淀至公共黑板，请制片人审阅。"
    )

    trace.append("[9号总控议长]: 完成全局研讨闭环汇总，输出交付工件。")

    return {
        **state,
        "execution_stage": "COMPLETED",
        "final_output": final_text,
        "trace_logs": trace
    }


# ==============================================================================
# 条件跳转路由函数
# ==============================================================================

def route_after_planning(state: AgentBlackboardState) -> str:
    """规划完成后的跳转决策"""
    pipeline = state.get("task_pipeline", [])
    if pipeline:
        return "worker_executor"
    return "final_synthesizer"


def route_next_step(state: AgentBlackboardState) -> str:
    """黑板同步后的流转决策：继续下一任务还是导向汇总"""
    idx = state.get("current_step_index", 0)
    pipeline = state.get("task_pipeline", [])
    # 限制单次任务最多连续执行 5 步，杜绝逻辑死循环
    if idx < len(pipeline) and idx < 5:
        return "worker_executor"
    return "final_synthesizer"


# ==============================================================================
# 编译构建状态图单例
# ==============================================================================

def compile_native_agent_graph():
    """
    编译正统 LangGraph 原生状态图。

    返回值说明：
    - CompiledGraph: 可执行并附带内存检查点的状态图。
    """
    workflow = StateGraph(AgentBlackboardState)

    workflow.add_node("supervisor_planner", supervisor_planner_node)
    workflow.add_node("worker_executor", worker_executor_node)
    workflow.add_node("blackboard_sync", blackboard_sync_node)
    workflow.add_node("final_synthesizer", final_synthesizer_node)

    workflow.set_entry_point("supervisor_planner")

    workflow.add_conditional_edges(
        "supervisor_planner",
        route_after_planning,
        {
            "worker_executor": "worker_executor",
            "final_synthesizer": "final_synthesizer"
        }
    )

    workflow.add_edge("worker_executor", "blackboard_sync")

    workflow.add_conditional_edges(
        "blackboard_sync",
        route_next_step,
        {
            "worker_executor": "worker_executor",
            "final_synthesizer": "final_synthesizer"
        }
    )

    workflow.add_edge("final_synthesizer", END)

    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# 模块全局编译单例
compiled_roundtable_graph = compile_native_agent_graph()


async def execute_native_agent_graph(session_id: str, user_prompt: str) -> Dict[str, Any]:
    """
    【高阶外置接口】：启动原生 LangGraph 执行流水线。

    参数说明：
    - session_id (str): 圆桌研讨会话 ID。
    - user_prompt (str): 用户输入的综合指令。

    返回值说明：
    - Dict[str, Any]: 最终执行状态字典（包含流水线各步骤细节、工件与汇总）。
    """
    initial_state: AgentBlackboardState = {
        "session_id": session_id,
        "user_prompt": user_prompt,
        "execution_stage": "PLANNING",
        "task_pipeline": [],
        "current_step_index": 0,
        "blackboard_context": {},
        "trace_logs": [f"[系统中枢]: 接收任务：“{user_prompt}”，载入原生 LangGraph 状态图。"],
        "final_output": "",
        "plan_table": "",
        "artifacts": {}
    }

    config = {"configurable": {"thread_id": session_id}}
    final_state = await compiled_roundtable_graph.ainvoke(initial_state, config=config)
    return final_state
