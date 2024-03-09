"""https://platform.openai.com/docs/api-reference/files"""

import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Literal, Optional

from aiocron import crontab
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form
from fastapi import Depends
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_
from sqlalchemy.orm import Session

from tools.DB import get_db, FileRecord

router = APIRouter(prefix="/v1/files", tags=["files"], responses={404: {"description": "Not found"}}, )

FILE_CACHE_DIR = "cache"
FILE_EXPIRATION_DELTA = timedelta(hours=6)


class FileNotFound(FileNotFoundError):
    def __init__(self, file_id: str = None):
        self.file_id = file_id


class FileResponseModel(BaseModel):
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


def check_file_exists(file_id: str):
    """检查文件是否存在"""
    if not os.path.exists(os.path.join(FILE_CACHE_DIR, file_id)):
        raise FileNotFound(file_id=file_id)


def remove_file(file_id: str):
    """删除文件"""
    try:
        os.remove(os.path.join(FILE_CACHE_DIR, file_id))
    except FileNotFoundError:
        pass


@crontab('0 0 * * *')
async def clean_expired_files_cron():
    """定时清理过期文件"""
    with get_db() as db:
        expired_files = db.query(FileRecord).filter(and_(FileRecord.expiration < datetime.now())).all()
        for file_record in expired_files:
            db.delete(file_record)
            db.commit()
            remove_file(file_record.id)


@router.post("", response_model=FileResponseModel)
async def upload_file(
        file: UploadFile = File(...),
        purpose: str = Form(...),
        db: Session = Depends(get_db)):
    """文件上传接口"""
    logging.info(f"Start uploading file: {file.filename}, file type: {file.content_type}, purpose: {purpose}")

    # 保存文件信息
    file_object = FileResponseModel(bytes=file.size, filename=file.filename, purpose=purpose)

    # 异步保存文件
    os.makedirs(FILE_CACHE_DIR, exist_ok=True)
    async with aiofiles.open(os.path.join(FILE_CACHE_DIR, file_object.id), "wb") as buffer:
        data = await file.read(1024)
        while data:
            await buffer.write(data)
            data = await file.read(1024)

    file_record = FileRecord(id=file_object.id, filename=file_object.filename, purpose=file_object.purpose,
                             created_at=file_object.created_at, bytes=file_object.bytes,
                             expiration=datetime.now() + FILE_EXPIRATION_DELTA, content_type=file.content_type)
    db.add(file_record)
    db.commit()

    logging.info(f"Finish uploading file: {file.filename}, saved as: {file_object.id}")
    return file_object


@router.get("")
async def list_files():
    """列出所有文件"""
    return JSONResponse(status_code=404, content={
        "object": "error",
        "message": "List files api not supported.",
        "type": "NotFoundError",
        "param": None,
        "code": 404
    })

    # logging.info("Start listing files")
    # file_records = db.query(FileRecord).filter(and_(FileRecord.expiration > datetime.now())).all()
    # file_objects = [FileResponse(id=file_record.id, filename=file_record.filename, bytes=file_record.bytes,
    #                              created_at=int(file_record.created_at), purpose=file_record.purpose) for file_record
    #                 in file_records]
    # logging.info("Finish listing files")
    # return file_objects


@router.get("/{file_id}")
async def retrieve_file(file_id: str, db: Session = Depends(get_db)):
    """Returns information about a specific file."""
    logging.info(f"Start retrieving file: {file_id}")

    file_record = db.query(FileRecord).filter(
        and_(FileRecord.id == file_id, FileRecord.expiration > datetime.now())).first()

    # verify
    if file_record is None:
        raise FileNotFound(file_id=file_id)
    check_file_exists(file_id=file_id)

    logging.info(f"Finish retrieving file: {file_id}")
    return FileResponseModel(filename=file_record.filename, bytes=file_record.bytes, created_at=int(file_record.created_at),
                             id=file_record.id, purpose=file_record.purpose)


@router.delete("/{file_id}")
async def delete_file(file_id: str, db: Session = Depends(get_db)):
    """Deletes a specific file."""
    logging.info(f"Start deleting file: {file_id}")

    file_record = db.query(FileRecord).filter(and_(FileRecord.id == file_id)).first()

    # verify
    if file_record is None:
        raise FileNotFound(file_id=file_id)
    check_file_exists(file_id=file_id)

    # clear
    db.delete(file_record)
    db.commit()
    remove_file(file_record.id)

    logging.info(f"Finish deleting file: {file_id}")
    return FileDeleteResponse(id=file_id, deleted=True)


@router.get("/{file_id}/content")
async def retrieve_file_content(file_id: str, db: Session = Depends(get_db)):
    """Returns the content of a specific file."""
    logging.info(f"Start retrieving file content: {file_id}")

    file_record = db.query(FileRecord).filter(
        and_(FileRecord.id == file_id, FileRecord.expiration > datetime.now())).first()

    # verify
    if file_record is None:
        raise FileNotFound(file_id=file_id)
    check_file_exists(file_id=file_id)

    logging.info(f"Finish retrieving file content: {file_id}")
    return FileResponse(path=os.path.join(FILE_CACHE_DIR, file_record.id), filename=file_record.filename,
                        media_type=file_record.content_type)
