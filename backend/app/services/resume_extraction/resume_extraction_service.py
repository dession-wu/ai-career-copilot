"""
简历信息提取服务
对外提供统一的简历提取接口
v2 路径: 规则 + LLM 双通道 → result_fusion_v2 → quality_assessor.assess_v2
"""
import asyncio
import logging
import re
import time
from typing import Dict, Any, Optional

from .extraction_engine import get_extraction_engine
from .quality_assessor import get_quality_assessor
from .result_fusion import get_result_fusion_v2
from .llm_v2_extraction import (
    extract_via_llm_v2,
    compute_field_confidence,
    merge_with_rules_v2,
    LLMUnavailableError,
    LLMCallError,
    LLMParseError,
)
from .rule_engine import get_rule_engine
from .layout_analyzer import get_layout_analyzer
from .pdf_parser import get_pdf_parser
from .smart_router import get_smart_router
from .ab_router import get_ab_router  # ★ P0-11 新增：A/B 实验分流 + 监控埋点
from .models import (
    ResumeData, QualityReport, ResumeDataV2,
    PersonalInfoV2, EducationV2, InternshipV2, WorkV2, ProjectV2,
    PortfolioV2, CompetitionV2, SelfEvaluation, SocialAccountV2, SourceOfInfo,
    ParsedDocument, PDFType,
)

logger = logging.getLogger(__name__)


def _emit_extraction_metric(
    user_id: str,
    bucket: str,
    quality_score: float,
    elapsed_ms: int,
    degraded: bool,
    field_count: int,
):
    """
    P0-10 / P2-6 监控埋点：发出提取质量指标
    生产环境应替换为 Prometheus / Datadog / OSS / StatsD
    """
    # ★ P0-11: 改用 A/B 路由（ab_router）替代 smart_router
    ab = get_ab_router()
    ab.record_metric(
        user_id=user_id or "anonymous",
        experiment_name="resume_extraction_v1",
        bucket=bucket,
        metric="extraction_quality_score",
        value=quality_score,
        meta={
            "elapsed_ms": elapsed_ms,
            "degraded": degraded,
            "field_count": field_count,
        },
    )
    logger.info(
        f"[P0-10] extraction_quality_score user={user_id[:8] if user_id else 'anon'} "
        f"bucket={bucket} score={quality_score:.3f} elapsed_ms={elapsed_ms} "
        f"degraded={degraded} fields={field_count}"
    )


