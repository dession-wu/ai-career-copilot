from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, AsyncGenerator
import logging
import os
import tempfile
import shutil
import json
import asyncio

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas.user import UserResponse
from app.schemas.job import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
    MatchAnalysisResponse,
    WeightedMatchAnalysisResponse,
    TailoredResumeResponse,
    ResumeVersionCreate,
    WorkflowDetailsResponse,
    WorkflowStepDetail,
    JDRequirementItem,
    ExperienceEvidenceItem,
    ProvenanceMapResponse,
    ProvenanceItem,
)
from app.services.job_service import JobService
from app.services.llm_service import LLMService
from app.services.vault_service import VaultService
from app.services.pdf_service import get_pdf_service
from app.services.job_extraction import JobExtractionService, JobExtractionRequest

router = APIRouter(prefix="/api/jobs", tags=["求职投递"])
logger = logging.getLogger(__name__)


@router.post("", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_data: JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """创建新的求职投递"""
    job_service = JobService(db)
    job = job_service.create_job(current_user.id, job_data)
    return job


@router.get("", response_model=List[JobApplicationResponse])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取用户的所有求职投递列表"""
    job_service = JobService(db)
    jobs = job_service.list_jobs_by_user_id(current_user.id)
    return jobs


@router.get("/{job_id}", response_model=JobApplicationResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取单个求职投递详情"""
    job_service = JobService(db)
    job = job_service.get_job_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    return job


@router.put("/{job_id}", response_model=JobApplicationResponse)
def update_job(
    job_id: str,
    job_data: JobApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """更新求职投递信息"""
    job_service = JobService(db)
    job = job_service.get_job_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此求职投递"
        )

    updated_job = job_service.update_job(job, job_data)
    return updated_job


@router.put("/{job_id}/status", response_model=JobApplicationResponse)
def update_job_status(
    job_id: str,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """更新求职投递状态"""
    job_service = JobService(db)
    job = job_service.get_job_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此求职投递"
        )

    new_status = status_update.get("status")
    if new_status not in ["preparing", "applied", "interviewing", "offered", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的状态值"
        )

    job.status = new_status
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """删除求职投递"""
    job_service = JobService(db)
    job = job_service.get_job_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此求职投递"
        )

    # 记录敏感操作日志
    client_ip = request.client.host
    logger.warning(f"SECURITY: User {current_user.id} deleted job {job_id} ({job.company_name} - {job.job_title}) from IP {client_ip}")

    job_service.delete_job(job)
    return None


@router.post("/{job_id}/analyze", response_model=MatchAnalysisResponse)
def analyze_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """分析 JD 与 Vault 的匹配度（传统方式）"""
    job_service = JobService(db)
    vault_service = VaultService(db)

    job = job_service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    vault = vault_service.get_vault_by_user_id(current_user.id)
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传简历到 Career Vault"
        )

    # 使用 LLMService 进行基础匹配分析
    llm_service = LLMService(db)
    analysis = llm_service.analyze_match(vault.structured_data, job.jd_text)

    # 保存分析结果
    job_service.update_match_analysis(job, analysis["overall_score"], analysis)

    return analysis


