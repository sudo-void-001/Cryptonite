"""
Cryptonite Pydantic Request and Response Schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field


class CapacityResponse(BaseModel):
    carrier_filename: str
    carrier_type: str
    capacity_bytes: int
    capacity_human: str


class SteganalysisResponse(BaseModel):
    chi_squared_p_value: float
    ssim_score: float
    rs_score: float
    psnr_db: float
    verdict: str
    is_suspicious: bool


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
