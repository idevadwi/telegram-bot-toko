# Phase 7: CI/CD with GitHub Actions for Telegram Bot Toko

## Overview

This guide provides step-by-step instructions for setting up automated CI/CD deployment for the **Telegram Bot Toko** using GitHub Actions. When you push code to the `main` branch, GitHub Actions will automatically deploy your changes to your VPS using Docker.

**What This CI/CD Does:**
- Automatically deploys on every push to the `main` branch
- Pulls latest code from GitHub to your VPS
- Updates environment variables from GitHub Secrets
- Rebuilds Docker image with no cache
- Restarts the bot container
- Provides manual triggers for sync and restart operations
- Shows deployment logs for verification

**Prerequisites:**
- ✅ Completed Phase 1 (Initial Server Setup with SSH keys)
- ✅ Completed Phase 3 (Docker & Docker Compose installed)
- ✅ Completed Phase 5 (PostgreSQL database setup)
- ✅ Completed Phase 6 (Application environment configured)
- ✅ GitHub repository for telegram-bot-toko
- ✅ VPS with project at `~/apps/telegram-bot-toko/`

---

## CI/CD Architecture

```
┌──────────────────┐         ┌─────────────────────────┐         ┌──────────────────┐
│   Developer      │         │   GitHub Repository     │         │  GitHub Actions  │
│   Local Machine  │────────▶│   telegram-bot-toko     │────────▶│    Workflow      │
│                  │  Push   │                         │ Trigger │                  │
└──────────────────┘         └─────────────────────────┘         └──────────────────┘
                                                                           │
                                                                           │ SSH Deploy
                                                                           ▼
                                                                  ┌──────────────────┐
                                                                  │   VPS Server     │
                                                                  │  deploy@vps-ip   │
                                                                  └──────────────────┘
                                                                           │
                                         ┌─────────────────────────────────┼─────────────────┐
                                         ▼                                 ▼                 ▼
                                    Git Pull                      Update .env        Build & Restart
                                    ~/apps/telegram-bot-toko      from Secrets       Docker Container
                                         │                                 │                 │
                                         └─────────────────────────────────┴─────────────────┘
                                                                           │
                                                                           ▼
                                                              ┌─────────────────────────┐
                                                              │  🤖 Bot Running         │
                                                              │  telegram-bot-toko      │
                                                              │  Container              │
                                                              └─────────────────────────┘
```

---

## Part A: SSH Key Setup for GitHub Actions

### Step 1: Generate Deployment SSH Key on VPS

SSH into your VPS as the `deploy` user and create a dedicated SSH key for GitHub Actions:

```bash
# SSH into your VPS
ssh deploy@your-vps-ip

# Navigate to SSH directory
cd ~/.ssh

# Generate deployment key (Ed25519 is recommended for security and performance)
ssh-keygen -t ed25519 -C "github-actions-telegram-bot" -f github_deploy_key

# Press Enter to skip passphrase (required for automated deployments)
```

This creates two files:
- `github_deploy_key` - Private key (will be added to GitHub Secrets)
- `github_deploy_key.pub` - Public key (will be added to VPS)

---

### Step 2: Add Public Key to VPS Authorized Keys

```bash
# Add public key to authorized_keys
cat github_deploy_key.pub >> ~/.ssh/authorized_keys

# Set proper permissions
chmod 600 ~/.ssh/authorized_keys
chmod 600 github_deploy_key
chmod 644 github_deploy_key.pub

# Verify the key was added
tail -1 ~/.ssh/authorized_keys
```

---

### Step 3: Copy Private Key for GitHub Secrets

Display and copy the entire private key:

```bash
# Display private key
cat github_deploy_key
```

**Copy the entire output**, including the BEGIN and END lines:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtz
... (many lines of key content) ...
AAAAB3NzaC1yc2EAAAABIwAAAQEA...
-----END OPENSSH PRIVATE KEY-----
```

**Security Note:** This private key is sensitive. Store it securely in GitHub Secrets only. Never commit it to your repository or share it publicly.

---

### Step 4: Test SSH Key Connection

Before proceeding, verify the SSH key works:

```bash
# Test connection (on your VPS)
ssh -i ~/.ssh/github_deploy_key deva@localhost "echo 'SSH connection successful'"

