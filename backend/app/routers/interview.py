from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas.user import UserResponse
from app.schemas.interview import InterviewQuestionResponse, InterviewQuestionUpdate
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/api/interview", tags=["面试准备"])


@router.get("/jobs/{job_id}/interview-prep", response_model=List[InterviewQuestionResponse])
def get_interview_questions(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取面试题（如果不存在则自动生成）"""
    interview_service = InterviewService(db)
    questions = interview_service.get_or_generate_questions(
        job_id=job_id,
        user_id=current_user.id
    )
    return questions


@router.post("/jobs/{job_id}/interview-prep/regenerate", response_model=List[InterviewQuestionResponse])
def regenerate_interview_questions(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """重新生成面试题"""
    interview_service = InterviewService(db)
    questions = interview_service.regenerate_questions(
        job_id=job_id,
        user_id=current_user.id
    )
    return questions


@router.put("/questions/{question_id}", response_model=InterviewQuestionResponse)
def update_interview_question(
    question_id: str,
    question_data: InterviewQuestionUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """更新面试题（用户笔记）"""
    interview_service = InterviewService(db)

    # 获取面试题
    question = interview_service.get_question_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview question not found"
        )

    # 验证该面试题属于当前用户
    if question.job_application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this question"
        )

    updated_question = interview_service.update_question(question, question_data)
    return updated_question
