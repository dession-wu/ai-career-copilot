from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.job_application import JobApplication
from app.schemas.job import JobApplicationCreate, JobApplicationUpdate


class JobService:
    def __init__(self, db: Session):
        self.db = db

    def get_job_by_id(self, job_id: str) -> Optional[JobApplication]:
        """通过 ID 获取求职投递"""
        return self.db.query(JobApplication).filter(JobApplication.id == job_id).first()

    def list_jobs_by_user_id(self, user_id: str) -> List[JobApplication]:
        """获取用户的所有求职投递"""
        return self.db.query(JobApplication).filter(JobApplication.user_id == user_id).all()

    def create_job(self, user_id: str, job_data: JobApplicationCreate) -> JobApplication:
        """创建求职投递"""
        db_job = JobApplication(
            user_id=user_id,
            company_name=job_data.company_name,
            job_title=job_data.job_title,
            jd_text=job_data.jd_text,
            status="preparing"
        )
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)
        return db_job

    def update_job(self, job: JobApplication, job_data: JobApplicationUpdate) -> JobApplication:
        """更新求职投递"""
        update_data = job_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete_job(self, job: JobApplication) -> None:
        """删除求职投递"""
        self.db.delete(job)
        self.db.commit()

    def update_match_analysis(self, job: JobApplication, match_score: int, match_analysis: dict) -> JobApplication:
        """更新匹配分析结果"""
        job.match_score = match_score
        job.match_analysis = match_analysis
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_tailored_resume(self, job: JobApplication, resume_md: str) -> JobApplication:
        """更新定制简历"""
        job.tailored_resume_md = resume_md
        self.db.commit()
        self.db.refresh(job)
        return job