# Expected output: SSH connection successful
```

---

## Part B: Configure GitHub Secrets

GitHub Secrets securely store sensitive information like SSH keys, API tokens, and passwords.

### Step 1: Navigate to GitHub Secrets

1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/telegram-bot-toko`
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** button

---

### Step 2: Add Required Secrets

Add these 9 secrets one by one. Click **New repository secret** for each:

| Secret Name | Value | Where to Get It |
|------------|-------|-----------------|
| **VPS_HOST** | Your VPS IP address (e.g., `123.45.67.89`) | VPS provider dashboard |
| **VPS_USERNAME** | `deploy` | The SSH user you created in Phase 1 |
| **VPS_SSH_KEY** | Private key content from Step 3 above | Output of `cat ~/.ssh/github_deploy_key` |
| **TELEGRAM_BOT_TOKEN** | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` | Get from [@BotFather](https://t.me/BotFather) on Telegram |
| **DROPBOX_APP_KEY** | Your Dropbox app key | [Dropbox Developer Console](https://www.dropbox.com/developers/apps) |
| **DROPBOX_APP_SECRET** | Your Dropbox app secret | Dropbox Developer Console |
| **DROPBOX_REFRESH_TOKEN** | Your Dropbox refresh token | Generate using Dropbox OAuth flow |
| **DB_PASSWORD** | PostgreSQL password | The password you set in Phase 5 |
| **ALLOWED_USERS** | `123456789,987654321` | Comma-separated Telegram user IDs (get from `/start` command) |

---

### Step 3: Verify All Secrets Are Added

After adding all secrets, you should see 9 secrets listed:

```
✅ VPS_HOST
✅ VPS_USERNAME
✅ VPS_SSH_KEY
✅ TELEGRAM_BOT_TOKEN
✅ DROPBOX_APP_KEY
✅ DROPBOX_APP_SECRET
✅ DROPBOX_REFRESH_TOKEN
✅ DB_PASSWORD
✅ ALLOWED_USERS
```

**Important Notes:**
- Secret values are hidden after creation (you can update but not view them)
- Secrets are encrypted and only accessible during workflow execution
- Never log or print secret values in your workflow
- Rotate secrets every 3 months for security

---

## Part C: GitHub Actions Workflow File

The workflow file has already been created at:
```
.github/workflows/deploy-telegram-bot-toko.yml
```

### Workflow Features

**Triggers:**
1. **Automatic:** Triggers on every push to `main` branch
2. **Manual:** Can be triggered manually from GitHub Actions UI with options:
   - `deploy` - Full deployment (pull code, rebuild, restart)
   - `sync` - Run data sync from Dropbox
   - `restart` - Simply restart the container

**Jobs:**
1. **deploy** - Main deployment job
   - Pulls latest code from GitHub
   - Updates `.env` file with secrets
   - Rebuilds Docker image (no cache)
   - Restarts container
   - Shows logs for verification

2. **sync** - Manual data sync job
   - Runs the sync script to update product data from Dropbox
   - Can be triggered manually when you need to refresh data

3. **restart** - Manual restart job
   - Simply restarts the bot container
   - Useful for quick restarts without full deployment

---

## Part D: How the CI/CD Workflow Works

### Automatic Deployment Flow (Push to Main)

```
1. You commit code locally:
   git add .
   git commit -m "feat: add new feature"
   git push origin main

2. GitHub detects push to main branch
   → Triggers the workflow automatically

3. GitHub Actions runner starts:
   → Checks out code (for workflow context)
   → Sets up SSH agent with your private key
   → Adds VPS to known_hosts (security)

4. SSH into VPS and execute deployment:
   → cd ~/apps/telegram-bot-toko
   → git pull origin main (get latest code)
   → Update config/.env with secrets from GitHub
   → cd docker
   → docker compose build --no-cache (rebuild image)
   → docker compose up -d (restart container)
   → docker compose logs (show verification logs)

5. Deployment complete:
   → Bot is now running with your latest code
   → Check GitHub Actions tab for green checkmark ✅
   → Test bot on Telegram to verify changes
