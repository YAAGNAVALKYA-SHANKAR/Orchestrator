import tkinter as tk
from tkinter import filedialog
from fastapi import APIRouter,UploadFile,File,HTTPException
from services.entity_services import EntityServices
from models.entity_model import EntityBase,StatusEnum
service=EntityServices()
router = APIRouter()
@router.post("/")
async def create_new_entity(data:EntityBase):return await service.create_entity(data)
@router.get("/{entity_name}")
async def get_entity_by_name(entity_name: str):return await service.get_entity_by_name(entity_name) 
@router.get("/",response_model=list[str])
async def get_all_entities():return await service.get_all_entities()
@router.put("/{entity_name}")
async def update_entity(entity_name:str,new_data:EntityBase):return await service.update_entity(new_data,entity_name)
@router.delete("/{entity_name}")
async def delete_entity(entity_name:str):return await service.delete_entity(entity_name)
@router.post("/upload")
async def bulk_import_entities(overwrite:bool,entity_name:str,files:list[UploadFile]=File(...)):return await service.bulk_upload(overwrite,entity_name,files)
@router.post("/export/")
async def bulk_export_entities(entity_name):
    root=tk.Tk()
    root.withdraw()
    root.attributes('-topmost',True)
    file_types=[("CSV File","*.csv"),("Excel File","*.xlsx")]
    file_path=filedialog.asksaveasfilename(title="Select Destination & File Type",filetypes=file_types,defaultextension=".xlsx")
    if not file_path:raise HTTPException (status_code=400,detail="No destination selected")
    return await service.bulk_download(entity_name,file_path)
@router.post("/status")
async def change_status(entity_name:str,new_status:StatusEnum):return await service.change_entity_status(entity_name,new_status)
@router.post("/{entity_name}")
async def add_data(entity_name:str,data:dict):return await service.add_data_to_entity(entity_name,data)