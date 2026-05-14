"""
Career Co-Pilot Agent 系统

工业级 Multi-Agent 架构的核心模块。
当前 Phase 1 实现:
- ResumeTailorAgent: 简历定制 Agent（ReAct 模式）

后续 Phase 将添加:
- JDAnalystAgent: JD 分析 Agent
- InterviewCoachAgent: 面试教练 Agent
- CareerSupervisor: 主管 Agent（Multi-Agent 编排）
"""

from .resume_tailor import ResumeTailorAgent, get_resume_tailor_agent

__all__ = [
    "ResumeTailorAgent",
    "get_resume_tailor_agent",
]
