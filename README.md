---
title: Instagram Blog Processor
emoji: 🤖
colorFrom: purple
colorTo: pink
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# Instagram Blog Processor

AI service for processing Instagram posts into blog articles with social cards.

## Features

- Instagram scraping with instaloader
- Blog generation using Google Gemini API
- Social card generation with Pillow
- Content classification
- Webhook-based job processing

## API Endpoints

- GET /health - Health check
- POST /webhook/process-job - Process Instagram job

## Environment Variables

Set these in Space Settings - Variables and secrets:

- GEMINI_API_KEY - Google Gemini API key
- SUPABASE_URL - Supabase project URL
- SUPABASE_SERVICE_KEY - Supabase service role key
- WEBHOOK_SECRET - Secret for webhook authentication
- CALLBACK_URL - Next.js callback URL
- CALLBACK_SECRET - Secret for callback authentication

## Docker

This Space uses a custom Dockerfile. See Dockerfile for details.

Port: 7860