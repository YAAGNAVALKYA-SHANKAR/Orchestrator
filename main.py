import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from general.database import init_db
from routes.category_routes import router as category_router
from routes.attributes_routes import router as attribute_router
from routes.sub_cat_routes import router as sub_cat_routes
app = FastAPI()
app.include_router(category_router, prefix="/api/categories", tags=["Categories"])
app.include_router(attribute_router, prefix="/api/attributes", tags=["Attributes"])
app.include_router(sub_cat_routes, prefix="/api/sub-categories", tags=["Sub-Categories"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def read_root():
    return {"message": "CORS enabled!"}
@app.on_event("startup")
async def startup():
    await init_db()
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)