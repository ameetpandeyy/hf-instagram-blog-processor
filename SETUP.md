# Setup Guide - Instagram Blog Processor

## Prerequisites

- Python 3.11+
- Docker Desktop (for local testing)
- Google Gemini API Key (free tier: https://makersuite.google.com/app/apikey)
- Supabase Project (free tier: https://supabase.com)
- GitHub Account (for Actions)
- HuggingFace Account (for Spaces)

## Step 1: Local Development Setup

### 1.1 Clone Repository

```bash
git clone <your-repo-url>
cd hf-instagram-blog-processor
```

### 1.2 Create Environment File

```bash
cp .env.example .env
```

Edit .env with your credentials:

```bash
# Get from https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-gemini-key-here

# Get from Supabase project settings
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# Generate random secrets
WEBHOOK_SECRET=generate-random-string-here
CALLBACK_SECRET=generate-another-random-string

# Your Next.js app URL
CALLBACK_URL=https://your-app.vercel.app/api/callbacks/job-complete
```

### 1.3 Install Dependencies

```bash
# Option 1: pip
pip install -r requirements.txt

# Option 2: Poetry (recommended)
poetry install
```

### 1.4 Run Locally

```bash
# Direct
uvicorn app.main:app --reload --port 7860

# Or use Make
make run

# Or use Docker
make docker-build
make docker-run
```

Visit: http://localhost:7860/health

## Step 2: Test Locally

### 2.1 Test Health Endpoint

```bash
curl http://localhost:7860/health
```

Expected response:
```json
{
  "status": "healthy",
  "cpu_percent": 5.2,
  "memory_percent": 45.1,
  "disk_percent": 60.3
}
```

### 2.2 Test Webhook Endpoint

```bash
curl -X POST http://localhost:7860/webhook/process-job \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-webhook-secret" \
  -d '{
    "job_id": "test-123",
    "instagram_url": "https://instagram.com/reel/ABC123"
  }'
```

### 2.3 Run Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
make test
```

## Step 3: Deploy to HuggingFace Space

### 3.1 Create HuggingFace Space

1. Go to: https://huggingface.co/new-space
2. Fill in:
   - **Space name**: instagram-blog-processor
   - **License**: MIT
   - **Space SDK**: Docker
   - **Hardware**: GPU basic (free)
   - **Visibility**: Public

3. Click "Create Space"

### 3.2 Connect GitHub Repository

1. Push this repo to GitHub (must be public for free cron)
2. In HF Space settings ? "Repository"
3. Connect your GitHub repo
4. Set branch: main

### 3.3 Add Secrets in HF Space

Go to Space settings ? "Variables and secrets" ? "Add a new secret":

- GEMINI_API_KEY = your Gemini API key
- SUPABASE_URL = your Supabase URL
- SUPABASE_SERVICE_KEY = your service role key
- WEBHOOK_SECRET = random string (save this!)
- CALLBACK_URL = https://your-app.vercel.app/api/callbacks/job-complete
- CALLBACK_SECRET = random string (save this!)

### 3.4 Deploy

Push to GitHub:

```bash
git add .
git commit -m "Initial HF Space setup"
git push origin main
```

HF Space will auto-build. Check logs in Space interface.

## Step 4: Setup GitHub Actions (Unlimited Cron)

### 4.1 Add Repository Secrets

In your GitHub repo ? Settings ? Secrets and variables ? Actions:

- NEXT_JS_APP_URL = https://your-app.vercel.app
- CRON_SECRET = random string for auth

### 4.2 Enable GitHub Actions

- Go to Actions tab
- Enable workflows
- Workflow will run every 5 minutes

### 4.3 Test Manual Trigger

- Go to Actions ? "Process Instagram Queue"
- Click "Run workflow"
- Check run logs

## Step 5: Integrate with Next.js App

### 5.1 Add Environment Variables to Vercel

In your Next.js project:

```bash
# HuggingFace Space URL
HF_SPACE_URL=https://your-username-instagram-blog-processor.hf.space
HF_SPACE_WEBHOOK_SECRET=same-as-hf-space-webhook-secret

# For receiving callbacks
CALLBACK_SECRET=same-as-hf-space-callback-secret
```

### 5.2 Create API Route in Next.js

File: pp/api/cron/trigger-hf-space/route.ts

```typescript
export async function GET(request: Request) {
  // Get pending jobs from Supabase
  const { data: jobs } = await supabase
    .from('jobs')
    .select('*')
    .eq('status', 'pending')
    .limit(3);

  // Trigger HF Space for each job
  for (const job of jobs) {
    await fetch(\/webhook/process-job, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Webhook-Secret': process.env.HF_SPACE_WEBHOOK_SECRET!
      },
      body: JSON.stringify({
        job_id: job.id,
        instagram_url: job.payload.instagramUrl
      })
    });
  }

  return Response.json({ triggered: jobs.length });
}
```

### 5.3 Create Callback Route in Next.js

File: pp/api/callbacks/job-complete/route.ts

```typescript
export async function POST(request: Request) {
  const data = await request.json();
  
  // Verify HMAC signature
  // ... signature verification code ...

  // Create draft post in Supabase
  await supabase.from('posts').insert({
    title: data.post_data.title,
    slug: data.post_data.slug,
    body_md: data.post_data.body_markdown,
    status: 'draft',
    // ... other fields
  });

  // Update job status
  await supabase.from('jobs')
    .update({ status: 'completed' })
    .eq('id', data.job_id);

  return Response.json({ success: true });
}
```

## Step 6: Verify End-to-End Flow

### 6.1 Submit Test Job

In your Next.js admin panel:
1. Go to /admin/posts/new-from-instagram
2. Paste Instagram URL: https://instagram.com/reel/ABC123
3. Click "Queue Job"

### 6.2 Check Logs

**HF Space Logs** (in HF Space interface):
- Should show webhook received
- Processing steps
- Callback sent

**GitHub Actions** (in GitHub Actions tab):
- Cron run every 5 minutes
- Check trigger calls

**Supabase** (in Supabase dashboard):
- Check jobs table status updates
- Check posts table for new draft

### 6.3 Review Draft

In Next.js admin panel:
1. Go to /admin/posts
2. See new draft post
3. Review generated content
4. Check social card uploaded

## Troubleshooting

### Issue: "Invalid webhook secret"

**Solution**: Ensure WEBHOOK_SECRET matches in:
- HF Space secrets
- Next.js environment variables

### Issue: "Gemini API rate limit"

**Solution**: Gemini free tier = 15 RPM. Wait or upgrade.

### Issue: "Instagram scraping failed"

**Solution**: Instagram may block requests. Try:
- Use residential proxy
- Add delay between requests
- Fallback to manual caption input

### Issue: "GPU not available in HF Space"

**Solution**: Check Space hardware settings. May need to restart Space.

## Monitoring

### HF Space Health

```bash
curl https://your-space.hf.space/health
```

### Check Job Queue

Query Supabase:

```sql
SELECT status, COUNT(*) 
FROM jobs 
GROUP BY status;
```

### View Logs

- HF Space: Logs tab in Space interface
- GitHub Actions: Actions tab in repo
- Next.js: Vercel logs

## Next Steps

1. Process all 46 Instagram posts from CSV
2. Monitor success rate and quality
3. Optimize prompts for better content
4. Add more card templates
5. Implement analytics dashboard
