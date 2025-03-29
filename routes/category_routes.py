import os
from fastapi import APIRouter, UploadFile, File
from bson import ObjectId
from general.database import categories
from models.category_model import CategoryBase
from services.bulk_imp_exp import ImportExportService
from services.category_services import CategoryServices
from services import change_status
router = APIRouter()
service=CategoryServices()

@router.post("/")
async def create_category(category: CategoryBase):
    return await service.create(data=category)

@router.get("/{category_id}")
async def get_category_by_name(category_id: str):
    return await service.get_category_by_name(category_id=category_id)

@router.get("/")
async def get_all_categories():
    return await service.get_all_categories()

@router.put("/{category_id}")
async def update_category(category_id: str, updated_data: CategoryBase):
    return await service.update(category_id=category_id, data=updated_data)

@router.delete("/{category_id}")
async def delete_category(category_id: str):
    return await service.delete(category_id=category_id)

@router.post("/bulk_upload/")
async def bulk_import_categories(overwrite:bool, files: list[UploadFile] = File(...)):
    return await service.bulk_upload(overwrite, files)

@router.post("/export/{file_path}")
async def bulk_export_categories(file_path: str):
    return await ImportExportService.bulk_export(file_path=file_path, collection=categories, collection_type="Categories")

@router.post("/status")
async def category_status(category_name: str, new_status: str, changed_by: str):
    return await change_status.ChangeStatus.change_status(name=category_name , new_status=new_status, changed_by=changed_by, collection=categories, collection_type="Category")