```

### Manual Trigger Flow

```
1. Go to GitHub repository → Actions tab

2. Click "Deploy Telegram Bot Toko" workflow

3. Click "Run workflow" button

4. Select action from dropdown:
   - deploy: Full deployment
   - sync: Run data sync
   - restart: Restart container

5. Click "Run workflow" (green button)

6. Watch workflow execution in real-time

7. Verify completion (green checkmark)
```

---

## Part E: Testing Your CI/CD Pipeline

### Initial Deployment Test

After setting up all secrets and creating the workflow file:

1. **Make a small test change:**
   ```bash
   # On your local machine
   cd telegram-bot-toko

   # Edit README.md or add a comment to any file
   echo "# CI/CD test" >> README.md

   # Commit and push
   git add README.md
   git commit -m "test: verify CI/CD deployment"
   git push origin main
   ```

2. **Watch GitHub Actions:**
   - Go to your repository on GitHub
   - Click the **Actions** tab
   - You should see a workflow running with your commit message
   - Click on it to watch real-time logs

3. **Verify on VPS:**
   ```bash
   # SSH to your VPS
   ssh deploy@your-vps-ip

   # Check if code was updated
   cd ~/apps/telegram-bot-toko
   git log -1  # Should show your latest commit

   # Check container status
   cd docker
   docker compose ps  # Should show "Up" status

   # Check logs
   docker compose logs --tail=50 bot
   ```

4. **Test bot on Telegram:**
   - Open Telegram
   - Send `/start` to your bot
   - Verify it responds correctly

---

### Manual Trigger Test

Test the manual sync trigger:

1. **Navigate to Actions tab:**
   - Go to GitHub repository → Actions
   - Click "Deploy Telegram Bot Toko" workflow

2. **Run manual sync:**
   - Click "Run workflow" button (right side)
   - Branch: `main`
   - Action: `sync`
   - Click green "Run workflow" button

3. **Watch execution:**
   - Workflow will appear in the list
   - Click to see live logs
   - Wait for completion (green checkmark)

4. **Verify sync completed:**
   ```bash
   ssh deploy@your-vps-ip
   cd ~/apps/telegram-bot-toko/docker
   docker compose logs --tail=100 bot | grep -i sync
   ```

---

## Part F: Verification Checklist

Use this checklist to ensure everything is set up correctly:

### Initial Setup
- [ ] SSH key generated on VPS (`~/.ssh/github_deploy_key`)
- [ ] Public key added to `~/.ssh/authorized_keys`
- [ ] SSH key connection tested successfully
- [ ] All 9 GitHub Secrets configured
- [ ] Workflow file exists at `.github/workflows/deploy-telegram-bot-toko.yml`
- [ ] VPS has project at `~/apps/telegram-bot-toko/`
- [ ] Git is configured on VPS with GitHub access

### First Deployment
- [ ] Made test commit and pushed to main
- [ ] GitHub Actions workflow triggered automatically
- [ ] Workflow completed successfully (green checkmark)
- [ ] Latest code pulled to VPS (verified with `git log`)
- [ ] Docker container rebuilt (checked with `docker images`)
- [ ] Container running (verified with `docker compose ps`)
- [ ] Bot responds on Telegram

### Manual Triggers
- [ ] Manual "sync" trigger works
- [ ] Manual "restart" trigger works
- [ ] Manual "deploy" trigger works

### Post-Deployment
- [ ] Bot functionality tested on Telegram
- [ ] Database queries working (search for products)
- [ ] Logs show no errors
- [ ] Environment variables loaded correctly

---

## Part G: Troubleshooting Common Issues

### Issue 1: SSH Connection Failed

**Symptoms:**
```
Permission denied (publickey)
```

**Solutions:**

1. **Verify SSH key in GitHub Secrets:**
   ```bash
   # On VPS, display the private key
   cat ~/.ssh/github_deploy_key
   ```
   - Copy the entire output including BEGIN/END lines
   - Update `VPS_SSH_KEY` secret in GitHub with this value

2. **Check authorized_keys:**
   ```bash
   # Verify public key is in authorized_keys
   grep "github-actions-telegram-bot" ~/.ssh/authorized_keys

   # If not found, add it again
   cat ~/.ssh/github_deploy_key.pub >> ~/.ssh/authorized_keys
   ```

3. **Verify permissions:**
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/github_deploy_key
   ```

