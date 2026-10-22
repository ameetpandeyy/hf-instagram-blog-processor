from fastapi import APIRouter
from pydantic import BaseModel
import psutil
import os

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float

@router.get("/health", response_model=HealthResponse)
async def health_check():
    '''Health check endpoint'''
    return HealthResponse(
        status="healthy",
        cpu_percent=psutil.cpu_percent(interval=1),
        memory_percent=psutil.virtual_memory().percent,
        disk_percent=psutil.disk_usage('/').percent
    )

@router.get("/")
async def root():
    '''Root endpoint'''
    return {
        "service": "Instagram Blog Processor",
        "version": "1.0.0",
        "status": "running"
    }
