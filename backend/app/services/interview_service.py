import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.interview_question import InterviewQuestion
from app.models.job_application import JobApplication
from app.models.career_vault import CareerVault
from app.schemas.interview import InterviewQuestionCreate, InterviewQuestionUpdate
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class InterviewService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService(db)

    def get_questions_by_job(self, job_id: str) -> List[InterviewQuestion]:
        """获取指定岗位的所有面试题"""
        return self.db.query(InterviewQuestion).filter(
            InterviewQuestion.application_id == job_id
        ).order_by(InterviewQuestion.created_at).all()

    def get_question_by_id(self, question_id: str) -> Optional[InterviewQuestion]:
        """通过 ID 获取面试题"""
        return self.db.query(InterviewQuestion).filter(
            InterviewQuestion.id == question_id
        ).first()

    def get_or_generate_questions(
        self,
        job_id: str,
        user_id: str,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> List[InterviewQuestion]:
        """
        获取或生成面试题
        如果已存在则返回现有题目，否则生成新题目
        """
        # 先检查是否已有面试题
        existing_questions = self.get_questions_by_job(job_id)
        if existing_questions:
            logger.info(f"Found {len(existing_questions)} existing questions for job {job_id}")
            return existing_questions

        # 没有则生成新的
        return self.regenerate_questions(job_id, user_id, llm_config)

    def regenerate_questions(
        self,
        job_id: str,
        user_id: str,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> List[InterviewQuestion]:
        """
        重新生成面试题
        删除旧的，生成新的
        """
        # 获取岗位信息
        job = self.db.query(JobApplication).filter(
            JobApplication.id == job_id,
            JobApplication.user_id == user_id
        ).first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job application not found"
            )

        # 获取用户的 Vault
        vault = self.db.query(CareerVault).filter(
            CareerVault.user_id == user_id
        ).first()

        if not vault:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Career Vault not found. Please upload your resume first."
            )

        # 删除旧的面试题
        old_questions = self.get_questions_by_job(job_id)
        for question in old_questions:
            self.db.delete(question)
        logger.info(f"Deleted {len(old_questions)} old questions for job {job_id}")

        # 准备简历内容
        resume_md = self._prepare_resume_content(vault)

        # 生成新的面试题
        try:
            import asyncio
            # 调用异步方法生成面试题
            generated_questions = asyncio.run(self.llm_service.generate_interview_questions(
                jd_text=job.jd_text,
                resume_md=resume_md,
                llm_config=llm_config
            ))
        except Exception as e:
            logger.error(f"Failed to generate interview questions: {e}")
            # 如果生成失败，使用基础模式的问题
            generated_questions = self.llm_service._generate_fallback_questions(job.jd_text)

        # 保存到数据库
        questions = []
        for q_data in generated_questions:
            question = InterviewQuestion(
                application_id=job_id,
                question_text=q_data.get("question_text", ""),
                question_type=q_data.get("question_type", "technical"),
                intent_analysis=q_data.get("intent_analysis", ""),
                suggested_answer_star=q_data.get("suggested_answer_star", ""),
                difficulty=q_data.get("difficulty", 3)
            )
            self.db.add(question)
            questions.append(question)

        self.db.commit()
        for q in questions:
            self.db.refresh(q)

        logger.info(f"Generated and saved {len(questions)} new questions for job {job_id}")
        return questions

    def _prepare_resume_content(self, vault: CareerVault) -> str:
        """准备简历内容用于生成面试题"""
        if vault.structured_data:
            # 使用结构化数据生成 Markdown
            data = vault.structured_data
            md_parts = []

            # 个人信息
            personal = data.get("personal_info", {})
            if personal:
                md_parts.append("## 个人信息")
                if personal.get("name"):
                    md_parts.append(f"姓名: {personal['name']}")
                if personal.get("email"):
                    md_parts.append(f"邮箱: {personal['email']}")

            # 教育经历
            education = data.get("education", [])
            if education:
                md_parts.append("\n## 教育背景")
                for edu in education:
                    md_parts.append(f"- {edu.get('school', '')} - {edu.get('degree', '')} ({edu.get('field', '')})")

            # 工作经历
            experiences = data.get("experiences", [])
            if experiences:
                md_parts.append("\n## 工作经历")
                for exp in experiences:
                    md_parts.append(f"\n### {exp.get('company', '')} - {exp.get('title', '')}")
                    if exp.get("projects"):
                        for proj in exp["projects"]:
                            md_parts.append(f"- 项目: {proj.get('name', '')}")
                            md_parts.append(f"  描述: {proj.get('description', '')}")

            # 技能
            skills = data.get("skills", [])
            if skills:
                md_parts.append("\n## 技能")
                skill_names = [s.get("name", "") for s in skills]
                md_parts.append(", ".join(skill_names))

            return "\n".join(md_parts)

        # 如果没有结构化数据，使用原始文本
        return vault.raw_content or ""

    def update_question(
        self,
        question: InterviewQuestion,
        update_data: InterviewQuestionUpdate
    ) -> InterviewQuestion:
        """更新面试题（支持用户添加笔记）"""
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(question, field, value)

        self.db.commit()
        self.db.refresh(question)
        logger.info(f"Updated question {question.id}")
        return question

    def delete_question(self, question: InterviewQuestion) -> None:
        """删除面试题"""
        self.db.delete(question)
        self.db.commit()
        logger.info(f"Deleted question {question.id}")

    def delete_questions_by_job(self, job_id: str) -> int:
        """删除指定岗位的所有面试题"""
        questions = self.get_questions_by_job(job_id)
        count = len(questions)
        for q in questions:
            self.db.delete(q)
        self.db.commit()
        logger.info(f"Deleted {count} questions for job {job_id}")
        return count
