from fastapi import APIRouter, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from app.config import get_settings
from services.job_processor import process_instagram_job
import logging

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

class ProcessJobRequest(BaseModel):
    job_id: str
    instagram_url: HttpUrl

class ProcessJobResponse(BaseModel):
    status: str
    message: str
    job_id: str

@router.post("/process-job", response_model=ProcessJobResponse)
async def process_job(
    request: ProcessJobRequest,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str = Header(None)
):
    '''
    Webhook endpoint for processing Instagram jobs.
    Triggered by Next.js app via cron or manual submission.
    '''
    # Verify webhook secret
    if x_webhook_secret != settings.webhook_secret:
        logger.warning(f"Invalid webhook secret for job {request.job_id}")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    logger.info(f"Received job {request.job_id} for {request.instagram_url}")
    
    # Process job in background
    background_tasks.add_task(
        process_instagram_job,
        job_id=request.job_id,
        instagram_url=str(request.instagram_url)
    )
    
    return ProcessJobResponse(
        status="accepted",
        message="Job queued for processing",
        job_id=request.job_id
    )
