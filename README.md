# Instagram Blog Processor - HuggingFace Space

Python-based AI service for processing Instagram posts into blog articles with social cards.

## Architecture

**Next.js App (Vercel)** ? Webhooks ? **HuggingFace Space (Python/Docker)** ? API ? **Google Gemini**

## Features

- ?? Instagram scraping with instaloader (no API key needed)
- ?? Blog generation using Google Gemini API (1500-2000 words)
- ?? Social card generation with Pillow (1080x1080 Instagram-style)
- ??? Content classification (videos, books, products, habits, general)
- ?? Affiliate link placeholder detection
- ?? YouTube video embedding
- ?? Webhook-based job processing

## Tech Stack

- FastAPI - Web framework
- Instaloader - Instagram scraping
- Google Gemini API - Content generation
- Pillow - Image generation
- Transformers - Content classification
- Supabase - Database & storage
- Docker - Containerization

## Setup

See specs/ folder for detailed requirements, design, and implementation tasks.
