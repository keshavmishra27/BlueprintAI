from fastapi import FastAPI
from backend.app.routers import members, assessment, repo_judge
from fastapi.middleware.cors import CORSMiddleware 

from backend.app.database import engine
from backend.app import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://127.0.0.1:5500",   
    "http://localhost:5500",
    "http://localhost:3000",   
    "*"                         
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)
app.include_router(members.router)
app.include_router(assessment.router)
app.include_router(repo_judge.router)

