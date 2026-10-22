# GitHub Actions Troubleshooting Guide

## Issue: Authentication Failed for HuggingFace

**Error:**
\\\
Password authentication in git is no longer supported. 
You must use a user access token or an SSH key instead.
fatal: Authentication failed for 'https://huggingface.co/spaces/...'
Error: Process completed with exit code 128.
\\\

**Solution:** ? Already fixed in the workflow!

### What Was Fixed:

The workflow now correctly embeds the HF_TOKEN in the git remote URL:

\\\yaml
git remote add space https://ameetspeaks:$HF_TOKEN@huggingface.co/spaces/ameetspeaks/templeappai
\\\

This uses the token for authentication instead of password.

---

## Required GitHub Secret: HF_TOKEN

### Step 1: Get Your HuggingFace Token

1. Go to: https://huggingface.co/settings/tokens
2. Click **"New token"**
3. Settings:
   - Name: \GitHub Actions Sync\
   - Type: **Write** (important!)
   - Repositories: Optional (leave empty for all)
4. Click **"Generate a token"**
5. **Copy the token** (you won't see it again!)

### Step 2: Add to GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** ? **Secrets and variables** ? **Actions**
3. Click **"New repository secret"**
4. Name: \HF_TOKEN\
5. Secret: Paste your HuggingFace token
6. Click **"Add secret"**

### Step 3: Verify It Works

1. Push the fixed workflow:
   \\\ash
   cd c:\\Users\\ameet\\ameetpandey\\hf-instagram-blog-processor
   git add .github/workflows/sync-to-hf.yml
   git commit -m "Fix HF authentication"
   git push origin main
   \\\

2. Check GitHub Actions tab
   - Should see "Sync to HuggingFace Space" running
   - Should complete successfully (green checkmark)

3. Check HuggingFace Space
   - Go to: https://huggingface.co/spaces/ameetspeaks/templeappai
   - Should see your code
   - Check "Logs" tab for build progress

---

## Common Issues & Solutions

### Issue: "HF_TOKEN secret not found"

**Solution:** Ensure you added the secret with exact name \HF_TOKEN\ (case-sensitive)

### Issue: "Permission denied (publickey)"

**Solution:** You're using SSH. Change to HTTPS with token (already done in workflow)

### Issue: Token expired

**Solution:** 
- HF tokens don't expire by default
- If you set expiry, generate a new token
- Update GitHub secret with new token

### Issue: Workflow runs but doesn't sync

**Solution:**
1. Check GitHub Actions logs for errors
2. Verify HF_TOKEN has **Write** permission (not just Read)
3. Ensure Space name is correct: \meetspeaks/templeappai\

### Issue: "Space not found"

**Solution:**
- Verify your Space exists: https://huggingface.co/spaces/ameetspeaks/templeappai
- Check spelling in workflow (username and space name are case-sensitive)

---

## Manual Sync (Alternative)

If GitHub Actions doesn't work, you can sync manually:

\\\ash
cd c:\\Users\\ameet\\ameetpandey\\hf-instagram-blog-processor

# Add HF Space as remote (replace YOUR_TOKEN with actual token)
git remote add hf https://ameetspeaks:YOUR_TOKEN@huggingface.co/spaces/ameetspeaks/templeappai

# Push to HF Space
git push hf main:main --force
\\\

---

## Verify Sync is Working

### Check 1: GitHub Actions

Go to: https://github.com/<your-username>/<your-repo>/actions

You should see:
- ? "Sync to HuggingFace Space" - Success
- Recent run triggered by your push

### Check 2: HuggingFace Space

Go to: https://huggingface.co/spaces/ameetspeaks/templeappai

You should see:
- Your code files
- "Building" or "Running" status
- Build logs in "Logs" tab

### Check 3: Health Endpoint

After build completes (3-5 minutes):

\\\ash
curl https://ameetspeaks-templeappai.hf.space/health
\\\

Should return:
\\\json
{
  "status": "healthy",
  "cpu_percent": 5.2,
  "memory_percent": 45.1,
  "disk_percent": 60.3
}
\\\

---

## Next Steps After Sync Works

1. ? HF Space is syncing from GitHub
2. ? Space is building and running
3. ?? Implement service functions (see specs/tasks.md)
4. ?? Create Next.js API routes (see specs/NEXTJS_INTEGRATION.md)
5. ?? Test with Instagram URL
6. ?? Process your 46 posts!

---

## Still Having Issues?

### Debug Checklist:

- [ ] HF token has **Write** permission (not Read)
- [ ] GitHub secret is named exactly \HF_TOKEN\
- [ ] Space name is correct: \meetspeaks/templeappai\
- [ ] Workflow file is in \.github/workflows/sync-to-hf.yml\
- [ ] Pushed workflow file to main branch
- [ ] GitHub Actions is enabled in repo settings

### Get Help:

- HF Spaces Docs: https://huggingface.co/docs/hub/spaces
- HF Token Docs: https://huggingface.co/docs/hub/security-tokens
- GitHub Actions Docs: https://docs.github.com/en/actions

---

## Success!

Once you see:
- ? GitHub Action completes successfully
- ? HF Space shows "Running"
- ? Health endpoint responds

**You're ready to start implementing the service functions!**

Next: Read \specs/tasks.md\ for implementation checklist.
