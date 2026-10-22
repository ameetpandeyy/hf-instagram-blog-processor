# Next.js Integration Guide

This document explains how to integrate the HuggingFace Space with your Next.js application.

## Overview

The Next.js app triggers the HF Space via webhooks and receives results via callbacks.

## Required API Routes in Next.js

### 1. Trigger HF Space (called by GitHub Actions)

File: 'src/app/api/cron/trigger-hf-space/route.ts'

### 2. Receive Callback (called by HF Space)

File: 'src/app/api/callbacks/job-complete/route.ts'

### 3. Admin UI for URL Submission

File: 'src/app/admin/(protected)/posts/new-from-instagram/page.tsx'

See SETUP.md for detailed implementation examples.
