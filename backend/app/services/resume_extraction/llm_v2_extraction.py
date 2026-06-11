"""
LLM v2 提取模块 — 对标字节跳动投递网页 13 段
- 使用 JSON Schema 强约束
- 单次 LLM 调用输出 v2 结构
- 第二轮 consistency check 标注 needs_review
"""
import json
import logging
import time
import re
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from .models import (
    ResumeDataV2, PersonalInfoV2, EducationV2, InternshipV2, WorkV2, ProjectV2,
    PortfolioV2, CompetitionV2, SelfEvaluation, SocialAccountV2, SourceOfInfo,
    Certification, Award, Language, SkillEntry,
)
from .config import extraction_config

# 跨包导入 (与 v1 路径一致) — P0-2 修复：移除静默 import 兜底
# ImportError 应在启动时暴露，不应静默吞掉
from app.services.llm_service import get_llm_provider_manager as get_llm_service

logger = logging.getLogger(__name__)


# ==================== P0-2 新增：自定义异常类 ====================
class LLMUnavailableError(Exception):
    """LLM 服务不可用（API key 缺失/未配置/provider 不支持 chat）"""
    pass


class LLMCallError(Exception):
    """LLM 调用失败（超时/网络/限流）"""
    pass


class LLMParseError(Exception):
    """LLM 输出解析失败（非 JSON/字段缺失）"""
    pass


# ==================== v2 JSON Schema（用于 LLM 强约束）====================
LLM_V2_SCHEMA = {
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "enum": ["v2"]},
        "personal_info": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "linkedin": {"type": "string"},
                "website": {"type": "string"},
                "gender": {"type": "string", "enum": ["", "male", "female", "other"]},
                "age": {"type": ["integer", "null"]},
                "location_city": {"type": "string"},
                "intent_position": {"type": "string"},
                "intent_city": {"type": "string"},
                "current_status": {"type": "string", "enum": ["", "student", "fresh_graduate", "employed", "unemployed"]},
                "years_of_experience": {"type": ["integer", "null"]},
                "political_status": {"type": "string", "enum": ["", "party_member", "league_member", "mass"]},
                "expected_salary_min": {"type": ["integer", "null"]},
                "expected_salary_max": {"type": ["integer", "null"]},
                "id_card_type": {"type": "string", "enum": ["", "mainland", "hk", "macau", "taiwan", "foreign"]},
                "id_card_number": {"type": "string"},
            }
        },
        "has_work_experience": {"type": "boolean"},
        "educations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "school": {"type": "string"},
                    "degree": {"type": "string"},
                    "degree_type": {"type": "string", "enum": ["", "full_time", "part_time", "online", "self_study"]},
                    "field_of_study": {"type": "string"},
                    "gpa": {"type": ["string", "null"]},
                    "gpa_scale": {"type": "string"},
                    "gpa_rank": {"type": "string"},
                    "honors": {"type": "array", "items": {"type": "string"}},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "description": {"type": "string"},
                    "courses": {"type": "array", "items": {"type": "string"}},
                }
            }
        },
        "internships": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "department": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "description": {"type": "string"},
                    "achievements": {"type": "array", "items": {"type": "string"}},
                }
            }
        },
        "work_experiences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "department": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "description": {"type": "string"},
                    "achievements": {"type": "array", "items": {"type": "string"}},
                }
            }
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "project_link": {"type": "string"},
                    "description": {"type": "string"},
                    "contributions": {"type": "array", "items": {"type": "string"}},
                    "tech_stack": {"type": "array", "items": {"type": "string"}},
                    "project_outcome": {"type": "string"},
                }
            }
        },
        "portfolios": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "link": {"type": "string"},
                    "platform": {"type": "string"},
                    "role": {"type": "string"},
                    "description": {"type": "string"},
                    "date": {"type": "string"},
                }
            }
        },
        "competitions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "organizer": {"type": "string"},
                    "level": {"type": "string", "enum": ["", "international", "national", "provincial", "school", "other"]},
                    "date": {"type": "string"},
                    "result": {"type": "string"},
                    "role": {"type": "string"},
                }
            }
        },
        "certifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "issuer": {"type": "string"},
                    "date": {"type": "string"},
                    "expiry_date": {"type": "string"},
                    "credential_id": {"type": "string"},
                }
            }
        },
        "awards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "issuer": {"type": "string"},
                    "date": {"type": "string"},
                    "description": {"type": "string"},
                }
            }
        },
        "languages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "level": {"type": "string"},
                    "proficiency": {"type": "string"},
                    "score": {"type": "string"},
                }
            }
        },
        "self_evaluation": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "strengths": {"type": "array", "items": {"type": "string"}},
                "weaknesses": {"type": "array", "items": {"type": "string"}},
            }
        },
        "social_accounts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "enum": ["", "github", "linkedin", "csdn", "juejin", "zhihu", "xiaohongshu", "wechat", "weibo", "bilibili", "blog", "other"]},
                    "url": {"type": "string"},
                    "label": {"type": "string"},
                }
            }
        },
        "source": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "enum": ["", "referral", "official_website", "social_media", "campus_recruitment", "job_fair", "headhunter", "other"]},
                "detail": {"type": "string"},
            }
        },
    }
}