@router.post("/{job_id}/analyze-weighted", response_model=WeightedMatchAnalysisResponse)
def analyze_job_weighted(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    分析 JD 与 Vault 的匹配度（加权算法）

    返回包含：
    - overall_score: 总体匹配分数 (0-100)
    - confidence: 匹配置信度 (0-1)
    - dimension_scores: 各维度得分（core_tech, framework, tool, soft_skill）
    - skill_match: 技能匹配详情（matched, missing, extra）
    - details: 详细匹配信息
    - processing_time_ms: 处理时间
    """
    import json
    import time

    job_service = JobService(db)
    vault_service = VaultService(db)

    job = job_service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    vault = vault_service.get_vault_by_user_id(current_user.id)
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传简历到 Career Vault"
        )

    # 使用新的加权匹配算法
    llm_service = LLMService(db)

    # 准备简历文本
    resume_text = json.dumps(vault.structured_data, ensure_ascii=False)

    # 执行加权匹配分析
    result = llm_service.calculate_weighted_score(job.jd_text, resume_text)

    # 生成优化建议
    suggestions = llm_service._generate_suggestions(
        result.skill_match["matched"],
        result.skill_match["missing"]
    )

    # 构建响应
    response_data = {
        "overall_score": result.overall_score,
        "confidence": result.confidence,
        "dimension_scores": [
            {
                "dimension": dim.dimension,
                "score": dim.score,
                "weight": dim.weight,
                "max_score": dim.max_score,
                "details": dim.details
            }
            for dim in result.dimension_scores
        ],
        "skill_match": result.skill_match,
        "details": result.details,
        "processing_time_ms": result.processing_time_ms,
        "suggestions": suggestions
    }

    # 保存分析结果（包含置信度）
    analysis_to_save = {
        "overall_score": result.overall_score,
        "confidence": result.confidence,
        "dimension_scores": response_data["dimension_scores"],
        "skill_match": result.skill_match,
        "processing_time_ms": result.processing_time_ms
    }
    job_service.update_match_analysis(job, result.overall_score, analysis_to_save)

    logger.info(f"Weighted match analysis completed for job {job_id}: "
                f"score={result.overall_score}, confidence={result.confidence}, "
                f"time={result.processing_time_ms}ms")

    # 检查响应时间
    if result.processing_time_ms > 2000:
        logger.warning(f"Weighted match analysis took {result.processing_time_ms}ms, exceeding 2s threshold")

    return WeightedMatchAnalysisResponse(**response_data)


@router.post("/{job_id}/tailor", response_model=TailoredResumeResponse)
def tailor_resume(
    job_id: str,
    llm_config: dict = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    生成定制简历（带防幻觉校验）
    
    返回包含：
    - content: 生成的简历内容
    - verification: 防幻觉校验结果
    - mapping: 技能映射关系
    - mode: 生成模式
    """
    from datetime import datetime

    job_service = JobService(db)
    vault_service = VaultService(db)
    llm_service = LLMService(db)

    job = job_service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    vault = vault_service.get_vault_by_user_id(current_user.id)
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传简历到 Career Vault"
        )

    # 调用 LLM 服务生成定制简历（带防幻觉校验）
    result = llm_service.tailor_resume(
        vault.structured_data,
        job.jd_text,
        llm_config
    )

    # 提取简历内容
    tailored_content = result["resume"]
    
    # 保存定制简历
    job_service.update_tailored_resume(job, tailored_content)

    # 构建响应（包含校验信息）
    return TailoredResumeResponse(
        content=tailored_content,
        version=job.version if hasattr(job, 'version') else 1,
        created_at=datetime.utcnow(),
        verification=result.get("verification"),
        mapping=result.get("mapping"),
        mode=result.get("mode", "unknown")
    )


