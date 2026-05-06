import json
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import get_settings
from app.schemas.scoring import (
    DimensionWeights,
    DimensionScore,
    MatchResponse,
    MatchRequest,
)

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    """内部评分结果数据结构"""
    score: int
    matched: List[str]
    missing: List[str]
    analysis: str
    suggestions: List[str]


class ResumeScoringEngine:
    """
    简历-JD多维度契合度打分引擎

    从四个维度评估简历与职位描述的匹配度：
    - skills: 技能匹配度
    - experience: 工作经验匹配度
    - projects: 项目经历匹配度
    - education: 教育背景匹配度
    """

    # 默认评分维度权重
    DEFAULT_WEIGHTS = DimensionWeights(
        skills=0.35,
        experience=0.35,
        projects=0.20,
        education=0.10
    )

    # 文本长度限制
    MAX_RESUME_LENGTH = 8000
    MAX_JD_LENGTH = 4000

    def __init__(self, db: Session = None):
        self.db = db
        self._llm_client = None

    def _get_llm_client(self, llm_config: Optional[Dict[str, Any]] = None):
        """获取 LLM 客户端"""
        if self._llm_client:
            return self._llm_client

        if not llm_config:
            # 使用系统默认配置
            api_key = settings.OPENAI_API_KEY
            model = settings.LLM_MODEL
            if not api_key:
                return None
            llm_config = {
                "api_key": api_key,
                "model": model,
            }

        api_key = llm_config.get("api_key")
        model = llm_config.get("model", "gpt-4o")

        if not api_key:
            return None

        try:
            from langchain_openai import ChatOpenAI

            client = ChatOpenAI(
                model=model,
                api_key=api_key,
                temperature=0.3,  # 评分任务需要更确定性的输出
                max_tokens=2000,
            )
            self._llm_client = client
            return client
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            return None

    def _truncate_text(self, text: str, max_length: int) -> str:
        """截断文本至指定长度"""
        if len(text) <= max_length:
            return text

        # 尝试在句子边界截断
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        last_cn_period = truncated.rfind('。')

        cut_point = max(last_period, last_newline, last_cn_period)
        if cut_point > max_length * 0.8:
            return truncated[:cut_point + 1]

        return truncated

    def _build_scoring_prompt(
        self,
        dimension: str,
        resume_text: str,
        jd_text: str
    ) -> str:
        """构建评分维度的提示词"""

        dimension_prompts = {
            "skills": {
                "name": "技能匹配度",
                "focus": "技术栈、编程语言、框架、工具、软硬技能",
                "examples": "Python, JavaScript, React, Kubernetes, 项目管理, 数据分析"
            },
            "experience": {
                "name": "工作经验匹配度",
                "focus": "工作年限、行业经验、职位级别、管理/独立贡献经验",
                "examples": "5年开发经验, 金融行业背景, 团队管理经验, 全栈开发"
            },
            "projects": {
                "name": "项目经历匹配度",
                "focus": "项目类型、技术复杂度、业务领域、成果量化",
                "examples": "微服务架构项目, 高并发系统, 数据平台建设, 性能优化项目"
            },
            "education": {
                "name": "教育背景匹配度",
                "focus": "学历层次、专业相关性、知名院校、持续学习",
                "examples": "计算机科学本科, 硕士学历, 知名院校, 相关证书"
            }
        }

        dim_info = dimension_prompts.get(dimension, dimension_prompts["skills"])

        prompt = f"""你是一位资深的HR和招聘专家。请从【{dim_info['name']}】维度，评估候选人简历与岗位JD的匹配度。

## 评估维度说明
- 评估重点：{dim_info['focus']}
- 参考示例：{dim_info['examples']}

## 岗位JD
{jd_text}

## 候选人简历
{resume_text}

## 评估要求
1. 仔细阅读JD中对该维度的具体要求
2. 分析候选人简历中相关的经历和能力
3. 对比匹配程度，给出客观评分

## 输出格式（严格JSON）
{{
  "score": 0-100的整数分数,
  "matched": ["匹配的具体项目1", "匹配的具体项目2"],
  "missing": ["缺失的具体项目1", "缺失的具体项目2"],
  "analysis": "对该维度的简要分析（50字以内）",
  "suggestions": ["改进建议1", "改进建议2"]
}}

评分标准：
- 90-100: 完全匹配，超出期望
- 75-89: 良好匹配，基本符合
- 60-74: 部分匹配，有差距但可接受
- 40-59: 匹配度较低，差距明显
- 0-39: 基本不匹配

请只返回JSON，不要添加任何其他文本。"""

        return prompt

    def _call_llm_with_retry(
        self,
        prompt: str,
        llm_config: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """调用LLM并带有重试机制"""
        client = self._get_llm_client(llm_config)

        if not client:
            logger.warning("No LLM client available")
            return None

        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content="你是一个专业的简历评估专家，只输出严格的JSON格式数据。"),
            HumanMessage(content=prompt)
        ]

        for attempt in range(max_retries):
            try:
                response = client.invoke(messages)
                content = response.content.strip()

                # 清理可能的 markdown 代码块
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                result = json.loads(content)

                # 验证必要字段
                required_fields = ["score", "matched", "missing", "analysis", "suggestions"]
                if all(field in result for field in required_fields):
                    return result
                else:
                    missing_fields = [f for f in required_fields if f not in result]
                    logger.warning(f"LLM response missing fields: {missing_fields}")

            except json.JSONDecodeError as e:
                logger.warning(f"Attempt {attempt + 1}: JSON parse error: {e}")
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}: LLM call failed: {e}")

        logger.error(f"Failed to get valid LLM response after {max_retries} attempts")
        return None

    def _score_dimension(
        self,
        dimension: str,
        resume_text: str,
        jd_text: str,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> ScoreResult:
        """对单一维度进行评分"""
        prompt = self._build_scoring_prompt(dimension, resume_text, jd_text)
        result = self._call_llm_with_retry(prompt, llm_config)

        if result:
            return ScoreResult(
                score=result.get("score", 50),
                matched=result.get("matched", []),
                missing=result.get("missing", []),
                analysis=result.get("analysis", "分析暂不可用"),
                suggestions=result.get("suggestions", [])
            )

        # LLM 失败时返回默认结果
        return self._fallback_dimension_score(dimension)

    def _fallback_dimension_score(self, dimension: str) -> ScoreResult:
        """LLM失败时的默认评分"""
        default_scores = {
            "skills": ScoreResult(
                score=50,
                matched=[],
                missing=["无法确定具体匹配项（LLM服务暂不可用）"],
                analysis="由于LLM服务暂不可用，无法完成详细分析",
                suggestions=["请稍后重试", "检查LLM配置是否正确"]
            ),
            "experience": ScoreResult(
                score=50,
                matched=[],
                missing=["无法确定具体匹配项（LLM服务暂不可用）"],
                analysis="由于LLM服务暂不可用，无法完成详细分析",
                suggestions=["请稍后重试", "检查LLM配置是否正确"]
            ),
            "projects": ScoreResult(
                score=50,
                matched=[],
                missing=["无法确定具体匹配项（LLM服务暂不可用）"],
                analysis="由于LLM服务暂不可用，无法完成详细分析",
                suggestions=["请稍后重试", "检查LLM配置是否正确"]
            ),
            "education": ScoreResult(
                score=50,
                matched=[],
                missing=["无法确定具体匹配项（LLM服务暂不可用）"],
                analysis="由于LLM服务暂不可用，无法完成详细分析",
                suggestions=["请稍后重试", "检查LLM配置是否正确"]
            ),
        }
        return default_scores.get(dimension, default_scores["skills"])

    def _generate_summary(
        self,
        dimensions: Dict[str, DimensionScore],
        overall_score: int
    ) -> str:
        """生成总体评价摘要"""
        if overall_score >= 85:
            level = "非常匹配"
            description = "候选人背景与岗位要求高度契合"
        elif overall_score >= 70:
            level = "良好匹配"
            description = "候选人基本符合岗位要求，部分维度可以进一步优化"
        elif overall_score >= 55:
            level = "部分匹配"
            description = "候选人与岗位存在一定差距，需要针对性提升"
        else:
            level = "匹配度较低"
            description = "候选人背景与岗位要求差距较大"

        strong_dims = [k for k, v in dimensions.items() if v.score >= 75]
        weak_dims = [k for k, v in dimensions.items() if v.score < 60]

        dim_names = {
            "skills": "技能",
            "experience": "经验",
            "projects": "项目",
            "education": "教育"
        }

        parts = [f"{description}（综合评分：{overall_score}/100，{level}）"]

        if strong_dims:
            strong_names = [dim_names.get(d, d) for d in strong_dims]
            parts.append(f"优势维度：{', '.join(strong_names)}")

        if weak_dims:
            weak_names = [dim_names.get(d, d) for d in weak_dims]
            parts.append(f"待提升维度：{', '.join(weak_names)}")

        return "；".join(parts)

    def _extract_top_strengths(self, dimensions: Dict[str, DimensionScore]) -> List[str]:
        """提取核心优势"""
        strengths = []

        for dim_name, dim_score in dimensions.items():
            if dim_score.score >= 70 and dim_score.matched:
                for item in dim_score.matched[:2]:
                    if item not in strengths:
                        strengths.append(item)

        return strengths[:5]

    def _extract_key_gaps(self, dimensions: Dict[str, DimensionScore]) -> List[str]:
        """提取关键差距"""
        gaps = []

        for dim_name, dim_score in dimensions.items():
            if dim_score.score < 70 and dim_score.missing:
                for item in dim_score.missing[:2]:
                    if item not in gaps:
                        gaps.append(item)

        return gaps[:5]

    def _generate_action_items(
        self,
        dimensions: Dict[str, DimensionScore]
    ) -> List[str]:
        """生成行动建议"""
        actions = []

        # 收集所有维度的建议
        for dim_name, dim_score in dimensions.items():
            for suggestion in dim_score.suggestions:
                if suggestion and suggestion not in actions:
                    actions.append(suggestion)

        return actions[:6]

    def calculate_match(
        self,
        request: MatchRequest
    ) -> MatchResponse:
        """
        执行简历-JD多维度匹配评分

        Args:
            request: 包含简历文本、JD文本和可选权重的请求对象

        Returns:
            MatchResponse: 包含各维度评分和综合分析的响应
        """
        logger.info("Starting multi-dimensional resume-JD match scoring")

        # 使用自定义权重或默认权重
        weights = request.weights or self.DEFAULT_WEIGHTS

        # 文本截断
        resume_text = self._truncate_text(
            request.resume_text,
            self.MAX_RESUME_LENGTH
        )
        jd_text = self._truncate_text(
            request.jd_text,
            self.MAX_JD_LENGTH
        )

        # 四个维度评分
        dimensions_to_score = ["skills", "experience", "projects", "education"]
        dimension_results: Dict[str, ScoreResult] = {}

        for dim in dimensions_to_score:
            logger.info(f"Scoring dimension: {dim}")
            result = self._score_dimension(
                dim,
                resume_text,
                jd_text,
                request.llm_config
            )
            dimension_results[dim] = result

        # 构建 DimensionScore 对象
        dimensions: Dict[str, DimensionScore] = {}
        for dim, result in dimension_results.items():
            dimensions[dim] = DimensionScore(
                score=result.score,
                matched=result.matched,
                missing=result.missing,
                analysis=result.analysis,
                suggestions=result.suggestions
            )

        # 计算加权综合得分
        overall_score = int(
            dimensions["skills"].score * weights.skills +
            dimensions["experience"].score * weights.experience +
            dimensions["projects"].score * weights.projects +
            dimensions["education"].score * weights.education
        )

        # 确保分数在有效范围内
        overall_score = max(0, min(100, overall_score))

        # 生成分析内容
        summary = self._generate_summary(dimensions, overall_score)
        top_strengths = self._extract_top_strengths(dimensions)
        key_gaps = self._extract_key_gaps(dimensions)
        action_items = self._generate_action_items(dimensions)

        logger.info(f"Match scoring complete. Overall score: {overall_score}")

        return MatchResponse(
            overall_score=overall_score,
            dimensions=dimensions,
            weights_used=weights,
            summary=summary,
            top_strengths=top_strengths,
            key_gaps=key_gaps,
            action_items=action_items
        )

    def calculate_text_hash(self, text: str) -> str:
        """计算文本哈希值（用于缓存）"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
