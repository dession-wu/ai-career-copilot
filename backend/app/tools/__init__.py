"""
Career Co-Pilot Agent Tool Kit

工业级 Agent 工具集，为 ReAct Agent 提供外部能力。
每个工具都有完整的 Pydantic Schema 和文档，便于 LLM 理解何时调用。
"""

from .vault_tools import parse_resume, search_vault
from .job_tools import extract_jd_keywords, calculate_match_score, search_job_market
from .resume_tools import generate_resume_section
from .verification_tools import verify_facts

__all__ = [
    "parse_resume",
    "search_vault",
    "extract_jd_keywords",
    "calculate_match_score",
    "search_job_market",
    "generate_resume_section",
    "verify_facts",
]
