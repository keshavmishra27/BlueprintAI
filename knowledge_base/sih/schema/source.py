from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SourceEvidence(BaseModel):
    source_url: str = Field(description="URL of the source")
    source_title: str = Field(description="Title of the source")
    source_type: str = Field(description="Type of source (official, news, repository, etc.)")
    retrieved_at: str = Field(description="ISO timestamp when the source was retrieved")
    extracted_text: str = Field(description="Raw text extracted that contains the evidence")
    notes: Optional[str] = Field(default=None, description="Researcher notes about the source")
