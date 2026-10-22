"""
Job Processor - Orchestrates Instagram-to-blog pipeline
TODO: Implement full pipeline (see specs/tasks.md)
"""
import logging

logger = logging.getLogger(__name__)

async def process_instagram_job(job_id: str, instagram_url: str):
    """
    Process Instagram job - STUB IMPLEMENTATION
    
    TODO: Implement full pipeline:
    1. Scrape Instagram (instagram_scraper.py)
    2. Classify content (classifier.py)
    3. Generate blog (gemini_generator.py)
    4. Detect affiliates (affiliate_detector.py)
    5. Embed videos (youtube_embedder.py)
    6. Generate card (card_generator.py)
    7. Upload to Supabase (supabase_client.py)
    8. POST callback to Next.js
    
    For now, just logs the job.
    """
    logger.info(f"[STUB] Processing job {job_id} for {instagram_url}")
    logger.warning("Job processor not yet implemented - see specs/tasks.md")
    
    # TODO: Remove this stub and implement actual processing
    # See specs/tasks.md - Task 7.1 for implementation details
    
    return {
        "status": "stub",
        "message": "Job processor not yet implemented",
        "job_id": job_id,
        "instagram_url": instagram_url
    }