from fastapi import APIRouter
from bson import ObjectId
from general.database import sub_categories
from models.sub_cat_model import SubCategoryBase
from services.bulk_imp_exp import ImportExportService
from services import create, update, find, delete, change_status
router = APIRouter()

@router.post("/")
async def create_sub_category(sub_category: SubCategoryBase, created_by:str):
    return await create.Create.create(data=sub_category, created_by=created_by, collection=sub_categories, collection_type="Sub-Category", prefix="SUB")

@router.get("/{sub_category_name}")
async def get_sub_category_by_name(sub_category_name: str):
    return await find.Find.get_doc_by_name(name=sub_category_name, collection=sub_categories, collection_type="Sub-Category")

@router.get("/")
async def get_all_sub_categories():
    return await find.Find.get_all_docs(collection=sub_categories, exclude_filter={"function": "ID_counter"})

@router.put("/{sub_category_name}")
async def update_category(sub_category_name: str, updated_data: SubCategoryBase, updated_by:str):
    return await update.Update.update(name=sub_category_name, updated_by=updated_by, data=updated_data, collection=sub_categories, collection_type="Sub-Category")

@router.delete("/{sub_category_name}")
async def delete_category(sub_category_name: str, deleted_by:str, reason:str):
    return await delete.Delete.delete(name=sub_category_name, deleted_by=deleted_by, reason=reason, collection=sub_categories, collection_type="Sub-Category")

@router.post("/import/{file_path}")
async def bulk_import_sub_categories(overwrite:bool, file_path: str, user:str):
    return await ImportExportService.bulk_import(overwrite,file_path=file_path, user=user, collection=sub_categories, collection_type="Sub-Categories")

@router.post("/export/{file_path}")
async def bulk_export_sub_categories(file_path: str):
    return await ImportExportService.bulk_export(file_path=file_path, collection=sub_categories, collection_type="Sub-Categories")

@router.post("/status")
async def category_status(sub_category_name: str, new_status: str, changed_by: str):
    return await change_status.ChangeStatus.change_status(name=sub_category_name , new_status=new_status, changed_by=changed_by, collection=sub_categories, collection_type="Sub-Category")