@router.post("/{job_id}/tailor/stream")
async def tailor_resume_stream(
    job_id: str,
    llm_config: dict = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    生成定制简历（SSE 流式传输）
    
    使用 Server-Sent Events 流式返回 AI 生成的简历内容，实现打字机效果。
    
    事件格式：
    - data: {"type": "chunk", "content": "..."}  # 内容块
    - data: {"type": "mapping", "data": {...}}   # 技能映射数据
    - data: {"type": "verification", "data": {...}}  # 校验结果
    - data: {"type": "done"}  # 完成标记
    - data: {"type": "error", "message": "..."}  # 错误信息
    """
    from datetime import datetime

    job_service = JobService(db)
    vault_service = VaultService(db)
    llm_service = LLMService(db)

    job = job_service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    vault = vault_service.get_vault_by_user_id(current_user.id)
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传简历到 Career Vault"
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        """SSE 事件生成器"""
        try:
            # 检查是否有 LLM 配置
            llm_client = llm_service._get_llm_client(llm_config)
            
            if not llm_client:
                # 基础模式：一次性返回
                logger.info("Using fallback mode (no LLM)")
                resume = llm_service._tailor_resume_fallback(vault.structured_data, job.jd_text)
                
                # 发送内容
                yield f"data: {json.dumps({'type': 'chunk', 'content': resume}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
                
                # 发送完成标记
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                
                # 保存到数据库
                job_service.update_tailored_resume(job, resume)
                return

            # LLM 模式：流式生成
            logger.info("Using LLM mode with streaming")
            
            # Step 1: 技能映射（非流式，但发送给前端）
            from langchain_core.messages import HumanMessage, SystemMessage
            
            system_prompt_step1 = """你是高级简历顾问。请分析岗位JD，提取核心技能要求，并与候选人简历进行映射。

任务：
1. 从JD中提取前10个核心硬技能和软技能
2. 在候选人简历中寻找能够证明这些技能的经历
3. 输出技能映射表

输出JSON格式：
{
  "required_skills": ["技能1", "技能2", ...],
  "skill_mapping": {
    "技能1": {
      "found_in_resume": true/false,
      "evidence": "简历中的具体证据",
      "confidence": 0-1
    }
  },
  "missing_skills": ["缺失技能1", ...],
  "highlight_projects": ["需要突出的项目1", ...]
}

只返回JSON，不要其他文本。"""

            messages_step1 = [
                SystemMessage(content=system_prompt_step1),
                HumanMessage(content=f"岗位 JD：\n{job.jd_text}\n\n候选人简历数据：\n{json.dumps(vault.structured_data, ensure_ascii=False, indent=2)}")
            ]

            try:
                response_step1 = llm_client.invoke(messages_step1)
                mapping_result = json.loads(response_step1.content)
                logger.info(f"Step 1 - Skill mapping completed")
                
                # 发送技能映射数据
                yield f"data: {json.dumps({'type': 'mapping', 'data': mapping_result}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Step 1 failed: {e}")
                mapping_result = {"required_skills": [], "skill_mapping": {}, "missing_skills": [], "highlight_projects": []}

            # Step 2: 严格重写（流式生成）
            system_prompt_step2 = """你是高级简历顾问。你只能使用候选人简历中提供的事实。

任务：根据技能映射关系，重写工作经历描述，突出与JD匹配的技能。

严格规则：
1. 只能使用简历中提到的技术栈和项目经验
2. 可以调整语序、突出关键词、使用更专业的表达方式
3. 绝对禁止添加简历中未提及的技术栈或虚构项目数据
4. 工作经历描述使用 STAR 法则
5. 突出量化成果

输出 Markdown 格式的完整简历。直接开始输出简历内容，不要添加任何解释或前缀。"""

            messages_step2 = [
                SystemMessage(content=system_prompt_step2),
                HumanMessage(content=f"技能映射：\n{json.dumps(mapping_result, ensure_ascii=False, indent=2)}\n\n候选人简历数据：\n{json.dumps(vault.structured_data, ensure_ascii=False, indent=2)}")
            ]

            # 使用流式生成
            generated_resume = ""
            try:
                for chunk in llm_client.stream(messages_step2):
                    content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                    if content:
                        generated_resume += content
                        # 发送内容块
                        yield f"data: {json.dumps({'type': 'chunk', 'content': content}, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.01)  # 小延迟避免阻塞
                
                logger.info("Step 2 - Resume streaming generation completed")
            except Exception as e:
                logger.error(f"Step 2 streaming failed: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': f'生成失败: {str(e)}'}, ensure_ascii=False)}\n\n"
                return

            # Step 3: 校验（非流式，但发送给前端）
            from app.services.hallucination_service import get_hallucination_service
            hallucination_service = get_hallucination_service()
            verification_result = hallucination_service.verify_resume_generation(
                vault.structured_data,
                generated_resume,
                return_details=True
            )
            
            logger.info(f"Step 3 - Verification completed")
            
            # 发送校验结果
            yield f"data: {json.dumps({'type': 'verification', 'data': verification_result}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.01)

            # 保存到数据库
            job_service.update_tailored_resume(job, generated_resume)
            
            # 发送完成标记
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )


@router.get("/{job_id}/tailor/versions")
def get_resume_versions(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取简历版本历史"""
    job_service = JobService(db)
    job = job_service.get_job_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    versions = job.tailored_resume_versions or []
    return {"versions": versions}


@router.post("/{job_id}/tailor/versions")
def save_resume_version(
    job_id: str,
    version_data: ResumeVersionCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """保存新版本简历"""
    from datetime import datetime

    job_service = JobService(db)
    job = job_service.get_job_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    # 初始化版本列表
    if not job.tailored_resume_versions:
        job.tailored_resume_versions = []

    # 添加新版本
    new_version = {
        "version": len(job.tailored_resume_versions) + 1,
        "content": version_data.content,
        "note": version_data.note,
        "created_at": datetime.utcnow().isoformat()
    }
    job.tailored_resume_versions.append(new_version)

    db.commit()
    db.refresh(job)

    return new_version


@router.post("/{job_id}/verify")
def verify_resume(
    job_id: str,
    resume_content: dict,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    手动校验简历内容是否存在幻觉
    
    请求体：
    {
        "resume_content": "简历Markdown内容"
    }
    
    返回：
    {
        "verified": true/false,
        "hallucination_level": "none/low/medium/high",
        "confidence_score": 0.95,
        "suspicious_count": 2,
        "suggestions": ["建议1", "建议2"],
        "details": {详细分析结果}
    }
    """
    from app.services.hallucination_service import get_hallucination_service
    from app.services.vault_service import VaultService

    job_service = JobService(db)
    vault_service = VaultService(db)

    job = job_service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    vault = vault_service.get_vault_by_user_id(current_user.id)
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传简历到 Career Vault"
        )

    # 获取简历内容
    content = resume_content.get("resume_content", "")
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供简历内容"
        )

    # 执行幻觉校验
    hallucination_service = get_hallucination_service()
    result = hallucination_service.verify_resume_generation(
        vault.structured_data,
        content,
        return_details=True
    )

    return result


@router.get("/{job_id}/export/pdf")
def export_resume_pdf(
    job_id: str,
    template: str = "modern",
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    导出简历为PDF
    
    参数：
    - template: 模板名称 (modern/classic/creative)
    
    返回：PDF文件下载
    """
    job_service = JobService(db)
    vault_service = VaultService(db)
    pdf_service = get_pdf_service()

    job = job_service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    # 获取简历内容
    resume_content = job.tailored_resume_md
    if not resume_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先生成定制简历"
        )

    # 生成PDF
    try:
        result = pdf_service.generate_pdf(
            resume_content=resume_content,
            template=template,
            metadata={
                "name": current_user.username,
                "job_title": job.job_title,
                "company": job.company_name
            }
        )

        if not result["success"]:
            # 降级方案：返回Markdown
            return {
                "success": False,
                "message": result.get("message", "PDF生成失败"),
                "fallback_format": "markdown",
                "content": resume_content
            }

        # 返回PDF文件
        file_path = result["file_path"]
        filename = f"{current_user.username}_{job.company_name}_{job.job_title}.pdf".replace(" ", "_")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/pdf"
        )

    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF导出失败: {str(e)}"
        )