---

### Issue 2: Git Pull Fails

**Symptoms:**
```
error: Your local changes to the following files would be overwritten by merge
```

**Solutions:**

1. **SSH to VPS and check git status:**
   ```bash
   ssh deploy@your-vps-ip
   cd ~/apps/telegram-bot-toko
   git status
   ```

2. **Stash or discard local changes:**
   ```bash
   # Option 1: Stash changes (save for later)
   git stash

   # Option 2: Discard changes (permanent)
   git reset --hard HEAD

   # Then try pulling again
   git pull origin main
   ```

---

### Issue 3: Docker Build Fails

**Symptoms:**
```
ERROR [internal] load metadata for docker.io/library/python:3.11-slim
```

**Solutions:**

1. **Check Docker daemon:**
   ```bash
   ssh deploy@your-vps-ip
   sudo systemctl status docker

   # If not running, start it
   sudo systemctl start docker
   ```

2. **Check disk space:**
   ```bash
   df -h

   # If disk is full, clean up old images
   docker system prune -a --volumes
   ```

3. **Pull base image manually:**
   ```bash
   docker pull python:3.11-slim
   ```

---

### Issue 4: Container Not Starting

**Symptoms:**
```
Container telegram-bot-toko exited with code 1
```

**Solutions:**

1. **Check container logs:**
   ```bash
   ssh deploy@your-vps-ip
   cd ~/apps/telegram-bot-toko/docker
   docker compose logs bot
   ```

2. **Common causes and fixes:**

   **a) Database connection error:**
   ```bash
   # Check if PostgreSQL is running
   docker compose ps postgresql-server

   # Check database credentials in .env
   cat ../config/.env | grep DB_
   ```

   **b) Missing environment variables:**
   ```bash
   # Verify all required variables exist
   cat ../config/.env

   # Compare with .env.example
   cat ../config/.env.example
   ```

   **c) Telegram token invalid:**
   ```bash
   # Test token manually
   curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

   # If invalid, get new token from @BotFather
   # Update GitHub Secret TELEGRAM_BOT_TOKEN
   # Redeploy
   ```

---

### Issue 5: Environment Variables Not Updating

**Symptoms:**
Bot still using old configuration after deployment.

**Solutions:**

1. **Check if .env file was updated:**
   ```bash
   ssh deploy@your-vps-ip
   cd ~/apps/telegram-bot-toko/config
   cat .env
   # Compare values with GitHub Secrets
   ```

2. **Manually update .env and restart:**
   ```bash
   # Edit .env file
   nano config/.env

   # Restart container
   cd docker
   docker compose restart bot
   ```

3. **Verify secrets in GitHub:**
   - Go to repository → Settings → Secrets
   - Ensure all 9 secrets are present
   - Update any that are incorrect
   - Trigger manual deployment

---

### Issue 6: Workflow Fails with "Host key verification failed"

**Symptoms:**
```
Host key verification failed
```

**Solutions:**

This is handled automatically by the workflow, but if it fails:

1. **Manually add VPS to known_hosts (on your local machine):**
   ```bash
   ssh-keyscan -H your-vps-ip >> ~/.ssh/known_hosts
   ```

2. **Or SSH once to accept the key:**
   ```bash
   ssh deploy@your-vps-ip
   # Type 'yes' when prompted
   ```

---

### Issue 7: Secrets Contain Special Characters

**Symptoms:**
Environment variables with `$`, `"`, or other special characters cause issues.

**Solutions:**

When adding secrets to GitHub:
- No need to escape special characters
- GitHub Secrets handle special characters automatically
- Don't wrap values in quotes when adding to GitHub Secrets

If issues persist:
1. Test the secret value manually on VPS
2. Verify no extra spaces or newlines were added
3. Regenerate the token/password if needed

---

## Part H: Security Best Practices

### 1. SSH Key Rotation

Rotate your deployment SSH key every 3 months:

