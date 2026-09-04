"""
Cryptonite Pydantic Request and Response Schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CapacityResponse(BaseModel):
    carrier_filename: str
    carrier_type: str
    capacity_bytes: int
    capacity_human: str
    usable_bytes: int
    file_size_bytes: int

    model_config = ConfigDict(frozen=True)


class SteganalysisResponse(BaseModel):
    chi_squared_p_value: float
    ssim_score: float
    rs_score: float
    psnr_db: float
    verdict: str
    is_suspicious: bool

    model_config = ConfigDict(frozen=True)


class EmbedMetadata(BaseModel):
    carrier_filename: str
    payload_filename: str
    blob_bytes: int
    capacity_bytes: int
    capacity_used_pct: float
    elapsed_s: float

    model_config = ConfigDict(frozen=True)


class ExtractMetadata(BaseModel):
    recovered_filename: str
    recovered_bytes: int
    sha256: str
    elapsed_s: float

    model_config = ConfigDict(frozen=True)


class BatchEmbedSummary(BaseModel):
    total: int
    succeeded: int
    failed: int
    failed_files: list[str]

    model_config = ConfigDict(frozen=True)


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None

    model_config = ConfigDict(frozen=True)
