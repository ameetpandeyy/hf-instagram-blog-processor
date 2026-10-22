# GitHub Secrets Setup Guide

## Required Secrets for Workflows

Your GitHub repository needs 3 secrets for automation to work:

### 1. HF_TOKEN (for sync-to-hf.yml)
**Purpose**: Pushes code to HuggingFace Space

**How to get**:
1. Go to: https://huggingface.co/settings/tokens
2. Click **"New token"**
3. Name: \GitHub Actions Sync\
4. Type: **Write** (important!)
5. Click **"Generate a token"**
6. **Copy the token** (you won't see it again!)

**How to add**:
1. Go to your GitHub repo
2. Settings ? Secrets and variables ? Actions
3. Click **"New repository secret"**
4. Name: \HF_TOKEN\
5. Secret: Paste your HuggingFace token
6. Click **"Add secret"**

### 2. NEXTJS_APP_URL (for process-queue.yml)
**Purpose**: Tells GitHub Actions where your Next.js app is

**Value**: Your production URL (e.g., \https://ameetpandey.com\)

**How to add**:
1. Go to your GitHub repo
2. Settings ? Secrets and variables ? Actions
3. Click **"New repository secret"**
4. Name: \NEXTJS_APP_URL\
5. Secret: \https://ameetpandey.com\ (your actual URL)
6. Click **"Add secret"**

### 3. CRON_SECRET (for process-queue.yml)
**Purpose**: Authenticates cron requests to your Next.js API

**How to generate**:
\\\ash
# On Windows PowerShell:
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# On Mac/Linux:
openssl rand -hex 32

# Or use any random string generator
\\\

**How to add**:
1. Generate random string (save it for later!)
2. Go to your GitHub repo
3. Settings ? Secrets and variables ? Actions
4. Click **"New repository secret"**
5. Name: \CRON_SECRET\
6. Secret: Paste the random string
7. Click **"Add secret"**

**Important**: Use the SAME value in:
- GitHub secret: \CRON_SECRET\
- Next.js \.env.local\: \CRON_SECRET\
- Vercel environment variable: \CRON_SECRET\

## Current Status

Check which secrets are configured:

1. Go to: https://github.com/<your-username>/<your-repo>/settings/secrets/actions
2. You should see:
   - ? HF_TOKEN
   - ? NEXTJS_APP_URL
   - ? CRON_SECRET

## Verify Workflows

After adding secrets:

### Test Sync Workflow
\\\ash
# Make any commit
git commit --allow-empty -m "Test sync workflow"
git push origin main

# Check: GitHub repo ? Actions ? "Sync to HuggingFace Space"
# Should show ? green checkmark
\\\

### Test Cron Workflow
\\\ash
# Manual trigger
# Go to: GitHub repo ? Actions ? "Process Instagram Queue" ? Run workflow

# Or wait 5 minutes for automatic run
\\\

## Troubleshooting

### Sync workflow fails with "Authentication failed"
**Solution**: Check that \HF_TOKEN\ has **Write** permission (not just Read)

### Cron workflow shows "URL rejected: No host part"
**Solution**: Add \NEXTJS_APP_URL\ secret with full URL including \https://\

### Cron shows "401 Unauthorized"
**Solution**: Ensure \CRON_SECRET\ matches in GitHub and Next.js

## Next Steps

Once secrets are configured:

1. ? Workflows run without errors
2. ? Code auto-syncs to HF Space on every push
3. ? Cron checks for jobs every 5 minutes
4. ?? Create Next.js API route: \/api/cron/trigger-hf-space\
5. ?? Implement Python services
6. ?? Test end-to-end flow
