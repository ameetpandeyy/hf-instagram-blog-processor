# Next.js Integration Guide

## Your HuggingFace Space Details

- **Space URL**: https://ameetspeaks-templeappai.hf.space
- **Username**: ameetspeaks
- **Space Name**: templeappai

## Step 1: Add Environment Variables to Next.js

In your Next.js project (\c:\\Users\\ameet\\ameetpandey\), add to \.env.local\:

\\\ash
# HuggingFace Space Configuration
HF_SPACE_URL=https://ameetspeaks-templeappai.hf.space
HF_SPACE_WEBHOOK_SECRET=<same-secret-as-hf-space>

# For receiving callbacks from HF Space
CALLBACK_SECRET=<same-secret-as-hf-space>
\\\

Also add to **Vercel Environment Variables** (Production):
- \HF_SPACE_URL\
- \HF_SPACE_WEBHOOK_SECRET\
- \CALLBACK_SECRET\

## Step 2: Create API Route - Trigger HF Space

**File**: \src/app/api/cron/trigger-hf-space/route.ts\

\\\	ypescript
import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  try {
    // Verify cron secret
    const authHeader = request.headers.get('authorization');
    const token = authHeader?.replace('Bearer ', '');
    
    if (token !== process.env.CRON_SECRET) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get pending jobs from Supabase
    const supabase = await createClient();
    const { data: jobs, error } = await supabase
      .from('jobs')
      .select('*')
      .eq('type', 'instagram-to-blog')
      .eq('status', 'pending')
      .order('created_at', { ascending: true })
      .limit(3); // Process 3 jobs at a time

    if (error) {
      console.error('Error fetching jobs:', error);
      return NextResponse.json({ error: 'Failed to fetch jobs' }, { status: 500 });
    }

    if (!jobs || jobs.length === 0) {
      return NextResponse.json({ message: 'No pending jobs', triggered: 0 });
    }

    console.log(\Found \ pending jobs\);

    // Trigger HF Space for each job
    const results = await Promise.allSettled(
      jobs.map(async (job) => {
        const response = await fetch(
          \\/webhook/process-job\,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Webhook-Secret': process.env.HF_SPACE_WEBHOOK_SECRET!,
            },
            body: JSON.stringify({
              job_id: job.id,
              instagram_url: job.payload.instagramUrl,
            }),
          }
        );

        if (!response.ok) {
          throw new Error(\HF Space returned \\);
        }

        console.log(\? Triggered job \\);
        return job.id;
      })
    );

    const succeeded = results.filter((r) => r.status === 'fulfilled').length;
    const failed = results.filter((r) => r.status === 'rejected').length;

    return NextResponse.json({
      message: 'Jobs triggered',
      triggered: succeeded,
      failed: failed,
      total: jobs.length,
    });
  } catch (error) {
    console.error('Error in trigger-hf-space:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
\\\

## Step 3: Create API Route - Receive Callback

**File**: \src/app/api/callbacks/job-complete/route.ts\

\\\	ypescript
import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';
import crypto from 'crypto';

export async function POST(request: Request) {
  try {
    const data = await request.json();
    
    // TODO: Verify HMAC signature for security
    // const signature = request.headers.get('x-signature');
    // const expectedSignature = crypto
    //   .createHmac('sha256', process.env.CALLBACK_SECRET!)
    //   .update(JSON.stringify(data))
    //   .digest('hex');
    // if (signature !== expectedSignature) {
    //   return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
    // }

    console.log(\Received callback for job \\, data.status);

    const supabase = await createClient();

    if (data.status === 'completed') {
      // Create draft post in database
      const { data: post, error: postError } = await supabase
        .from('posts')
        .insert({
          title: data.post_data.title,
          slug: data.post_data.slug,
          body_md: data.post_data.body_markdown,
          meta_description: data.post_data.meta_description,
          primary_keyword: data.post_data.keywords[0] || null,
          secondary_keywords: data.post_data.keywords.slice(1, 6) || [],
          read_minutes: data.post_data.read_minutes || 5,
          status: 'draft',
          instagram_url: data.post_data.instagram_url,
          youtube_links: data.post_data.youtube_links || [],
          content_type: data.post_data.content_type,
          affiliate_links: data.post_data.affiliate_links || [],
          needs_finalization: (data.post_data.affiliate_links?.length || 0) > 0,
          social_card_id: data.post_data.social_card_id || null,
        })
        .select()
        .single();

      if (postError) {
        console.error('Error creating post:', postError);
        throw postError;
      }

      console.log(\? Created draft post: \\);

      // Update job status to completed
      await supabase
        .from('jobs')
        .update({
          status: 'completed',
          result: { post_id: post.id },
          updated_at: new Date().toISOString(),
        })
        .eq('id', data.job_id);

      return NextResponse.json({
        success: true,
        post_id: post.id,
      });
    } else if (data.status === 'failed') {
      // Update job status to failed
      await supabase
        .from('jobs')
        .update({
          status: 'failed',
          error: data.error,
          updated_at: new Date().toISOString(),
        })
        .eq('id', data.job_id);

      return NextResponse.json({
        success: true,
        message: 'Job marked as failed',
      });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error in job-complete callback:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
\\\

## Step 4: Test the Integration

### Test 1: Health Check HF Space

\\\ash
curl https://ameetspeaks-templeappai.hf.space/health
\\\

Expected response:
\\\json
{
  "status": "healthy",
  "cpu_percent": 5.2,
  "memory_percent": 45.1,
  "disk_percent": 60.3
}
\\\

### Test 2: Manually Trigger Cron

\\\ash
curl -X GET 'http://localhost:3000/api/cron/trigger-hf-space' \\
  -H 'Authorization: Bearer your-cron-secret'
\\\

### Test 3: Submit Instagram URL

In your admin panel:
1. Go to \/admin/posts/new-from-instagram\
2. Paste: \https://instagram.com/reel/ABC123\
3. Click "Queue Job"
4. Check job status in \/admin/posts\

## Step 5: Update Database Schema

Run this migration in Supabase SQL Editor:

\\\sql
-- Add new columns to posts table (if not already added)
ALTER TABLE posts 
ADD COLUMN IF NOT EXISTS instagram_url TEXT,
ADD COLUMN IF NOT EXISTS youtube_links TEXT[],
ADD COLUMN IF NOT EXISTS content_type TEXT,
ADD COLUMN IF NOT EXISTS affiliate_links JSONB,
ADD COLUMN IF NOT EXISTS needs_finalization BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS social_card_id UUID REFERENCES cards(id);

-- Create index for finalization filtering
CREATE INDEX IF NOT EXISTS idx_posts_needs_finalization 
ON posts(needs_finalization) 
WHERE needs_finalization = TRUE;
\\\

## Step 6: GitHub Actions Secrets

In your **public GitHub repo** for HF Space, add these secrets:

### Repository Secrets (Settings ? Secrets and variables ? Actions)

1. **HF_TOKEN**
   - Get from: https://huggingface.co/settings/tokens
   - Type: Write access
   - Used by: \sync-to-hf.yml\ workflow

2. **NEXTJS_APP_URL**
   - Value: \https://ameetpandey.com\
   - Used by: \process-queue.yml\ workflow

3. **CRON_SECRET**
   - Value: Random secure string (same as in Next.js \.env.local\)
   - Used by: \process-queue.yml\ workflow

## Step 7: Verify Auto-Sync

1. Push code to GitHub:
   \\\ash
   git add .
   git commit -m "Setup HF Space integration"
   git push origin main
   \\\

2. Check GitHub Actions tab - should see:
   - ? "Sync to HuggingFace Space" workflow running
   - ? "Process Instagram Queue" scheduled (every 5 min)

3. Check HF Space:
   - Go to https://huggingface.co/spaces/ameetspeaks/templeappai
   - Should see your code synced
   - Check "Logs" tab for startup messages

## Troubleshooting

### Issue: HF Space not syncing

**Solution**: Check GitHub Actions logs. Ensure \HF_TOKEN\ has write access.

### Issue: "Invalid webhook secret"

**Solution**: Ensure \HF_SPACE_WEBHOOK_SECRET\ matches in:
- HF Space secrets
- Next.js \.env.local\
- Vercel environment variables

### Issue: Callback not received

**Solution**: Check HF Space logs. Ensure \CALLBACK_URL\ is correct and accessible.

### Issue: Jobs stay in "pending" status

**Solution**:
1. Check GitHub Actions cron is running
2. Check Next.js API route is accessible
3. Check HF Space webhook endpoint responds

## Next Steps

1. ? Verify HF Space is running: https://ameetspeaks-templeappai.hf.space/health
2. ? Verify GitHub Actions sync is working
3. ? Test cron trigger manually
4. ? Submit test Instagram URL
5. ? Monitor job processing
6. ?? Process your 46 Instagram posts!