SYSTEM_PROMPT_V2 = """你是顶级简历解析助手。需要将候选人简历的原始文本转换为结构化 JSON。

**严格规则**：
1. **不能编造**：找不到的字段填 `null`（personal_info）或 `[]`（数组），不要猜测。
2. **日期格式**：统一用 `YYYY-MM` 形式（例：2023-09）；"至今"/"present" → 空字符串即可。
3. **实习/工作区分**：title 包含 "实习"/"intern"/"实习生" → 放 `internships`；否则 → `work_experiences`。
4. **竞赛 vs 奖项**：比赛/竞赛/挑战杯/Kaggle → `competitions`；奖学金/优秀学生/学院奖 → `awards`。
5. **作品 vs 项目**：项目通常有起止时间和角色描述，作品是链接形式（GitHub 仓库、Demo 站、博客文章）。
6. **语言能力**：英语/日语/法语等 + 等级（CET-4/雅思 7.0/托福 100/N1）。
7. **社交账号**：URL 模式识别（github.com/...→github, juejin.cn/...→juejin 等）。
8. **了解渠道**：文末提到 "内推"/"官网"/"校招" 等。

**输出要求**：
- 输出严格符合下面 JSON Schema 的对象
- `personal_info.name/email/phone` 必填, 否则 `confidence` 标 0
- 字段级 `confidence` 默认 0.8, 推断的标 0.6
- 推断存在歧义的字段在 `needs_review` 数组列出

**待解析简历文本**：
{text}
"""


def build_user_prompt_v2(text: str) -> str:
    return f"""请按以下 JSON Schema 输出解析结果：

```json
{json.dumps(LLM_V2_SCHEMA, ensure_ascii=False, indent=2)}
```

简历文本：
```
{text[:6000]}
```

只返回 JSON, 不要任何解释。"""


def extract_via_llm_v2(text: str, llm=None) -> Dict[str, Any]:
    """
    使用 LLM 进行 v2 提取, 返回 dict
    P0-2 修复：失败时抛异常（LLMUnavailableError/LLMCallError/LLMParseError），由上层降级到规则引擎
    """
    if not text or not text.strip():
        return ResumeDataV2.empty().to_dict()

    if llm is None:
        # P0-2: 不再静默 return 空，改为抛 LLMUnavailableError
        try:
            provider = get_llm_service()
            if provider is None or not hasattr(provider, "chat"):
                raise LLMUnavailableError("LLM provider 不可用，请检查 API key 配置")
            class _LLMAdapter:
                def chat(self, messages, temperature=0.1, max_tokens=4096):
                    if hasattr(provider, "chat"):
                        return provider.chat(messages, temperature=temperature, max_tokens=max_tokens)
                    raise LLMUnavailableError("LLM provider 不支持 chat 接口")
            llm = _LLMAdapter()
        except LLMUnavailableError:
            raise  # 让上层捕获并降级到规则引擎
        except Exception as e:
            logger.error(f"LLM 服务初始化失败: {e}", exc_info=True)
            raise LLMUnavailableError(f"LLM 服务初始化失败: {e}") from e

    user_prompt = build_user_prompt_v2(text)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_V2.format(text=text[:200])},
        {"role": "user", "content": user_prompt},
    ]

    start = time.time()
    try:
        result = llm.chat(messages, temperature=0.1, max_tokens=4096)
    except Exception as e:
        # P0-2: 抛 LLMCallError 而非返回空
        logger.error(f"LLM 调用失败: {e}")
        raise LLMCallError(f"LLM 调用失败: {e}") from e

    elapsed_ms = int((time.time() - start) * 1000)
    content = result if isinstance(result, str) else str(result)

    # 尝试解析 JSON — P0-2: 失败时抛 LLMParseError
    json_match = re.search(r"\{[\s\S]*\}", content)
    if not json_match:
        logger.warning("LLM 输出未匹配到 JSON, 触发降级到规则引擎")
        raise LLMParseError("LLM 输出未匹配到 JSON")

    try:
        data = json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        logger.warning(f"LLM JSON 解析失败: {e}, 触发降级到规则引擎")
        raise LLMParseError(f"LLM JSON 解析失败: {e}") from e

    # 写入 extraction_quality 时间
    if "extraction_quality" not in data:
        data["extraction_quality"] = {}
    data["extraction_quality"]["extraction_time_ms"] = elapsed_ms
    data["extraction_quality"]["parser_engine"] = "llm_v2"

    return data


