from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import (
    RepoJudgeAnalysisPayload, 
    RepositoryAssessment, 
    SemanticReport, 
    create_result_from_payload,
    StructuralLayer,
    SemanticLayer
)
from database import save_analysis, get_analysis, list_analyses
from security import sanitize_payload

app = FastAPI(title="Repo Judge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

import urllib.request
import urllib.error
import json

@app.post("/api/analysis", response_model=RepositoryAssessment)
def create_analysis(payload: RepoJudgeAnalysisPayload):
    
    if sanitize_payload(payload.model_dump()):
        raise HTTPException(
            status_code=400, 
            detail="Sensitive credential-like content was detected in the analysis payload. Request rejected for security."
        )

    product_api_url = f"http://localhost:8000/api/v1/decisions/{payload.decision_id}"
    try:
        req = urllib.request.Request(product_api_url)
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                raise HTTPException(status_code=404, detail="Decision not found in canonical API")
            
            decision_data = json.loads(response.read().decode())
            decision_fingerprint = decision_data.get("decision_fingerprint")
            if not decision_fingerprint:
                raise HTTPException(status_code=500, detail="Decision fingerprint missing in canonical API response")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise HTTPException(status_code=404, detail="Decision not found in canonical API")
        raise HTTPException(status_code=500, detail=f"Error fetching decision: {str(e)}")
    except urllib.error.URLError as e:
        raise HTTPException(status_code=500, detail=f"Could not connect to Product API: {str(e)}")

    semantic_report = create_result_from_payload(payload, decision_fingerprint)
    
    gap_api_url = "http://localhost:8000/api/v1/repositories/analyze"
    gap_payload = {
        "decision_id": payload.decision_id,
        "repo_path": payload.repo_path
    }
    
    structural_layer = StructuralLayer(status="unavailable", report=None)
    try:
        req = urllib.request.Request(gap_api_url, data=json.dumps(gap_payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                gap_data = json.loads(response.read().decode())
                
                if gap_data.get("decision_id") != semantic_report.metadata.decision_id:
                    raise HTTPException(status_code=400, detail="Decision ID mismatch between structural and semantic reports")
                if gap_data.get("decision_fingerprint") != semantic_report.metadata.decision_fingerprint:
                    raise HTTPException(status_code=400, detail="Decision fingerprint mismatch between structural and semantic reports")
                    
                structural_layer = StructuralLayer(status="success", report=gap_data)
            else:
                structural_layer = StructuralLayer(status="failure", report=None)
    except urllib.error.URLError:
        structural_layer = StructuralLayer(status="failure", report=None)

    assessment = RepositoryAssessment(
        metadata=semantic_report.metadata,
        structural=structural_layer,
        semantic=SemanticLayer(status="success", report=semantic_report)
    )
    
    save_analysis(assessment.model_dump())
    
    return assessment

@app.get("/api/analysis/{analysis_id}", response_model=RepositoryAssessment)
def retrieve_analysis(analysis_id: str):
    result = get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result

@app.get("/api/analyses")
def list_all_analyses():
    return list_analyses()