```bash
# Generate new key
cd ~/.ssh
ssh-keygen -t ed25519 -C "github-actions-telegram-bot-$(date +%Y%m)" -f github_deploy_key_new

# Add new public key
cat github_deploy_key_new.pub >> authorized_keys

# Update GitHub Secret VPS_SSH_KEY with new private key content
cat github_deploy_key_new

# Test new key works
# Then remove old key from authorized_keys
nano authorized_keys  # Delete old key line
```

**Set a reminder:** Add calendar event every 3 months to rotate keys.

---

### 2. Limit SSH Key Permissions (Optional Advanced)

For maximum security, restrict what the deployment key can do:

```bash
# Create restricted deployment script
nano ~/scripts/deploy-telegram-bot.sh
```

Add:
```bash
#!/bin/bash
case "$SSH_ORIGINAL_COMMAND" in
  "cd ~/apps/telegram-bot-toko"*|"git pull"*|"docker compose"*)
    eval "$SSH_ORIGINAL_COMMAND"
    ;;
  *)
    echo "Command not allowed for deployment key"
    exit 1
    ;;
esac
```

Make executable:
```bash
chmod +x ~/scripts/deploy-telegram-bot.sh
```

Edit authorized_keys:
```bash
nano ~/.ssh/authorized_keys
```

Prepend to the deployment key line:
```
command="~/scripts/deploy-telegram-bot.sh",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-ed25519 AAAA...
```

---

### 3. Enable Branch Protection (Recommended)

Prevent accidental deployments:

1. Go to repository → Settings → Branches
2. Add branch protection rule for `main`:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date
3. Save changes

Now you must create PRs and get reviews before deploying to main.

---

### 4. Monitor GitHub Actions Usage

Check your Actions usage:
1. Go to repository → Settings → Billing
2. Monitor minutes used (GitHub provides free minutes)
3. Set up spending limits if needed

---

### 5. Audit Deployment Logs

Keep track of deployments:

```bash
# On VPS, view deployment history
cd ~/apps/telegram-bot-toko
git log --oneline --graph --all -20

# Check container restart history
docker compose logs --since 7d telegram-bot-toko | grep "Starting"
```

---

## Part I: Rollback Procedures

If a deployment introduces bugs or breaks functionality:

### Option 1: Quick Rollback via Git

```bash
# SSH to VPS
ssh deploy@your-vps-ip

# Navigate to project
cd ~/apps/telegram-bot-toko

# View recent commits
git log --oneline -10

# Find the last working commit hash (e.g., abc1234)
# Rollback to that commit
git checkout abc1234

# Rebuild and restart
cd docker
docker compose build --no-cache
docker compose up -d

# Verify
docker compose logs -f bot
```

---

### Option 2: Revert Commit and Redeploy

```bash
# On your local machine
cd telegram-bot-toko

# Find the bad commit
git log --oneline -10

# Revert the commit (creates new commit that undoes changes)
git revert <bad-commit-hash>

# Push to trigger automatic deployment
git push origin main
```

---

### Option 3: Manual Trigger Previous Version

1. Create a new branch from the last working commit:
   ```bash
   git checkout -b rollback-temp <last-working-commit-hash>
   git push origin rollback-temp
   ```

2. Update the workflow to deploy from `rollback-temp`
3. Trigger manual deployment
4. Fix the issue, then merge back to main

---

## Part J: Advanced Features

### Adding Deployment Notifications (Optional)

Get notified on deployments via Telegram:

1. **Create notification script on VPS:**
   ```bash
   nano ~/scripts/notify-deployment.sh
   ```

   ```bash
   #!/bin/bash
   BOT_TOKEN="your-notification-bot-token"
   CHAT_ID="your-chat-id"
   MESSAGE="🚀 Deployment completed for telegram-bot-toko at $(date)"

   curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
     -d chat_id="$CHAT_ID" \
     -d text="$MESSAGE"
   ```

   ```bash
   chmod +x ~/scripts/notify-deployment.sh
   ```

2. **Add to workflow (in deploy-telegram-bot-toko.yml):**
   ```yaml
   - name: Send notification
     run: |
       ssh ${{ secrets.VPS_USERNAME }}@${{ secrets.VPS_HOST }} \
         "~/scripts/notify-deployment.sh"
   ```

