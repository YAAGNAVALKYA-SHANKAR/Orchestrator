from fastapi import APIRouter
from bson import ObjectId
from general.database import attributes
from models.attribute_model import AttributeBase
from services.bulk_imp_exp import ImportExportService
from services.attribute_services import AttributeServices
from services import change_status
router = APIRouter()
service=AttributeServices()
@router.post("/")

async def create_attribute(attribute: AttributeBase):
    return await service.create(data=attribute)

@router.get("/{attribute_name}")
async def get_attribute_by_name(attribute_id: str):
    return await service.get_doc_by_name(attribute_id=attribute_id)

@router.get("/")
async def get_all_attributes():
    return await service.get_all_docs()

@router.put("/{attribute_id}")
async def update_attribute(attribute_id: str, updated_data: AttributeBase):
    return await service.update(attribute_id=attribute_id, data=updated_data)

@router.delete("/{attribute_id}")
async def delete_attribute(attribute_id: str):
    return await service.delete(attribute_id=attribute_id)

@router.post("/import/{file_path}")
async def bulk_import_attributes(overwrite:bool, file_path: str, user:str):
    return await ImportExportService.bulk_import(overwrite,file_path=file_path, user=user, collection=attributes, collection_type="Attributes")

@router.post("/export/{file_path}")
async def bulk_export_attributes(file_path: str):
    return await ImportExportService.bulk_export(file_path=file_path, collection=attributes, collection_type="Attributes")

@router.post("/status")
async def attribute_status(attribute_name: str, new_status: str, changed_by: str):
    return await change_status.ChangeStatus.change_status(name=attribute_name , new_status=new_status, changed_by=changed_by, collection=attributes, collection_type="Attribute")