from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import logging

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas.user import UserResponse
from app.schemas.vault import CareerVaultResponse, CareerVaultUpdate
from pydantic import BaseModel
from app.services.vault_service import VaultService
from app.config import get_settings

router = APIRouter(prefix="/api/vault", tags=["经历总库"])
settings = get_settings()
logger = logging.getLogger(__name__)

# 内存存储处理状态（生产环境应使用Redis）
processing_status = {}


class ReparseRequest(BaseModel):
    raw_content: str


class UploadStatusResponse(BaseModel):
    status: str
    message: str
    vault: Optional[CareerVaultResponse] = None


@router.post("/reparse", response_model=CareerVaultResponse)
def reparse_vault(
    request: ReparseRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """根据编辑后的原始文本重新解析 Vault"""
    vault_service = VaultService(db)
    vault = vault_service.get_vault_by_user_id(current_user.id)

    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career Vault 不存在，请先上传简历"
        )

    # 使用新的原始文本重新解析
    structured_data = vault_service.extract_structured_data(request.raw_content)

    # 更新 Vault
    vault_data = CareerVaultUpdate(structured_data=structured_data)
    updated_vault = vault_service.update_vault(vault, vault_data)

    # 同时更新 raw_content
    vault.raw_content = request.raw_content
    db.commit()
    db.refresh(updated_vault)

    return updated_vault


def _process_resume_background(user_id: str, file_path: str, file_ext: str, upload_id: str):
    """后台处理简历文件"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        vault_service = VaultService(db)
        vault_service.upload_dir = settings.UPLOAD_DIR

        # 解析文件获取原始文本
        if file_ext == 'pdf':
            raw_content = vault_service._extract_text_from_pdf(file_path)
        elif file_ext in ['docx', 'doc']:
            raw_content = vault_service._extract_text_from_docx(file_path)
        else:
            raw_content = ""

        if not raw_content.strip():
            processing_status[upload_id] = {
                "status": "error",
                "message": "无法从文件中提取文本"
            }
            return

        # 提取结构化数据
        structured_data = vault_service.extract_structured_data(raw_content)

        # 检查是否已存在 Vault
        existing_vault = vault_service.get_vault_by_user_id(user_id)

        if existing_vault:
            existing_vault.raw_content = raw_content
            existing_vault.structured_data = structured_data
            existing_vault.version += 1
            existing_vault.updated_at = __import__('datetime').datetime.utcnow()
            db.commit()
            db.refresh(existing_vault)
            vault = existing_vault
        else:
            from app.schemas.vault import CareerVaultCreate
            vault_data = CareerVaultCreate(structured_data=structured_data)
            new_vault = vault_service.create_vault(user_id, vault_data)
            new_vault.raw_content = raw_content
            db.commit()
            db.refresh(new_vault)
            vault = new_vault

        processing_status[upload_id] = {
            "status": "completed",
            "message": "处理完成",
            "vault_id": vault.id
        }

    except Exception as e:
        processing_status[upload_id] = {
            "status": "error",
            "message": str(e)
        }
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
        db.close()


@router.get("/upload-status/{upload_id}", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取简历上传处理状态"""
    if upload_id not in processing_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到上传任务"
        )

    status_info = processing_status[upload_id]
    response = {
        "status": status_info["status"],
        "message": status_info["message"]
    }

    if status_info["status"] == "completed" and "vault_id" in status_info:
        vault_service = VaultService(db)
        vault = vault_service.get_vault_by_user_id(current_user.id)
        if vault:
            response["vault"] = vault

    # 清理已完成的记录
    if status_info["status"] in ["completed", "error"]:
        del processing_status[upload_id]

    return response


@router.post("/upload", response_model=CareerVaultResponse)
async def upload_resume(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """上传并解析简历 - 支持大文件异步处理"""
    vault_service = VaultService(db)

    # 检查文件类型
    allowed_types = {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/msword': 'doc',
    }

    content_type = file.content_type or ''

    # 如果没有 content_type，尝试从文件名推断
    if not content_type and file.filename:
        if file.filename.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif file.filename.lower().endswith('.docx'):
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif file.filename.lower().endswith('.doc'):
            content_type = 'application/msword'

    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型。请上传 PDF 或 Word 文档。"
        )

    # 检查文件大小
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    file_ext = allowed_types[content_type]

    # 如果文件小于1MB，直接同步处理
    if file_size < 1024 * 1024:  # 1MB
        vault = vault_service.process_resume_upload(current_user.id, file)
        return vault

    # 大文件使用后台任务异步处理
    import asyncio
    from fastapi import BackgroundTasks

    # 生成唯一ID
    upload_id = str(uuid.uuid4())
    temp_filename = f"{upload_id}.{file_ext}"
    temp_path = os.path.join(settings.UPLOAD_DIR, temp_filename)

    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # 保存文件
    content = await file.read()
    with open(temp_path, "wb") as f:
        f.write(content)

    # 初始化处理状态
    processing_status[upload_id] = {
        "status": "processing",
        "message": "文件正在处理中"
    }

    # 启动后台任务
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None,
        _process_resume_background,
        current_user.id,
        temp_path,
        file_ext,
        upload_id
    )

    # 立即返回处理中的响应
    raise HTTPException(
        status_code=status.HTTP_202_ACCEPTED,
        detail={
            "message": "文件正在处理中",
            "upload_id": upload_id,
            "status": "processing",
            "check_status_url": f"/api/vault/upload-status/{upload_id}"
        }
    )


@router.get("", response_model=CareerVaultResponse)
def get_vault(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取用户的 Career Vault"""
    vault_service = VaultService(db)
    vault = vault_service.get_vault_by_user_id(current_user.id)

    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career Vault 不存在，请先上传简历"
        )

    return vault


@router.put("", response_model=CareerVaultResponse)
def update_vault(
    vault_data: CareerVaultUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """更新 Career Vault 结构化数据"""
    vault_service = VaultService(db)
    vault = vault_service.get_vault_by_user_id(current_user.id)

    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career Vault 不存在，请先上传简历"
        )

    updated_vault = vault_service.update_vault(vault, vault_data)
    return updated_vault


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_vault(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """删除 Career Vault"""
    vault_service = VaultService(db)
    vault = vault_service.get_vault_by_user_id(current_user.id)

    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career Vault 不存在"
        )

    # 记录敏感操作日志
    client_ip = request.client.host
    logger.warning(f"SECURITY: User {current_user.id} deleted vault from IP {client_ip}")

    vault_service.delete_vault(vault)
    return None
