from fastapi import FastAPI
from product.api.v1.routes import router as v1_router
from product.db.session import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BlueprintAI Product API", version="1.0.0")

app.include_router(v1_router, prefix="/api/v1")