def merge_with_rules_v2(llm_data: Dict[str, Any], rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """融合规则 + LLM 结果 — 优先级: 规则 > LLM (规则更准), 但 LLM 提供额外字段"""
    merged = dict(llm_data)
    # 个人主页 / 社交账号: 规则补全
    rule_socials = rule_data.get("social_accounts", [])
    if rule_socials:
        existing_urls = {s.get("url") for s in merged.get("social_accounts", [])}
        for s in rule_socials:
            if s.get("url") and s["url"] not in existing_urls:
                merged.setdefault("social_accounts", []).append(s)
    # 竞赛: 规则补全
    rule_competitions = rule_data.get("competitions", [])
    if rule_competitions:
        existing_names = {c.get("name") for c in merged.get("competitions", [])}
        for c in rule_competitions:
            if c.get("name") and c["name"] not in existing_names:
                merged.setdefault("competitions", []).append(c)
    # 作品: 规则补全
    rule_portfolios = rule_data.get("portfolios", [])
    if rule_portfolios:
        existing_links = {p.get("link") for p in merged.get("portfolios", [])}
        for p in rule_portfolios:
            if p.get("link") and p["link"] not in existing_links:
                merged.setdefault("portfolios", []).append(p)
    # 自我评价: 任一非空即可
    rule_eval = rule_data.get("self_evaluation", {})
    if rule_eval and not merged.get("self_evaluation", {}).get("text"):
        merged["self_evaluation"] = rule_eval
    # 了解渠道: 规则补全
    rule_source = rule_data.get("source", {})
    if rule_source and not merged.get("source", {}).get("channel"):
        merged["source"] = rule_source
    # 语言: 规则补全考试名/分值
    rule_langs = rule_data.get("languages_enhanced", [])
    if rule_langs:
        existing_keys = {(l.get("name"), l.get("level")) for l in merged.get("languages", [])}
        for l in rule_langs:
            key = (l.get("name"), l.get("level"))
            if key not in existing_keys and l.get("name"):
                merged.setdefault("languages", []).append(l)
    return merged


def compute_field_confidence(data: Dict[str, Any]) -> Dict[str, Any]:
    """根据填充度计算字段级置信度, 并自动标记 needs_review"""
    field_scores: Dict[str, float] = {}

    # Personal info
    pi = data.get("personal_info", {})
    pi_filled = sum(1 for k in ["name", "email", "phone", "id_card_number"] if pi.get(k))
    field_scores["personal_info"] = min(1.0, 0.4 + pi_filled * 0.15)

    # Education
    edus = data.get("educations", [])
    if edus:
        ed_filled = sum(1 for e in edus if e.get("school") and e.get("degree") and e.get("start_date"))
        field_scores["educations"] = min(1.0, 0.5 + (ed_filled / max(len(edus), 1)) * 0.5)
    else:
        field_scores["educations"] = 0.0

    # Internships / work
    field_scores["internships"] = 0.8 if data.get("internships") else 0.0
    field_scores["work_experiences"] = 0.8 if data.get("work_experiences") else 0.0

    # Projects / portfolios / competitions / certifications / awards / languages
    for k in ["projects", "portfolios", "competitions", "certifications", "awards", "languages",
              "social_accounts"]:
        field_scores[k] = 0.7 if data.get(k) else 0.0

    # self_evaluation / source
    field_scores["self_evaluation"] = 0.7 if data.get("self_evaluation", {}).get("text") else 0.0
    field_scores["source"] = 0.7 if data.get("source", {}).get("channel") else 0.0

    # 写入 extraction_quality
    if "extraction_quality" not in data:
        data["extraction_quality"] = {}
    data["extraction_quality"]["field_scores"] = field_scores

    # 标记 needs_review: 必识别字段 (name/email/phone) 缺失 OR 教育缺失
    needs_review = (
        not (pi.get("name") and pi.get("phone"))
        or len(edus) == 0
    )
    data["needs_review"] = needs_review
    if "extraction_quality" in data:
        data["extraction_quality"]["low_confidence_fields"] = [
            k for k, v in field_scores.items() if v < 0.6
        ]
    return data
