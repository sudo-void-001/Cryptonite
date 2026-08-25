"""
Cryptonite FastAPI REST Endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.schemas import CapacityResponse, SteganalysisResponse

app = FastAPI(
    title="Cryptonite REST API",
    description="Production-grade steganography toolkit API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "cryptonite"}