---

### Scheduled Data Sync

Automatically sync data from Dropbox daily:

1. **Add cron job on VPS:**
   ```bash
   crontab -e
   ```

   Add:
   ```
   # Sync data from Dropbox every day at 3 AM
   0 3 * * * cd ~/apps/telegram-bot-toko/docker && docker compose exec -T bot python -m scripts.sync >> ~/logs/sync.log 2>&1
   ```

---

## Part K: Post-Implementation Workflow

Your typical development workflow will now be:

```
1. Make changes locally:
   - Edit code in src/
   - Test locally with: make dev
   - Commit changes: git commit -m "feat: description"

2. Push to GitHub:
   - git push origin main

3. Automatic deployment:
   - GitHub Actions triggers automatically
   - Watch progress in Actions tab
   - Deployment completes in 2-3 minutes

4. Verify on Telegram:
   - Test bot functionality
   - Verify changes are live
   - Check logs if needed

5. Monitor:
   - Check GitHub Actions for status
   - View VPS logs if issues arise
   - Use manual triggers for sync/restart
```

---

## Part L: Monitoring Deployments

### View Deployment History

**On GitHub:**
1. Go to repository → Actions tab
2. See all workflow runs with status
3. Click any run to see detailed logs
4. Download logs for debugging

**On VPS:**
```bash
# View recent deployments via git
ssh deploy@your-vps-ip
cd ~/apps/telegram-bot-toko
git log --oneline --graph --all -20

# View Docker container history
cd docker
docker compose logs --since 24h telegram-bot-toko

# Check container uptime
docker ps | grep telegram-bot-toko
```

---

### Set Up Alerts (Optional)

Use GitHub's built-in notifications:
1. Go to repository → Settings → Notifications
2. Enable email notifications for:
   - ✅ Failed workflow runs
   - ✅ Deployment failures

You'll receive emails if deployments fail.

---

## Success Criteria

Your CI/CD is successfully set up when:

- ✅ All 9 GitHub Secrets are configured
- ✅ SSH key works for automated deployment
- ✅ Pushing to main triggers automatic deployment
- ✅ Deployment completes successfully (green checkmark)
- ✅ Latest code is pulled to VPS
- ✅ Docker image is rebuilt
- ✅ Container restarts automatically
- ✅ Bot is functional on Telegram after deployment
- ✅ Manual triggers work (sync, restart, deploy)
- ✅ You can rollback if needed
- ✅ Deployment logs are visible and clear

---

## Quick Reference Commands

**Check workflow status:**
```bash
# View on GitHub
https://github.com/YOUR_USERNAME/telegram-bot-toko/actions
```

**Manual deployment test:**
```bash
echo "# test" >> README.md
git add README.md
git commit -m "test: CI/CD deployment"
git push origin main
```

**Check VPS deployment:**
```bash
ssh deploy@your-vps-ip "cd ~/apps/telegram-bot-toko && git log -1"
```

**View container logs:**
```bash
ssh deploy@your-vps-ip "cd ~/apps/telegram-bot-toko/docker && docker compose logs --tail=50 bot"
```

**Manual rollback:**
```bash
ssh deploy@your-vps-ip
cd ~/apps/telegram-bot-toko
git checkout <previous-commit-hash>
cd docker && docker compose build --no-cache && docker compose up -d
```

---

## Next Steps

Congratulations! Your CI/CD pipeline is now set up.

**What to do next:**
1. Test your deployment with a small code change
2. Familiarize yourself with the GitHub Actions interface
3. Set up branch protection rules (optional)
4. Configure deployment notifications (optional)
5. Proceed to [`08-MONITORING-MAINTENANCE.md`](08-MONITORING-MAINTENANCE.md) for ongoing monitoring

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [SSH Key Authentication Guide](https://www.ssh.com/academy/ssh/key)
- [CICD-QUICK-REFERENCE.md](CICD-QUICK-REFERENCE.md) - One-page cheat sheet

---

**Document Version**: 2.0
**Last Updated**: 2026-01-12
**Tested On**: Ubuntu 24.04 LTS, Docker Compose v2, GitHub Actions
**Project**: Telegram Bot Toko (Python 3.11)
