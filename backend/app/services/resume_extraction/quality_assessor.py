"""
质量评估器
评估简历信息提取的质量，计算置信度和完整度
"""

import logging
from typing import List, Dict, Any

from .models import (
    ResumeData, QualityReport, PersonalInfo, EducationEntry,
    WorkEntry, ProjectEntry, SkillEntry
)
from .config import quality_config

logger = logging.getLogger(__name__)


class QualityAssessor:
    """提取质量评估器"""
    
    def __init__(self):
        self.config = quality_config
    
    def assess(self, resume_data: ResumeData, raw_text: str) -> QualityReport:
        """
        评估提取质量
        
        Args:
            resume_data: 提取的简历数据
            raw_text: 原始文本
            
        Returns:
            QualityReport: 质量评估报告
        """
        logger.info("开始质量评估...")
        
        # 计算各维度分数
        accuracy_score = self._calculate_accuracy(resume_data)
        completeness_score = self._calculate_completeness(resume_data)
        confidence_score = self._calculate_confidence(resume_data)
        
        # 计算整体分数
        overall_score = (
            accuracy_score * self.config.accuracy_weight +
            completeness_score * self.config.completeness_weight +
            confidence_score * self.config.confidence_weight
        )
        
        # 计算各字段分数
        field_scores = self._calculate_field_scores(resume_data)
        
        # 发现问题
        issues = self._detect_issues(resume_data)
        
        # 生成建议
        suggestions = self._generate_suggestions(resume_data, issues)
        
        # 识别低置信度字段
        low_confidence_fields = self._identify_low_confidence_fields(resume_data)
        
        report = QualityReport(
            overall_score=round(overall_score, 2),
            accuracy_score=round(accuracy_score, 2),
            completeness_score=round(completeness_score, 2),
            field_scores=field_scores,
            issues=issues,
            suggestions=suggestions,
            low_confidence_fields=low_confidence_fields
        )
        
        logger.info(f"质量评估完成: 整体分数={overall_score:.2f}, 准确度={accuracy_score:.2f}, 完整度={completeness_score:.2f}")
        return report
    
    def _calculate_accuracy(self, resume_data: ResumeData) -> float:
        """计算准确度"""
        scores = []
        
        # 个人信息准确度
        if resume_data.personal_info.name:
            scores.append(resume_data.personal_info.confidence)
        
        # 教育经历准确度
        for edu in resume_data.education:
            if edu.school:
                scores.append(edu.confidence)
        
        # 工作经历准确度
        for work in resume_data.work_experience:
            if work.company:
                scores.append(work.confidence)
        
        # 项目经历准确度
        for proj in resume_data.projects:
            if proj.name:
                scores.append(proj.confidence)
        
        # 技能准确度
        for skill in resume_data.skills:
            scores.append(skill.confidence)
        
        if not scores:
            return 0.0
        
        return sum(scores) / len(scores)
    
    def _calculate_completeness(self, resume_data: ResumeData) -> float:
        """计算完整度"""
        total_weight = 0
        filled_weight = 0
        
        # 定义各字段的权重
        field_weights = {
            "personal_info": 0.2,
            "education": 0.25,
            "work_experience": 0.25,
            "skills": 0.2,
            "projects": 0.1,
        }
        
        # 个人信息完整度
        personal_fields = ["name", "email", "phone"]
        personal_filled = sum(1 for f in personal_fields if getattr(resume_data.personal_info, f))
        personal_completeness = personal_filled / len(personal_fields)
        filled_weight += personal_completeness * field_weights["personal_info"]
        total_weight += field_weights["personal_info"]
        
        # 教育经历完整度
        if resume_data.education:
            edu_completeness = min(len(resume_data.education) / 2, 1.0)  # 期望至少2条
            filled_weight += edu_completeness * field_weights["education"]
        total_weight += field_weights["education"]
        
        # 工作经历完整度
        if resume_data.work_experience:
            work_completeness = min(len(resume_data.work_experience) / 2, 1.0)
            filled_weight += work_completeness * field_weights["work_experience"]
        total_weight += field_weights["work_experience"]
        
        # 技能完整度
        if resume_data.skills:
            skill_completeness = min(len(resume_data.skills) / 5, 1.0)  # 期望至少5个技能
            filled_weight += skill_completeness * field_weights["skills"]
        total_weight += field_weights["skills"]
        
        # 项目经历完整度
        if resume_data.projects:
            proj_completeness = min(len(resume_data.projects) / 2, 1.0)
            filled_weight += proj_completeness * field_weights["projects"]
        total_weight += field_weights["projects"]
        
        if total_weight == 0:
            return 0.0
        
        return filled_weight / total_weight
    
    def _calculate_confidence(self, resume_data: ResumeData) -> float:
        """计算整体置信度"""
        confidences = []
        
        if resume_data.personal_info.confidence > 0:
            confidences.append(resume_data.personal_info.confidence)
        
        for edu in resume_data.education:
            confidences.append(edu.confidence)
        
        for work in resume_data.work_experience:
            confidences.append(work.confidence)
        
        for proj in resume_data.projects:
            confidences.append(proj.confidence)
        
        for skill in resume_data.skills:
            confidences.append(skill.confidence)
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)
    
    def _calculate_field_scores(self, resume_data: ResumeData) -> Dict[str, float]:
        """计算各字段分数"""
        scores = {}
        
        # 个人信息
        if resume_data.personal_info.name:
            scores["personal_info"] = resume_data.personal_info.confidence
        
        # 教育经历
        if resume_data.education:
            edu_scores = [e.confidence for e in resume_data.education if e.school]
            scores["education"] = sum(edu_scores) / len(edu_scores) if edu_scores else 0.0
        
        # 工作经历
        if resume_data.work_experience:
            work_scores = [w.confidence for w in resume_data.work_experience if w.company]
            scores["work_experience"] = sum(work_scores) / len(work_scores) if work_scores else 0.0
        
        # 项目经历
        if resume_data.projects:
            proj_scores = [p.confidence for p in resume_data.projects if p.name]
            scores["projects"] = sum(proj_scores) / len(proj_scores) if proj_scores else 0.0
        
        # 技能
        if resume_data.skills:
            skill_scores = [s.confidence for s in resume_data.skills]
            scores["skills"] = sum(skill_scores) / len(skill_scores) if skill_scores else 0.0
        
        return scores
    
    def _detect_issues(self, resume_data: ResumeData) -> List[str]:
        """检测问题"""
        issues = []
        
        # 检查关键字段缺失
        if not resume_data.personal_info.name:
            issues.append("未识别到姓名")
        
        if not resume_data.education:
            issues.append("未识别到教育经历")
        
        if not resume_data.work_experience and not resume_data.projects:
            issues.append("未识别到工作经历或项目经历")
        
        if len(resume_data.skills) < 3:
            issues.append("识别的技能数量较少")
        
        # 检查低置信度
        low_confidence_fields = []
        
        if resume_data.personal_info.confidence < self.config.low_confidence_threshold:
            low_confidence_fields.append("个人信息")
        
        for edu in resume_data.education:
            if edu.confidence < self.config.low_confidence_threshold:
                low_confidence_fields.append(f"教育经历: {edu.school}")
        
        for work in resume_data.work_experience:
            if work.confidence < self.config.low_confidence_threshold:
                low_confidence_fields.append(f"工作经历: {work.company}")
        
        if low_confidence_fields:
            issues.append(f"以下字段置信度较低: {', '.join(low_confidence_fields[:3])}")
        
        return issues
    
    def _generate_suggestions(self, resume_data: ResumeData, issues: List[str]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if "未识别到姓名" in issues:
            suggestions.append("建议手动输入姓名")
        
        if "未识别到教育经历" in issues:
            suggestions.append("建议检查PDF格式或手动添加教育经历")
        
        if "未识别到工作经历或项目经历" in issues:
            suggestions.append("建议检查PDF格式或手动添加工作经历")
        
        if "识别的技能数量较少" in issues:
            suggestions.append("建议补充更多技能信息")
        
        # 根据完整度给出建议
        completeness = self._calculate_completeness(resume_data)
        if completeness < 0.5:
            suggestions.append("整体完整度较低，建议重新上传更清晰的简历")
        elif completeness < 0.8:
            suggestions.append("部分信息缺失，建议检查并补充")
        
        return suggestions
    
    def _identify_low_confidence_fields(self, resume_data: ResumeData) -> List[str]:
        """识别低置信度字段"""
        low_confidence_fields = []
        
        if resume_data.personal_info.confidence < self.config.low_confidence_threshold:
            low_confidence_fields.append("personal_info")
        
        for i, edu in enumerate(resume_data.education):
            if edu.confidence < self.config.low_confidence_threshold:
                low_confidence_fields.append(f"education[{i}]")
        
        for i, work in enumerate(resume_data.work_experience):
            if work.confidence < self.config.low_confidence_threshold:
                low_confidence_fields.append(f"work_experience[{i}]")
        
        for i, proj in enumerate(resume_data.projects):
            if proj.confidence < self.config.low_confidence_threshold:
                low_confidence_fields.append(f"projects[{i}]")
        
        return low_confidence_fields


# 单例模式
_quality_assessor = None


def get_quality_assessor() -> QualityAssessor:
    """获取质量评估器单例"""
    global _quality_assessor
    if _quality_assessor is None:
        _quality_assessor = QualityAssessor()
    return _quality_assessor
