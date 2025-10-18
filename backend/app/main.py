"""
PASE FastAPI Backend

Main application entry point for the Protein Allosteric Site Prediction API.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from pathlib import Path

# Create FastAPI app
app = FastAPI(
    title="PASE API",
    description="Protein Allosteric Site Prediction using GVP-GNN",
    version="0.1.0"
)

# CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class PredictionRequest(BaseModel):
    protein_id: str
    source: str = "pdb"  # pdb or uniprot

class ResiduePrediction(BaseModel):
    chain: str
    residue_number: int
    residue_name: str
    probability: float
    allosteric: bool

class PredictionResponse(BaseModel):
    protein_id: str
    total_residues: int
    predicted_allosteric: int
    residues: List[ResiduePrediction]
    visualization_url: Optional[str] = None

class SystemStatus(BaseModel):
    model_status: str
    phase: str
    phase_description: str
    validated_proteins: int
    allosteric_residues: int


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "PASE API",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "predict": "/api/predict",
            "upload": "/api/upload",
            "search": "/api/search",
            "status": "/api/status"
        }
    }

@app.get("/api/status")
async def get_status() -> SystemStatus:
    """
    Get current system and model status.
    """
    return SystemStatus(
        model_status="training",
        phase="2 of 12 complete",
        phase_description="Data validation complete. Next: Preprocessing and feature extraction.",
        validated_proteins=116,
        allosteric_residues=2137
    )

@app.get("/api/search")
async def search_protein(query: str):
    """
    Search for a protein by PDB ID or UniProt ID.
    
    Args:
        query: PDB ID (e.g., 3UO9) or UniProt ID
        
    Returns:
        Protein metadata and availability status
    """
    # TODO: Implement protein database lookup
    # For now, return placeholder
    return {
        "query": query,
        "found": False,
        "message": "Protein search functionality will be implemented after model training completes.",
        "available_datasets": ["ASBench validated proteins"]
    }

@app.post("/api/upload")
async def upload_pdb(file: UploadFile = File(...)):
    """
    Upload a PDB file for analysis.
    
    Args:
        file: PDB file uploaded by user
        
    Returns:
        File information and processing status
    """
    # Validate file type
    if not file.filename.endswith('.pdb'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a PDB file."
        )
    
    # TODO: Save file and process
    # For now, return placeholder
    return {
        "filename": file.filename,
        "size": file.size if hasattr(file, 'size') else None,
        "status": "received",
        "message": "File uploaded successfully. Prediction functionality will be available after model training."
    }

@app.post("/api/predict")
async def predict_allosteric_sites(request: PredictionRequest) -> PredictionResponse:
    """
    Predict allosteric sites for a given protein.
    
    Args:
        request: Protein ID and source (PDB or UniProt)
        
    Returns:
        Predicted allosteric residues with probabilities
    """
    # TODO: Integrate with trained GVP-GNN model
    # For now, return placeholder response
    
    raise HTTPException(
        status_code=503,
        detail="Model training in progress. Prediction will be available after Phase 7 (Training) completes."
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Not Found",
        "message": "The requested endpoint does not exist.",
        "available_endpoints": ["/", "/api/status", "/api/search", "/api/upload", "/api/predict"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

