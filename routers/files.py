"""https://platform.openai.com/docs/api-reference/files"""

import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Literal, Optional

import aiocron
import aiofiles
from fastapi import APIRouter, UploadFile, File
from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy import and_
from sqlalchemy.orm import Session

from tools.DB import get_db, FileRecord

router = APIRouter(prefix="/v1/files", tags=["files"], responses={404: {"description": "Not found"}}, )

FILE_CACHE_DIR = "cache"
FILE_EXPIRATION_DELTA = timedelta(hours=12)


class FileNotFound(FileNotFoundError):
    def __init__(self, file_id: str = None):
        self.file_id = file_id


class FileResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"file-{uuid.uuid4().hex}", description="The file identifier")
    object: str = Field(default="file", description="The object type, which is always file.")
    bytes: int = Field(description="The size of the file, in bytes.")
    created_at: Optional[int] = Field(default_factory=lambda: int(time.time()),
                                      description="The Unix timestamp (in seconds) for when the file was created.")
    filename: str = Field(description="The name of the file.")
    purpose: Literal["fine-tune", "fine-tune-results", "assistants", "assistants_output"] = Field(
        description="The intended purpose of the file. Supported values are fine-tune, fine-tune-results, assistants, and assistants_output.")


class FileDeleteResponse(BaseModel):
    id: str = Field(description="The file identifier")
    object: str = Field(default="file", description="The object type, which is always file.")
    deleted: bool = Field(description="Whether the file was deleted.")


@aiocron.crontab('0 0 * * *')
async def clean_expired_files_cron():
    """定时清理过期文件"""
    with get_db(None) as db:
        expired_files = db.query(FileRecord).filter(FileRecord.expiration < datetime.now()).all()
        for file_record in expired_files:
            os.remove(os.path.join(FILE_CACHE_DIR, file_record.filename))
            db.delete(file_record)
        db.commit()


@router.post("", response_model=FileResponse)
async def upload_file(
        file: UploadFile = File(...),
        purpose: Literal["fine-tune", "fine-tune-results", "assistants", "assistants_output"] = None,
        db: Session = Depends(get_db)):
    # todo: can't get purpose from request body
    """文件上传接口"""
    logging.debug(f"Get request: {file.filename}, file type: {file.content_type}, purpose: {purpose}")

    # 异步保存文件
    os.makedirs(FILE_CACHE_DIR, exist_ok=True)
    async with aiofiles.open(os.path.join(FILE_CACHE_DIR, file.filename), "wb") as buffer:
        await buffer.write(await file.read())

    response = FileResponse(bytes=file.size, filename=file.filename, purpose=purpose)
    file_record = FileRecord(id=response.id, filename=response.filename, purpose=response.purpose,
                             created_at=response.created_at, bytes=response.bytes,
                             expiration=datetime.now() + FILE_EXPIRATION_DELTA)
    db.add(file_record)
    db.commit()

    return response


@router.get("/v1/files/{file_id}")
async def retrieve_file(file_id: str, db: Session = Depends(get_db)):
    """Returns information about a specific file."""
    file_record = db.query(FileRecord).filter(
        and_(FileRecord.id == file_id, FileRecord.expiration > datetime.now())).first()
    if file_record is None:
        raise FileNotFound(file_id=file_id)
    logging.debug(f"Retrieve file: {file_record.filename}")
    return FileResponse(filename=file_record.filename, bytes=file_record.bytes)


@router.delete("/v1/files/{file_id}")
async def delete_file(file_id: str, db: Session = Depends(get_db)):
    """Deletes a specific file."""
    file_record = db.query(FileRecord).filter(and_(FileRecord.id == file_id)).first()
    if file_record is None:
        raise FileNotFound(file_id=file_id)

    file_path = os.path.join(FILE_CACHE_DIR, file_record.filename)
    os.remove(file_path)
    db.delete(file_record)
    db.commit()
    return FileDeleteResponse(id=file_id, deleted=True)
