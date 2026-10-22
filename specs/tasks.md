# Implementation Tasks - HuggingFace Space

## Phase 1: Core Infrastructure

### Task 1.1: Project Setup
- [x] Create directory structure
- [x] Create Dockerfile
- [x] Create requirements.txt
- [x] Create .env.example
- [ ] Add psutil to requirements.txt
- [ ] Test Docker build locally

### Task 1.2: FastAPI Application
- [x] Create app/main.py with FastAPI instance
- [x] Create app/config.py with Pydantic settings
- [x] Create app/routers/health.py
- [x] Create app/routers/webhooks.py
- [ ] Test endpoints with curl

## Phase 2: Instagram Scraping

### Task 2.1: Implement Instagram Scraper
- [ ] Complete services/instagram_scraper.py
- [ ] Add instaloader initialization
- [ ] Implement scrape_post() method
- [ ] Add YouTube link extraction regex
- [ ] Add error handling and retries
- [ ] Write unit tests (tests/test_scraper.py)
- [ ] Test with real Instagram URLs

## Phase 3: Content Generation

### Task 3.1: Gemini API Integration
- [ ] Complete services/gemini_generator.py
- [ ] Initialize Gemini client with API key
- [ ] Implement generate_blog() method
- [ ] Add prompt templates for each content type
- [ ] Implement streaming response handling
- [ ] Add rate limiting (15 RPM)
- [ ] Write unit tests
- [ ] Test with sample captions

### Task 3.2: Content Classifier
- [ ] Complete services/classifier.py
- [ ] Load transformers pipeline (facebook/bart-large-mnli)
- [ ] Implement classify_content() method
- [ ] Add confidence threshold logic
- [ ] Cache model in memory
- [ ] Write unit tests
- [ ] Benchmark GPU vs CPU performance

## Phase 4: Social Card Generation

### Task 4.1: Card Generator with Pillow
- [ ] Complete services/card_generator.py
- [ ] Implement gradient background rendering
- [ ] Add text rendering with custom fonts
- [ ] Create layout for different content types
- [ ] Implement card templates (videos, books, products)
- [ ] Add Supabase Storage upload
- [ ] Write unit tests
- [ ] Generate sample cards

### Task 4.2: Card Templates
- [ ] Create templates/card_videos.py
- [ ] Create templates/card_books.py
- [ ] Create templates/card_products.py
- [ ] Create templates/card_habits.py
- [ ] Create templates/card_general.py

## Phase 5: Content Processing

### Task 5.1: Affiliate Detector
- [ ] Complete services/affiliate_detector.py
- [ ] Add book pattern detection regex
- [ ] Add product pattern detection
- [ ] Implement placeholder insertion
- [ ] Store placeholder metadata
- [ ] Write unit tests

### Task 5.2: YouTube Embedder
- [ ] Complete services/youtube_embedder.py
- [ ] Extract video IDs from URLs
- [ ] Generate markdown embed code
- [ ] Insert in References section
- [ ] Write unit tests

## Phase 6: Database Integration

### Task 6.1: Supabase Client
- [ ] Complete services/supabase_client.py
- [ ] Initialize Supabase client with service key
- [ ] Implement update_job_status()
- [ ] Implement upload_social_card()
- [ ] Implement create_draft_post()
- [ ] Add error handling
- [ ] Write integration tests

## Phase 7: Job Processing

### Task 7.1: Job Processor
- [ ] Complete services/job_processor.py
- [ ] Implement process_instagram_job() orchestration
- [ ] Add step-by-step status updates
- [ ] Implement error handling and retries
- [ ] Add progress logging
- [ ] Implement callback to Next.js
- [ ] Test end-to-end flow

### Task 7.2: Callback Service
- [ ] Implement POST to Next.js callback URL
- [ ] Add HMAC signature generation
- [ ] Add retry logic with exponential backoff
- [ ] Handle callback failures gracefully

## Phase 8: Testing

### Task 8.1: Unit Tests
- [ ] tests/test_scraper.py
- [ ] tests/test_gemini.py
- [ ] tests/test_classifier.py
- [ ] tests/test_card_generator.py
- [ ] tests/test_affiliate_detector.py
- [ ] tests/test_youtube_embedder.py
- [ ] Run pytest and ensure > 80% coverage

### Task 8.2: Integration Tests
- [ ] Test webhook endpoint with mock payload
- [ ] Test full pipeline with sample Instagram URL
- [ ] Test error scenarios (invalid URL, API failures)
- [ ] Test callback to mock Next.js endpoint

## Phase 9: Deployment

### Task 9.1: HuggingFace Space Setup
- [ ] Create HF Space: https://huggingface.co/new-space
- [ ] Choose Docker runtime with GPU (basic)
- [ ] Connect GitHub repository
- [ ] Add environment variables in Space settings:
  - GEMINI_API_KEY
  - SUPABASE_URL
  - SUPABASE_SERVICE_KEY
  - WEBHOOK_SECRET
  - CALLBACK_URL
  - CALLBACK_SECRET
- [ ] Test Space deployment
- [ ] Verify GPU access

### Task 9.2: GitHub Actions Setup
- [x] Create .github/workflows/process-queue.yml
- [ ] Add GitHub secrets:
  - NEXT_JS_APP_URL
  - CRON_SECRET
- [ ] Test manual workflow trigger
- [ ] Verify cron schedule (every 5 minutes)

### Task 9.3: Documentation
- [ ] Update README.md with setup instructions
- [ ] Document API endpoints
- [ ] Add troubleshooting guide
- [ ] Create deployment checklist

## Phase 10: Optimization

### Task 10.1: Performance Tuning
- [ ] Profile GPU usage
- [ ] Optimize model loading (cache at startup)
- [ ] Add Redis caching for repeated requests
- [ ] Benchmark processing time

### Task 10.2: Monitoring
- [ ] Add structured logging (JSON format)
- [ ] Implement metrics collection
- [ ] Add error alerting
- [ ] Create dashboard for job stats

## Next Steps After Completion

1. Test with real Instagram posts (all 46 from CSV)
2. Monitor processing time and success rate
3. Optimize prompts based on output quality
4. Add more card templates
5. Implement batch processing for multiple jobs
