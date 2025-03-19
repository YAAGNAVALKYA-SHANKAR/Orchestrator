from fastapi import APIRouter
from bson import ObjectId
from general.database import categories
from models.category_model import CategoryBase
from services.bulk_imp_exp import ImportExportService
from services import create, update, find, delete, change_status
router = APIRouter()

@router.post("/")
async def create_category(category: CategoryBase, created_by:str):
    return await create.Create.create(data=category, created_by=created_by, collection=categories, collection_type="Category", prefix="CAT")

@router.get("/{category_name}")
async def get_category_by_name(category_name: str):
    return await find.Find.get_doc_by_name(name=category_name, collection=categories, collection_type="Category")

@router.get("/")
async def get_all_categories():
    return await find.Find.get_all_docs(collection=categories, exclude_filter={"function": "ID_counter"})

@router.put("/{category_name}")
async def update_category(category_name: str, updated_data: CategoryBase, updated_by:str):
    return await update.Update.update(name=category_name, updated_by=updated_by, data=updated_data, collection=categories, collection_type="Category")

@router.delete("/{category_name}")
async def delete_category(category_name: str, deleted_by:str, reason:str):
    return await delete.Delete.delete(name=category_name, deleted_by=deleted_by, reason=reason, collection=categories, collection_type="Category")

@router.post("/import/{file_path}")
async def bulk_import_categories(overwrite:bool, file_path: str, user:str):
    return await ImportExportService.bulk_import(overwrite,file_path=file_path, user=user, collection=categories, collection_type="Categories")

@router.post("/export/{file_path}")
async def bulk_export_categories(file_path: str):
    return await ImportExportService.bulk_export(file_path=file_path, collection=categories, collection_type="Categories")

@router.post("/status")
async def category_status(category_name: str, new_status: str, changed_by: str):
    return await change_status.ChangeStatus.change_status(name=category_name , new_status=new_status, changed_by=changed_by, collection=categories, collection_type="Category")