@router.get("/templates/pdf")
def get_pdf_templates():
    """获取可用的PDF模板列表"""
    pdf_service = get_pdf_service()
    templates = pdf_service.get_available_templates()
    return {"templates": templates}


@router.get("/templates/pdf/{template_id}/preview")
def preview_pdf_template(template_id: str):
    """预览PDF模板（返回HTML）"""
    pdf_service = get_pdf_service()

    if template_id not in pdf_service.TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )

    html_preview = pdf_service.preview_template(template_id)
    return {"html": html_preview}


# ==================== 职位信息自动提取 API ====================

@router.post("/extract")
async def extract_job_from_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    从上传的文件中提取职位信息
    
    支持格式：PNG, JPG, JPEG, WEBP, PDF
    最大文件大小：10MB
    
    返回：
    {
        "success": true,
        "data": {
            "job_title": {"value": "...", "confidence": 0.9},
            "company_name": {"value": "...", "confidence": 0.85},
            ...
        },
        "processing_time": 2.5,
        "suggestions": ["..."]
    }
    """
    extraction_service = JobExtractionService()
    
    # 验证文件类型
    allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'application/pdf']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file.content_type}"
        )
    
    # 创建临时文件
    temp_file = None
    try:
        # 生成临时文件路径
        suffix = os.path.splitext(file.filename)[1] or '.tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_file = tmp.name
        
        # 处理提取请求
        request = JobExtractionRequest(
            file_path=temp_file,
            file_name=file.filename,
            file_type=file.content_type,
            user_id=str(current_user.id)
        )
        
        response = extraction_service.process_request(request)
        
        if response.success:
            return {
                "success": True,
                "data": response.job_info.to_dict() if response.job_info else None,
                "message": response.message,
                "suggestions": response.suggestions
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=response.message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提取失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@router.post("/extract/confirm")
async def confirm_extracted_job(
    job_data: dict,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    确认提取的职位信息并创建职位记录
    
    请求体：
    {
        "job_title": "...",
        "company_name": "...",
        "location": "...",
        "salary_min": 15000,
        "salary_max": 25000,
        "experience_required": "3-5年",
        "education_required": "本科",
        "job_description": "...",
        "job_requirements": "...",
        "jd_text": "原始JD文本（可选）"
    }
    
    返回：创建成功的职位记录
    """
    try:
        job_service = JobService(db)
        
        # 构建JD文本（如果没有提供）
        jd_text = job_data.get("jd_text", "")
        if not jd_text:
            jd_parts = []
            if job_data.get("job_description"):
                jd_parts.append(f"岗位职责:\n{job_data['job_description']}")
            if job_data.get("job_requirements"):
                jd_parts.append(f"任职要求:\n{job_data['job_requirements']}")
            jd_text = "\n\n".join(jd_parts)
        
        # 创建职位数据
        create_data = JobApplicationCreate(
            company_name=job_data.get("company_name", ""),
            job_title=job_data.get("job_title", ""),
            location=job_data.get("location", ""),
            jd_text=jd_text,
            salary_range=f"{job_data.get('salary_min', '')}-{job_data.get('salary_max', '')}" if job_data.get('salary_min') else "",
            status="preparing"
        )
        
        # 创建职位
        job = job_service.create_job(current_user.id, create_data)
        
        # 更新额外字段（如果有）
        if job_data.get("experience_required"):
            job.experience_required = job_data["experience_required"]
        if job_data.get("education_required"):
            job.education_required = job_data["education_required"]
        
        db.commit()
        db.refresh(job)
        
        return JobApplicationResponse.from_orm(job)
        
    except Exception as e:
        logger.error(f"Failed to create job from extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建职位失败: {str(e)}"
        )


