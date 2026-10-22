# Requirements - HuggingFace Space Backend

## Core Requirements

### R1: Instagram Scraping
**Goal**: Extract content from Instagram posts without API keys

**Acceptance Criteria**:
- Use instaloader library (no auth required)
- Extract: caption, media_url, posted_date, video_url (if video)
- Parse YouTube links from caption via regex
- Handle both /p/ and /reel/ URLs
- Return structured data: InstagramReelData

### R2: Content Classification
**Goal**: Categorize Instagram content into types

**Acceptance Criteria**:
- Use 	ransformers zero-shot classification
- Model: facebook/bart-large-mnli (loaded at startup)
- Categories: videos, books, products, habits, general
- Return content_type with confidence score
- Default to 'general' if confidence < 0.7

### R3: Blog Generation with Gemini
**Goal**: Generate 1500-2000 word blog articles

**Acceptance Criteria**:
- Use Google Gemini API (gemini-1.5-flash)
- Input: caption + content_type
- Output: markdown article with title, headings, sections
- Streaming responses for progress updates
- Retry logic for API failures (3 attempts)
- Rate limiting: 15 RPM (Gemini free tier)

### R4: Social Card Generation
**Goal**: Create 1080x1080 Instagram-style PNG cards

**Acceptance Criteria**:
- Use Pillow library
- Vibrant gradient background (purple ? pink ? orange)
- Title at top (72px bold, white)
- List items for listicles (48px, numbered, max 5)
- Footer: "ameetpandey.com" + "@ameetbuilds"
- Upload to Supabase Storage (social-cards bucket)
- Return public URL

### R5: Affiliate Placeholder Detection
**Goal**: Identify book/product mentions for manual affiliate linking

**Acceptance Criteria**:
- Active only for content_type: books, products
- Detect patterns: "Title" by Author, product names
- Replace with [AFFILIATE_PLACEHOLDER_N]
- Store metadata: {placeholderId, title, type, url: null}
- Return array of placeholders

### R6: YouTube Video Embedding
**Goal**: Extract and format YouTube links from caption

**Acceptance Criteria**:
- Extract URLs matching youtube.com or youtu.be
- Convert to markdown embed syntax
- Insert in "References & Resources" section
- Return list of embedded URLs

### R7: Webhook Endpoint
**Goal**: Receive job requests from Next.js app

**Acceptance Criteria**:
- POST /webhook/process-job
- Validate X-Webhook-Secret header
- Accept payload: {job_id, instagram_url}
- Process in background (FastAPI BackgroundTasks)
- Return 202 Accepted immediately

### R8: Job Processing Pipeline
**Goal**: Orchestrate end-to-end processing

**Acceptance Criteria**:
- Update Supabase job status: processing
- Execute pipeline: scrape ? classify ? generate ? detect ? embed ? card ? upload
- Handle errors with retries (max 3 attempts per step)
- Log progress to Supabase
- POST results to Next.js callback URL

### R9: Callback to Next.js
**Goal**: Notify Next.js when processing completes

**Acceptance Criteria**:
- POST to CALLBACK_URL with results
- Include HMAC signature for authentication
- Payload: {job_id, status, post_data, error}
- Retry on failure (3 attempts with exponential backoff)

### R10: Health Check
**Goal**: Monitor service health

**Acceptance Criteria**:
- GET /health endpoint
- Return: {status, cpu_percent, memory_percent, disk_percent}
- Used by Docker healthcheck

## Non-Functional Requirements

### Performance
- Process single job in < 3 minutes
- GPU-accelerated classification (< 1 second)
- Card generation in < 5 seconds

### Reliability
- Automatic retry on transient failures
- Graceful degradation (skip card if generation fails)
- Persistent logging

### Security
- Webhook secret validation
- Callback signature verification
- No secrets in logs

### Scalability
- Support 3 parallel jobs (current GPU capacity)
- Stateless design for horizontal scaling
