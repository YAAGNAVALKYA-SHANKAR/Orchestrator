from fastapi import APIRouter
from bson import ObjectId
from general.database import attributes
from models.attribute_model import AttributeBase
from services.bulk_imp_exp import ImportExportService
from services import create, update, find, delete, change_status
router = APIRouter()

@router.post("/")
async def create_attribute(attribute: AttributeBase, created_by:str):
    return await create.Create.create(data=attribute, created_by=created_by, collection=attributes, collection_type="Attribute", prefix="ATTR")

@router.get("/{attribute_name}")
async def get_attribute_by_name(attribute_name: str):
    return await find.Find.get_doc_by_name(name=attribute_name, collection=attributes, collection_type="Attribute")

@router.get("/")
async def get_all_attributes():
    return await find.Find.get_all_docs(collection=attributes, exclude_filter={"function": "ID_counter"})

@router.put("/{attribute_name}")
async def update_attribute(attribute_name: str, updated_data: AttributeBase, updated_by:str):
    return await update.Update.update(name=attribute_name, updated_by=updated_by, data=updated_data, collection=attributes, collection_type="Attribute")

@router.delete("/{attribute_name}")
async def delete_attribute(attribute_name: str, deleted_by:str, reason:str):
    return await delete.Delete.delete(name=attribute_name, deleted_by=deleted_by, reason=reason, collection=attributes, collection_type="Attribute")

@router.post("/import/{file_path}")
async def bulk_import_attributes(overwrite:bool, file_path: str, user:str):
    return await ImportExportService.bulk_import(overwrite,file_path=file_path, user=user, collection=attributes, collection_type="Attributes")

@router.post("/export/{file_path}")
async def bulk_export_attributes(file_path: str):
    return await ImportExportService.bulk_export(file_path=file_path, collection=attributes, collection_type="Attributes")

@router.post("/status")
async def attribute_status(attribute_name: str, new_status: str, changed_by: str):
    return await change_status.ChangeStatus.change_status(name=attribute_name , new_status=new_status, changed_by=changed_by, collection=attributes, collection_type="Attribute")