def _normalize_date(date_str: str) -> str:
    """
    统一日期格式为 YYYY-MM
    支持: YYYY.MM / YYYY/MM / YYYY-MM / YYYY年MM月 / YYYY / "至今" / "Present"
    """
    if not date_str or not isinstance(date_str, str):
        return ""
    s = date_str.strip()
    if not s:
        return ""
    # 至今 / present 原样保留
    if s in ("至今", "现在", "Present", "present", "Now", "now"):
        return s
    # YYYY.MM / YYYY/MM / YYYY-MM
    m = re.match(r'^(\d{4})[\.\-/](\d{1,2})$', s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    # YYYY年MM月
    m = re.match(r'^(\d{4})年(\d{1,2})月?$', s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    # YYYY-MM-DD 截取前 7
    m = re.match(r'^(\d{4})-(\d{1,2})-\d{1,2}$', s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    # YYYY
    m = re.match(r'^(\d{4})$', s)
    if m:
        return f"{m.group(1)}-01"
    return s


class ResumeExtractionService:
    """简历信息提取服务 - 默认 v2"""

    def __init__(self):
        self.extraction_engine = get_extraction_engine()
        self.quality_assessor = get_quality_assessor()
        self.fusion_v2 = get_result_fusion_v2()
        self.rule_engine = get_rule_engine()
        self.layout_analyzer = get_layout_analyzer()
        self.pdf_parser = get_pdf_parser()

    # ==================== v2 主路径 (默认) ====================
    async def extract_from_file_v2(
        self,
        file_path: str,
        user_id: Optional[str] = None,
        use_llm: bool = True,
    ) -> Dict[str, Any]:
        """
        从文件提取简历信息 (v2 路径)

        Returns:
            {
                "success": bool,
                "data": ResumeDataV2 dict,
                "quality": ExtractionQuality dict,
                "needs_review": bool,
                "extraction_time_ms": int,
                "sources": dict  # 字段级来源 rule / llm / fused
            }
        """
        start = time.time()
        logger.info(f"[v2] 开始提取简历: {file_path}, user_id={user_id}")

        try:
            # 1. PDF 解析 + 版面分析
            document = self.pdf_parser.parse(file_path)
            structure = self.layout_analyzer.analyze(document)
            document.structure = structure
            text = document.full_text or document.raw_text

            # 2. 规则引擎 v2 提取
            rule_result = self.rule_engine.extract_v2(document, structure)
            # 补全 v1 提取 (educations/internships/work/projects/languages 等基础段位)
            rule_v1 = self.rule_engine.extract(document, structure)
            rule_result = self._merge_v1_into_v2(rule_result, rule_v1)

            # 3. LLM v2 提取 (可选, 失败降级)
            llm_result: Dict[str, Any] = {}
            if use_llm:
                try:
                    llm_result = extract_via_llm_v2(text)
                except Exception as e:
                    logger.warning(f"LLM v2 提取失败, 降级: {e}")

            # 4. 融合规则 + LLM
            fused = self.fusion_v2.fuse(rule_result, llm_result)
            fused["raw_text_preview"] = text[:2000]

            # 5. 计算字段级置信度
            fused = compute_field_confidence(fused)

            # 6. 质量评估
            elapsed_ms = int((time.time() - start) * 1000)
            quality = self.quality_assessor.assess_v2(
                fused,
                raw_text=text,
                parser_engine="rule+llm_v2" if llm_result else "rule_v2",
            )
            quality["extraction_time_ms"] = elapsed_ms
            fused["extraction_quality"] = quality

            # 7. needs_review
            needs_review = bool(fused.get("needs_review")) or quality["confidence_score"] < 0.7
            fused["needs_review"] = needs_review

            # P0-10 监控埋点
            try:
                # ★ P0-11: 改用 A/B 路由分流
                bucket = get_ab_router().assign_bucket(user_id or "anon", "resume_extraction_v1")
                field_count = sum(1 for v in (fused.get("personal_info") or {}).values() if v)
                field_count += len(fused.get("educations") or [])
                field_count += len(fused.get("work_experiences") or [])
                _emit_extraction_metric(
                    user_id=user_id or "anon",
                    bucket=bucket,
                    quality_score=quality.get("confidence_score", 0.0),
                    elapsed_ms=elapsed_ms,
                    degraded=False,
                    field_count=field_count,
                )
            except Exception as e:
                logger.warning(f"[P0-10] metric emission failed (non-fatal): {e}")

            return {
                "success": True,
                "data": fused,
                "quality": quality,
                "needs_review": needs_review,
                "extraction_time_ms": elapsed_ms,
                "schema_version": "v2",
            }

        except Exception as e:
            logger.warning(f"[v2] 简历提取失败, 降级到 v1 规则引擎: {e}", exc_info=True)
            # ★ P0-3: 异常降级到 v1 路径（同步调用），不再返回空数据
            try:
                v1_result = await self.extract_from_text(text, user_id)
                if v1_result.get("success"):
                    return {
                        "success": True,
                        "data": v1_result["data"],
                        "v2_data": v1_result.get("v2_data", {}),
                        "quality": v1_result.get("quality", {}),
                        "needs_review": True,
                        "degraded": True,
                        "extraction_time_ms": int((time.time() - start) * 1000),
                        "schema_version": "v1_fallback",
                    }
            except Exception as fallback_err:
                logger.error(f"[v2] 降级到 v1 也失败: {fallback_err}", exc_info=True)
            # 终极兜底：返回 v2 empty（标记为失败）
            return {
                "success": False,
                "error": str(e),
                "data": ResumeDataV2.empty().to_dict(),
                "quality": self.quality_assessor.assess_v2({}),
                "needs_review": True,
                "degraded": True,
                "extraction_time_ms": int((time.time() - start) * 1000),
                "schema_version": "v2",
            }

    async def extract_from_text_v2(
        self,
        text: str,
        user_id: Optional[str] = None,
        use_llm: bool = True,
    ) -> Dict[str, Any]:
        """
        从文本提取简历信息 (v2 路径)
        """
        start = time.time()
        logger.info(f"[v2] 开始文本提取, user_id={user_id}, len={len(text)}")

        try:
            # 1. 构造 ParsedDocument
            document = ParsedDocument(
                raw_text=text,
                text_blocks=[],
                image_blocks=[],
                pdf_type=PDFType.TEXT,
                page_count=1,
                metadata={"source": "text"},
                full_text=text,
            )
            structure = self.layout_analyzer.analyze(document)
            document.structure = structure

            # 2. 规则引擎 v2
            rule_result = self.rule_engine.extract_v2(document, structure)
            rule_v1 = self.rule_engine.extract(document, structure)
            rule_result = self._merge_v1_into_v2(rule_result, rule_v1)

            # 3. LLM v2
            llm_result: Dict[str, Any] = {}
            if use_llm:
                try:
                    llm_result = extract_via_llm_v2(text)
                except Exception as e:
                    logger.warning(f"LLM v2 提取失败: {e}")

            # 4. 融合
            fused = self.fusion_v2.fuse(rule_result, llm_result)
            fused["raw_text_preview"] = text[:2000]

            # 5. 字段级置信度
            fused = compute_field_confidence(fused)

            # 6. 质量评估
            elapsed_ms = int((time.time() - start) * 1000)
            quality = self.quality_assessor.assess_v2(
                fused,
                raw_text=text,
                parser_engine="rule+llm_v2" if llm_result else "rule_v2",
            )
            quality["extraction_time_ms"] = elapsed_ms
            fused["extraction_quality"] = quality

            needs_review = bool(fused.get("needs_review")) or quality["confidence_score"] < 0.7
            fused["needs_review"] = needs_review

            # P0-10 监控埋点（★ P0-11 修复后）
            try:
                bucket = get_ab_router().assign_bucket(user_id or "anon", "resume_extraction_v1")
                field_count = sum(1 for v in (fused.get("personal_info") or {}).values() if v)
                field_count += len(fused.get("educations") or [])
                field_count += len(fused.get("work_experiences") or [])
                _emit_extraction_metric(
                    user_id=user_id or "anon",
                    bucket=bucket,
                    quality_score=quality.get("confidence_score", 0.0),
                    elapsed_ms=elapsed_ms,
                    degraded=False,
                    field_count=field_count,
                )
            except Exception as e:
                logger.warning(f"[P0-10] metric emission failed (non-fatal): {e}")

            return {
                "success": True,
                "data": fused,
                "quality": quality,
                "needs_review": needs_review,
                "extraction_time_ms": elapsed_ms,
                "schema_version": "v2",
            }

        except Exception as e:
            logger.warning(f"[v2] 文本提取失败, 降级到 v1 规则引擎: {e}", exc_info=True)
            # ★ P0-3: 异常降级到 v1 路径
            try:
                v1_result = await self.extract_from_text(text, user_id)
                if v1_result.get("success"):
                    return {
                        "success": True,
                        "data": v1_result["data"],
                        "v2_data": v1_result.get("v2_data", {}),
                        "quality": v1_result.get("quality", {}),
                        "needs_review": True,
                        "degraded": True,
                        "extraction_time_ms": int((time.time() - start) * 1000),
                        "schema_version": "v1_fallback",
                    }
            except Exception as fallback_err:
                logger.error(f"[v2] 降级到 v1 也失败: {fallback_err}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": ResumeDataV2.empty().to_dict(),
                "quality": self.quality_assessor.assess_v2({}),
                "needs_review": True,
                "degraded": True,
                "extraction_time_ms": int((time.time() - start) * 1000),
                "schema_version": "v2",
            }

    # ==================== 旧 v1 接口 (兼容) ====================
    async def extract_from_file(self, file_path: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        v1 兼容入口 - 内部走 v2 路径, 但同时返回 v1 格式
        """
        v2_result = await self.extract_from_file_v2(file_path, user_id)
        # 转换为 v1 格式 (兼容旧前端)
        if v2_result.get("success"):
            v1_data = self._v2_to_v1_compat(v2_result["data"])
            return {
                **v2_result,
                "data": v1_data,  # v1 形态
                "v2_data": v2_result["data"],  # v2 形态
            }
        return v2_result

    async def extract_from_text(self, text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """v1 兼容入口"""
        v2_result = await self.extract_from_text_v2(text, user_id)
        if v2_result.get("success"):
            v1_data = self._v2_to_v1_compat(v2_result["data"])
            return {
                **v2_result,
                "data": v1_data,
                "v2_data": v2_result["data"],
            }
        return v2_result

    # ==================== 工具方法 ====================
    def _merge_v1_into_v2(self, v2: Dict[str, Any], v1: Dict[str, Any]) -> Dict[str, Any]:
        """
        把规则引擎 v1 提取的基础段位 (education/work/projects/skills/languages/certifications/awards)
        合并进 v2 dict, 避免重复调用
        """
        if not v1:
            return v2
        v2.setdefault("personal_info", {})
        # personal_info 字段补全
        v1_pi = v1.get("personal_info")
        if v1_pi and hasattr(v1_pi, "__dict__"):
            for k, v in v1_pi.__dict__.items():
                if v and not v2["personal_info"].get(k):
                    v2["personal_info"][k] = v
        # 列表段位
        section_map = {
            "education": "educations",
            "work_experience": "work_experiences",
            "projects": "projects",
            "skills": "skills",
            "languages": "languages",
            "certifications": "certifications",
            "awards": "awards",
        }
        for v1_key, v2_key in section_map.items():
            existing = v2.get(v2_key) or []
            if existing:
                continue
            v1_items = v1.get(v1_key) or []
            converted = []
            for item in v1_items:
                if hasattr(item, "to_dict"):
                    converted.append(item.to_dict())
                elif isinstance(item, dict):
                    converted.append(item)
            if converted:
                v2[v2_key] = converted
        return v2

    def _v2_to_v1_compat(self, v2: Dict[str, Any]) -> Dict[str, Any]:
        """
        v2 dict → v1 兼容 dict — P0-1 修复版
        补全所有字段重命名：
        - personal_info.location_city → location
        - personal_info.intent_position → job_intent
        - educations[].field_of_study → field
        - educations[].start_date/end_date → YYYY-MM 规范化
        """
        # 1. personal_info 字段重命名
        v2_pi = v2.get("personal_info", {}) or {}
        v1_pi = {
            "name": v2_pi.get("name", ""),
            "email": v2_pi.get("email", ""),
            "phone": v2_pi.get("phone", ""),
            "linkedin": v2_pi.get("linkedin", "") or "",
            "website": v2_pi.get("website", "") or "",
            "gender": v2_pi.get("gender", "") or "",
            "age": v2_pi.get("age"),
            "location": v2_pi.get("location_city", "") or v2_pi.get("location", ""),  # ★ 关键
            "job_intent": v2_pi.get("intent_position", "") or v2_pi.get("job_intent", ""),  # ★ 关键
            "years_of_experience": v2_pi.get("years_of_experience"),
            "political_status": v2_pi.get("political_status", "") or "",
            "expected_salary_min": v2_pi.get("expected_salary_min"),
            "expected_salary_max": v2_pi.get("expected_salary_max"),
            "birth_date": v2_pi.get("birth_date", "") or "",
            "confidence": v2_pi.get("confidence", 0.0),
        }

        # 2. educations 字段重命名 + 日期规范化
        v1_educations = []
        for edu in (v2.get("educations", []) or []):
            v1_educations.append({
                "school": edu.get("school", "") or "",
                "degree": edu.get("degree", "") or "",
                "degree_type": edu.get("degree_type", "") or "",
                "field": edu.get("field_of_study", "") or edu.get("field", ""),  # ★ 关键
                "gpa": edu.get("gpa"),
                "gpa_scale": edu.get("gpa_scale", "") or "",
                "gpa_rank": edu.get("gpa_rank", "") or "",
                "honors": edu.get("honors", []) or [],
                "start_date": _normalize_date(edu.get("start_date", "") or ""),  # ★ 规范化
                "end_date": _normalize_date(edu.get("end_date", "") or ""),
                "description": edu.get("description", "") or "",
                "courses": edu.get("courses", []) or [],
            })

        # 3. work_experiences 字段重命名 + 日期规范化
        v1_work = []
        for work in (v2.get("work_experiences", []) or []):
            v1_work.append({
                "company": work.get("company", "") or "",
                "title": work.get("title", "") or "",
                "department": work.get("department", "") or "",
                "start_date": _normalize_date(work.get("start_date", "") or ""),
                "end_date": _normalize_date(work.get("end_date", "") or ""),
                "description": work.get("description", "") or "",
                "achievements": work.get("achievements", []) or [],
            })

        # 4. internships 字段重命名 + 日期规范化
        v1_internships = []
        for intern in (v2.get("internships", []) or []):
            v1_internships.append({
                "company": intern.get("company", "") or "",
                "title": intern.get("title", "") or "",
                "department": intern.get("department", "") or "",
                "start_date": _normalize_date(intern.get("start_date", "") or ""),
                "end_date": _normalize_date(intern.get("end_date", "") or ""),
                "description": intern.get("description", "") or "",
                "achievements": intern.get("achievements", []) or [],
            })

        # 5. projects (字段命名一致, 只需规范化日期)
        v1_projects = []
        for proj in (v2.get("projects", []) or []):
            v1_projects.append({
                "name": proj.get("name", "") or "",
                "role": proj.get("role", "") or "",
                "start_date": _normalize_date(proj.get("start_date", "") or ""),
                "end_date": _normalize_date(proj.get("end_date", "") or ""),
                "project_link": proj.get("project_link", "") or "",
                "description": proj.get("description", "") or "",
                "contributions": proj.get("contributions", []) or [],
                "tech_stack": proj.get("tech_stack", []) or [],
                "project_outcome": proj.get("project_outcome", "") or "",
            })

        return {
            "personal_info": v1_pi,
            "education": v1_educations,
            "work_experience": v1_work,
            "internships": v1_internships,
            "projects": v1_projects,
            "skills": v2.get("skills", []) or [],
            "certifications": v2.get("certifications", []) or [],
            "awards": v2.get("awards", []) or [],
            "languages": v2.get("languages", []) or [],
            "raw_text_preview": v2.get("raw_text_preview", "") or "",
            "extraction_quality": v2.get("extraction_quality"),
            "needs_review": v2.get("needs_review", False),
        }

    def validate_extraction(self, resume_data) -> Dict[str, Any]:
        """验证提取结果 (兼容 v1)"""
        issues: list = []
        warnings: list = []
        try:
            if hasattr(resume_data, "personal_info"):
                if not resume_data.personal_info.name:
                    issues.append("缺少姓名")
            if hasattr(resume_data, "education"):
                if not resume_data.education:
                    warnings.append("缺少教育经历")
        except Exception:
            pass
        return {"valid": len(issues) == 0, "issues": issues, "warnings": warnings}


# 单例模式
_resume_extraction_service = None


def get_resume_extraction_service() -> ResumeExtractionService:
    """获取简历提取服务单例"""
    global _resume_extraction_service
    if _resume_extraction_service is None:
        _resume_extraction_service = ResumeExtractionService()
    return _resume_extraction_service


# 便捷函数
async def extract_resume_file_v2(file_path: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    service = get_resume_extraction_service()
    return await service.extract_from_file_v2(file_path, user_id)


async def extract_resume_text_v2(text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    service = get_resume_extraction_service()
    return await service.extract_from_text_v2(text, user_id)


# 旧 v1 接口
async def extract_resume_file(file_path: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    service = get_resume_extraction_service()
    return await service.extract_from_file(file_path, user_id)


async def extract_resume_text(text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    service = get_resume_extraction_service()
    return await service.extract_from_text(text, user_id)