# ==================== 状态历史 API ====================

from app.schemas.job_status import (
    JobStatusUpdateRequest,
    JobStatusHistoryResponse,
    JobStatusHistoryListResponse,
)
from app.models.job_status_history import JobStatusHistory
from datetime import datetime


@router.post("/{job_id}/status-with-history", response_model=JobStatusHistoryResponse)
def update_job_status_with_history(
    job_id: str,
    status_update: JobStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    更新求职投递状态并记录历史

    此接口会创建状态历史记录，适用于需要记录状态变更场景的情况。
    如果只需要简单更新状态，请使用 PUT /{job_id}/status 接口。
    """
    logger.info(f"[StatusUpdate] User {current_user.id} updating job {job_id} to {status_update.new_status}")

    try:
        job_service = JobService(db)
        job = job_service.get_job_by_id(job_id)

        if not job:
            logger.warning(f"[StatusUpdate] Job not found: {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="求职投递不存在"
            )

        if job.user_id != current_user.id:
            logger.warning(f"[StatusUpdate] Permission denied: user {current_user.id} for job {job_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此求职投递"
            )

        # 验证状态值
        valid_statuses = [
            "preparing", "applied", "resume_screening", "interview_scheduled",
            "interviewing", "offer_pending", "offered", "rejected", "withdrawn"
        ]
        if status_update.new_status not in valid_statuses:
            logger.warning(f"[StatusUpdate] Invalid status: {status_update.new_status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的状态值，必须是以下之一: {', '.join(valid_statuses)}"
            )

        old_status = job.status
        new_status = status_update.new_status

        # 更新职位状态
        job.status = new_status

        # 根据状态更新相关时间字段
        if new_status == "applied" and not job.applied_at:
            job.applied_at = datetime.utcnow()
        elif new_status == "interview_scheduled" and not job.interview_scheduled_at:
            job.interview_scheduled_at = datetime.utcnow()
        elif new_status in ["offered", "rejected"] and not job.final_result_at:
            job.final_result_at = datetime.utcnow()

        # 创建状态历史记录
        history_entry = JobStatusHistory(
            job_application_id=job_id,
            old_status=old_status,
            new_status=new_status,
            changed_at=status_update.changed_at or datetime.utcnow(),
            changed_by="user",
            notes=status_update.notes,
            metadata=status_update.metadata
        )

        db.add(history_entry)
        db.commit()
        db.refresh(history_entry)
        db.refresh(job)

        logger.info(f"[StatusUpdate] Successfully updated job {job_id} from {old_status} to {new_status}")

        return history_entry

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[StatusUpdate] Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"状态更新失败: {str(e)}"
        )


@router.get("/{job_id}/status-history", response_model=JobStatusHistoryListResponse)
def get_job_status_history(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取求职投递的状态变更历史"""
    job_service = JobService(db)
    job = job_service.get_job_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    history = db.query(JobStatusHistory).filter(
        JobStatusHistory.job_application_id == job_id
    ).order_by(JobStatusHistory.changed_at.desc()).all()

    return {
        "history": history,
        "total": len(history)
    }


# ==================== Phase 3: 工作流详情与溯源 API ====================

@router.get("/{job_id}/workflow-details", response_model=WorkflowDetailsResponse)
def get_workflow_details(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取简历定制工作流的详细步骤信息
    
    返回 JD 诉求与经历召回的双栏比对数据，展示 AI 如何匹配和选择经历。
    """
    from datetime import datetime
    import re

    job_service = JobService(db)
    vault_service = VaultService(db)
    llm_service = LLMService(db)

    job = job_service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    vault = vault_service.get_vault_by_user_id(current_user.id)
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传简历到 Career Vault"
        )

    # 获取技能映射数据（从之前的分析结果或重新生成）
    mapping_data = {}
    if job.match_analysis:
        mapping_data = job.match_analysis.get("skill_mapping", {})
    
    # 如果没有映射数据，重新生成
    if not mapping_data:
        try:
            llm_client = llm_service._get_llm_client()
            if llm_client:
                from langchain_core.messages import HumanMessage, SystemMessage
                
                system_prompt = """你是高级简历顾问。请分析岗位JD，提取核心技能要求，并与候选人简历进行映射。

任务：
1. 从JD中提取前10个核心硬技能和软技能
2. 在候选人简历中寻找能够证明这些技能的经历
3. 输出技能映射表

输出JSON格式：
{
  "required_skills": ["技能1", "技能2", ...],
  "skill_mapping": {
    "技能1": {
      "found_in_resume": true/false,
      "evidence": "简历中的具体证据",
      "confidence": 0-1
    }
  },
  "missing_skills": ["缺失技能1", ...],
  "highlight_projects": ["需要突出的项目1", ...]
}

只返回JSON，不要其他文本。"""

                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"岗位 JD：\n{job.jd_text}\n\n候选人简历数据：\n{json.dumps(vault.structured_data, ensure_ascii=False, indent=2)}")
                ]

                response = llm_client.invoke(messages)
                mapping_data = json.loads(response.content)
        except Exception as e:
            logger.error(f"Failed to generate skill mapping: {e}")
            mapping_data = {"required_skills": [], "skill_mapping": {}, "missing_skills": [], "highlight_projects": []}

    # 构建工作流步骤详情
    steps = []

    # Step 1: JD 分析
    jd_requirements = []
    required_skills = mapping_data.get("required_skills", [])
    for skill in required_skills[:8]:  # 限制数量
        jd_requirements.append(JDRequirementItem(
            skill=skill,
            category="core_tech" if any(kw in skill.lower() for kw in ["python", "java", "react", "node"]) else "soft_skill",
            importance="high",
            context=f"JD中明确要求{skill}"
        ))

    # Step 2: 经历召回
    recalled_experiences = []
    skill_mapping = mapping_data.get("skill_mapping", {})
    
    # 从简历结构化数据中提取经历
    experiences = vault.structured_data.get("experiences", [])
    for idx, exp in enumerate(experiences[:5]):
        exp_title = exp.get("title", "未命名经历")
        exp_company = exp.get("company", "")
        exp_period = exp.get("period", "")
        exp_description = exp.get("description", "")
        
        # 计算匹配度
        match_score = 0
        matched_skills = []
        for skill, mapping in skill_mapping.items():
            if mapping.get("found_in_resume", False):
                evidence = mapping.get("evidence", "")
                if skill.lower() in exp_description.lower() or skill.lower() in exp_title.lower():
                    match_score += 10
                    matched_skills.append(skill)
        
        match_score = min(match_score, 100)  # 上限100
        
        if match_score > 0:
            recalled_experiences.append(ExperienceEvidenceItem(
                experience_id=f"exp_{idx}",
                title=exp_title,
                company=exp_company,
                period=exp_period,
                evidence_text=exp_description[:200] + "..." if len(exp_description) > 200 else exp_description,
                match_score=match_score,
                match_reason=f"匹配技能: {', '.join(matched_skills[:3])}" if matched_skills else "经历相关"
            ))

    # 按匹配度排序
    recalled_experiences.sort(key=lambda x: x.match_score, reverse=True)

    # 添加步骤
    steps.append(WorkflowStepDetail(
        step_name="JD 诉求解析",
        step_description="从职位描述中提取核心技能要求和关键诉求",
        jd_requirements=jd_requirements,
        recalled_experiences=[],
        processing_status="completed"
    ))

    steps.append(WorkflowStepDetail(
        step_name="经历主体召回",
        step_description="从经历总库中召回与 JD 诉求最相关的经历片段",
        jd_requirements=[],
        recalled_experiences=recalled_experiences[:5],
        processing_status="completed"
    ))

    steps.append(WorkflowStepDetail(
        step_name="经历重写优化",
        step_description="基于召回的经历，使用 STAR 法则重写描述，突出与 JD 的匹配度",
        jd_requirements=[],
        recalled_experiences=[],
        processing_status="completed"
    ))

    return WorkflowDetailsResponse(
        job_id=job_id,
        steps=steps,
        generated_at=datetime.utcnow()
    )


@router.get("/{job_id}/provenance", response_model=ProvenanceMapResponse)
def get_provenance_map(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取 AI 生成内容的数据溯源映射
    
    展示 AI 生成的每个声明/数值的来源，帮助用户验证内容真实性。
    """
    from datetime import datetime
    import re

    job_service = JobService(db)
    vault_service = VaultService(db)

    job = job_service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="求职投递不存在"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此求职投递"
        )

    vault = vault_service.get_vault_by_user_id(current_user.id)
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传简历到 Career Vault"
        )

    # 获取定制简历内容
    resume_content = job.tailored_resume_md or ""
    if not resume_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先生成定制简历"
        )

    # 获取校验结果
    from app.services.hallucination_service import get_hallucination_service
    hallucination_service = get_hallucination_service()
    verification_result = hallucination_service.verify_resume_generation(
        vault.structured_data,
        resume_content,
        return_details=True
    )

    # 提取数值声明（如 "提升 30%"、"减少 50%" 等）
    provenance_items = []
    
    # 数值模式匹配
    metric_patterns = [
        r'(\d+(?:\.\d+)?)\s*%',
        r'(\d+(?:\.\d+)?)\s*倍',
        r'(\d+(?:\.\d+)?)\s*万',
        r'(\d+(?:\.\d+)?)\s*千',
        r'(\d+(?:\.\d+)?)\s*亿',
    ]
    
    # 从校验结果中提取声明
    verified_claims = verification_result.get("verified_claims", [])
    suspicious_claims = verification_result.get("suspicious_claims", [])
    
    for claim in verified_claims:
        claim_text = claim.get("claim", "")
        source = claim.get("source", "")
        confidence = claim.get("confidence", 0.8)
        
        provenance_items.append(ProvenanceItem(
            claim=claim_text,
            claim_type="metric" if any(re.search(p, claim_text) for p in metric_patterns) else "skill",
            source_type="vault_experience" if source else "inferred",
            source_text=source if source else None,
            confidence=confidence,
            verification_status="verified"
        ))
    
    for claim in suspicious_claims:
        claim_text = claim.get("claim", "")
        reason = claim.get("reason", "")
        
        provenance_items.append(ProvenanceItem(
            claim=claim_text,
            claim_type="metric" if any(re.search(p, claim_text) for p in metric_patterns) else "other",
            source_type="hallucinated",
            source_text=None,
            confidence=0.3,
            verification_status="warning"
        ))

    # 如果没有提取到声明，添加一些示例
    if not provenance_items:
        # 从简历内容中提取一些关键句子
        sentences = re.split(r'[。！？\n]', resume_content)
        for sentence in sentences[:5]:
            sentence = sentence.strip()
            if len(sentence) > 10:
                has_metric = any(re.search(p, sentence) for p in metric_patterns)
                if has_metric:
                    provenance_items.append(ProvenanceItem(
                        claim=sentence[:100],
                        claim_type="metric",
                        source_type="inferred",
                        confidence=0.7,
                        verification_status="unverified"
                    ))

    # 计算整体置信度
    if provenance_items:
        overall_confidence = sum(item.confidence for item in provenance_items) / len(provenance_items)
    else:
        overall_confidence = 0.5

    return ProvenanceMapResponse(
        job_id=job_id,
        provenance_items=provenance_items,
        overall_confidence=overall_confidence,
        generated_at=datetime.utcnow()
    )
