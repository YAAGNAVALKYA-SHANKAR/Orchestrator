from fastapi import APIRouter, UploadFile, File
from bson import ObjectId
from general.database import sub_categories
from models.sub_cat_model import SubCategoryBase
from services.subcategory_services import SubCategoryServices
from services import change_status
router = APIRouter()
service=SubCategoryServices()
@router.post("/")
async def create_sub_category(sub_category: SubCategoryBase):
    return await service.create(data=sub_category)

@router.get("/{sub_category_id}")
async def get_sub_category_by_id(sub_category_id: str):
    return await service.get_doc_by_id(sub_category_id=sub_category_id)

@router.get("/")
async def get_all_sub_categories():
    return await service.get_all_sub_categories()

@router.put("/{sub_category_id}")
async def update_category(sub_category_id: str, updated_data: SubCategoryBase):
    return await service.update(sub_category_id=sub_category_id, data=updated_data)

@router.delete("/{sub_category_id}")
async def delete_category(sub_category_id: str):
    return await service.delete(sub_category_id=sub_category_id)

@router.post("/bulk_upload/")
async def bulk_import_sub_categories(overwrite:bool, files: list[UploadFile] = File(...)):
    return await service.bulk_upload(overwrite, files)

@router.post("/export/{file_path}")
async def bulk_export_sub_categories(file_path: str):
    return await service.bulk_download(file_path=file_path, collection=sub_categories, collection_type="Sub-Categories")

@router.post("/status")
async def category_status(sub_category_name: str, new_status: str, changed_by: str):
    return await change_status.ChangeStatus.change_status(name=sub_category_name , new_status=new_status, changed_by=changed_by, collection=sub_categories, collection_type="Sub-Category")