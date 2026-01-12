# Telegram Bot Toko - CI/CD GitHub Actions Workflow

This document contains the GitHub Actions workflow for automated deployment of Telegram Bot Toko to your VPS.

## Workflow File Location

Create this file in your repository:
`.github/workflows/deploy-telegram-bot-toko.yml`

## Complete Workflow Content

```yaml
name: Deploy Telegram Bot Toko

on:
  push:
    branches:
      - main
      - production
  workflow_dispatch:
    inputs:
      action:
        description: 'Action to perform'
        required: true
        type: choice
        options:
          - deploy
          - sync
          - restart

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-mock
      
      - name: Run tests
        run: |
          pytest tests/ -v --cov=src --cov-report=xml --cov-report=term
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: false

  deploy:
    name: Deploy to VPS
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.8.0
        with:
          ssh-private-key: ${{ secrets.VPS_SSH_KEY }}
      
      - name: Add VPS to known hosts
        run: |
          mkdir -p ~/.ssh
          ssh-keyscan -H ${{ secrets.VPS_HOST }} >> ~/.ssh/known_hosts
      
      - name: Deploy to VPS
        env:
          VPS_HOST: ${{ secrets.VPS_HOST }}
          VPS_USERNAME: ${{ secrets.VPS_USERNAME }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          DROPBOX_APP_KEY: ${{ secrets.DROPBOX_APP_KEY }}
          DROPBOX_APP_SECRET: ${{ secrets.DROPBOX_APP_SECRET }}
          DROPBOX_REFRESH_TOKEN: ${{ secrets.DROPBOX_REFRESH_TOKEN }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        run: |
          ssh $VPS_USERNAME@$VPS_HOST << 'ENDSSH'
            set -e
            
            # Navigate to project directory
            cd ~/apps/telegram-bot-toko
            
            # Pull latest code
            git pull origin main
            
            # Update environment variables
            cat > config/.env << ENVEOF
            # Dropbox Configuration
            DROPBOX_APP_KEY=${{ secrets.DROPBOX_APP_KEY }}
            DROPBOX_APP_SECRET=${{ secrets.DROPBOX_APP_SECRET }}
            DROPBOX_REFRESH_TOKEN=${{ secrets.DROPBOX_REFRESH_TOKEN }}
            DROPBOX_FOLDER_PATH=/IPOS
            
            # Telegram Configuration
            TELEGRAM_BOT_TOKEN=${{ secrets.TELEGRAM_BOT_TOKEN }}
            ALLOWED_USERS=${{ secrets.ALLOWED_USERS }}
            
            # Database Configuration
            DB_HOST=postgresql-server
            DB_PORT=5432
            DB_NAME=i5bu
            DB_USER=postgres
            DB_PASSWORD=${{ secrets.DB_PASSWORD }}
            
            # Application Configuration
            MAX_CSV_FILES=5
            SEARCH_RESULTS_LIMIT=10
            
            # Logging Configuration
            LOG_LEVEL=INFO
            ENVEOF
            
            # Set secure permissions
            chmod 600 config/.env
            
            # Navigate to docker directory
            cd docker
            
            # Rebuild and restart container
            docker compose down
            docker compose build --no-cache
            docker compose up -d
            
            # Wait for container to start
            sleep 10
            
            # Check if container is running
            docker compose ps
            
            echo "Deployment completed successfully!"
          ENDSSH
      
      - name: Verify deployment
        env:
          VPS_HOST: ${{ secrets.VPS_HOST }}
          VPS_USERNAME: ${{ secrets.VPS_USERNAME }}
        run: |
          ssh $VPS_USERNAME@$VPS_HOST << 'ENDSSH'
            cd ~/apps/telegram-bot-toko/docker
            docker compose logs --tail=50
          ENDSSH
      
      - name: Deployment notification
        if: always()
        run: |
          if [ ${{ job.status }} == 'success' ]; then
            echo "✅ Telegram Bot Toko deployed successfully!"
          else
            echo "❌ Deployment failed!"
          fi

  sync:
    name: Trigger Data Sync
    runs-on: ubuntu-latest
    if: github.event.inputs.action == 'sync'
    
    steps:
      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.8.0
        with:
          ssh-private-key: ${{ secrets.VPS_SSH_KEY }}
      
      - name: Add VPS to known hosts
        run: |
          mkdir -p ~/.ssh
          ssh-keyscan -H ${{ secrets.VPS_HOST }} >> ~/.ssh/known_hosts
      
      - name: Trigger sync
        env:
          VPS_HOST: ${{ secrets.VPS_HOST }}
          VPS_USERNAME: ${{ secrets.VPS_USERNAME }}
        run: |
          ssh $VPS_USERNAME@$VPS_HOST << 'ENDSSH'
            cd ~/apps/telegram-bot-toko
            python -m scripts.sync
          ENDSSH
      
      - name: Sync notification
        run: |
          echo "✅ Data sync triggered!"

  restart:
    name: Restart Bot
    runs-on: ubuntu-latest
    if: github.event.inputs.action == 'restart'
    
    steps:
      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.8.0
        with:
          ssh-private-key: ${{ secrets.VPS_SSH_KEY }}
      
      - name: Add VPS to known hosts
        run: |
          mkdir -p ~/.ssh
          ssh-keyscan -H ${{ secrets.VPS_HOST }} >> ~/.ssh/known_hosts
      
      - name: Restart bot
        env:
          VPS_HOST: ${{ secrets.VPS_HOST }}
          VPS_USERNAME: ${{ secrets.VPS_USERNAME }}
        run: |
          ssh $VPS_USERNAME@$VPS_HOST << 'ENDSSH'
            cd ~/apps/telegram-bot-toko/docker
            docker compose restart bot
            echo "Bot restarted successfully!"
          ENDSSH
      
      - name: Restart notification
        run: |
          echo "✅ Bot restarted!"
```

---

## Required GitHub Secrets

Add these secrets to your GitHub repository:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### Required Secrets

| Secret Name | Value | Description |
|------------|-------|-------------|
| `VPS_HOST` | Your VPS IP address | Server IP (e.g., 123.45.67.89) |
| `VPS_USERNAME` | `deploy` | SSH username |
| `VPS_SSH_KEY` | Private key content | SSH private key from Phase 7 (vps_docs/07-CICD-GITHUB-ACTIONS.md) |
| `TELEGRAM_BOT_TOKEN` | Your bot token | From @BotFather |
| `DROPBOX_APP_KEY` | Dropbox app key | From Dropbox Developer Console |
| `DROPBOX_APP_SECRET` | Dropbox app secret | From Dropbox Developer Console |
| `DROPBOX_REFRESH_TOKEN` | Dropbox refresh token | From Dropbox Developer Console |
| `DB_PASSWORD` | PostgreSQL password | From Phase 5 database setup |
| `ALLOWED_USERS` | Comma-separated user IDs | Telegram user IDs (e.g., 123456789,987654321) |

---

## Workflow Features

### 1. Automated Deployment on Push
- Automatically deploys when code is pushed to `main` branch
- Runs tests before deployment
- Pulls latest code from GitHub
- Updates environment variables from secrets
- Rebuilds and restarts Docker container

### 2. Manual Deployment
- Use **workflow_dispatch** to manually trigger deployment
- Options: `deploy`, `sync`, `restart`
- Accessible from GitHub Actions tab → Select workflow → Run workflow

### 3. Testing
- Runs pytest tests before deployment
- Uploads coverage reports to Codecov (optional)
- Prevents deployment if tests fail

### 4. Data Sync
- Manually trigger sync from GitHub Actions
- Downloads latest backup from Dropbox
- Restores to PostgreSQL
- Exports to CSV

### 5. Bot Restart
- Quick restart without full deployment
- Useful for configuration changes or troubleshooting

---

## Setup Instructions

### Step 1: Create Workflow File

```bash
# On your local machine
cd telegram-bot-toko

# Create .github/workflows directory
mkdir -p .github/workflows

# Create workflow file
nano .github/workflows/deploy-telegram-bot-toko.yml
```

Paste the workflow content from above.

### Step 2: Commit and Push

```bash
git add .github/workflows/deploy-telegram-bot-toko.yml
git commit -m "Add CI/CD workflow for Telegram Bot Toko"
git push origin main
```

### Step 3: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add all required secrets listed above

### Step 4: Test Deployment

```bash
# Make a small change to trigger deployment
echo "# Test deployment" >> README.md
git add README.md
git commit -m "Test CI/CD deployment"
git push origin main
```

### Step 5: Monitor Deployment

1. Go to your GitHub repository
2. Click **Actions** tab
3. Select the workflow run
4. Monitor the progress:
   - ✅ Run Tests
   - ✅ Deploy to VPS
   - ✅ Verify deployment

---

## Manual Workflow Trigger

### Trigger Deployment Manually

1. Go to your GitHub repository
2. Click **Actions** tab
3. Select **Deploy Telegram Bot Toko** workflow
4. Click **Run workflow**
5. Choose action: `deploy`, `sync`, or `restart`
6. Click **Run workflow**

### Trigger Sync Manually

1. Follow steps above
2. Choose action: `sync`
3. Click **Run workflow**

### Trigger Restart Manually

1. Follow steps above
2. Choose action: `restart`
3. Click **Run workflow**

---

## Troubleshooting CI/CD

### Issue: SSH Connection Failed

**Symptoms**: Workflow fails at "Setup SSH" step

**Solutions**:
1. Verify VPS_SSH_KEY is correct in GitHub Secrets
2. Check VPS_HOST is correct
3. Ensure VPS is accessible from GitHub Actions
4. Test SSH connection locally:
   ```bash
   ssh -i ~/.ssh/github_deploy_key deploy@YOUR_VPS_IP
   ```

### Issue: Tests Failed

**Symptoms**: Workflow fails at "Run Tests" step

**Solutions**:
1. Run tests locally:
   ```bash
   pytest tests/ -v
   ```
2. Fix any failing tests
3. Commit and push fixes

### Issue: Deployment Failed

**Symptoms**: Workflow fails at "Deploy to VPS" step

**Solutions**:
1. Check deployment logs in GitHub Actions
2. SSH into VPS and check manually:
   ```bash
   ssh deploy@YOUR_VPS_IP
   cd ~/apps/telegram-bot-toko
   git pull origin main
   ```
3. Check Docker logs:
   ```bash
   cd docker
   docker compose logs
   ```

### Issue: Environment Variables Not Updated

**Symptoms**: Bot uses old configuration after deployment

**Solutions**:
1. Verify secrets are set correctly in GitHub
2. Check .env file on VPS:
   ```bash
   cat ~/apps/telegram-bot-toko/config/.env
   ```
3. Manually update .env if needed:
   ```bash
   nano ~/apps/telegram-bot-toko/config/.env
   ```

---

## Best Practices

### 1. Branch Protection
- Enable branch protection for `main` branch
- Require pull request reviews
- Require status checks to pass

### 2. Secret Rotation
- Rotate SSH keys regularly (every 3 months)
- Update VPS_SSH_KEY in GitHub Secrets
- Remove old keys from authorized_keys

### 3. Monitoring
- Monitor GitHub Actions runs regularly
- Set up notifications for failed deployments
- Review logs for errors

### 4. Testing
- Always run tests locally before pushing
- Maintain high test coverage
- Add tests for new features

### 5. Rollback
- Keep previous Docker images
- Use git to rollback if needed:
  ```bash
  git revert HEAD
  git push origin main
  ```

---

## Workflow Diagram

```
┌──────────────┐
│   GitHub     │
│  Repository  │
└──────┬───────┘
       │ Push to main
       ▼
┌──────────────────┐
│ GitHub Actions   │
│   Workflow      │
└──────┬─────────┘
       │
       ├─▶ Run Tests (pytest)
       │       │
       │       ├─ Success → Deploy
       │       └─ Fail → Stop
       │
       ▼
┌──────────────────┐
│  Deploy to VPS │
│  via SSH       │
└──────┬─────────┘
       │
       ├─▶ Pull code
       ├─▶ Update .env
       ├─▶ Rebuild Docker
       └─▶ Restart container
               │
               ▼
        ┌──────────────┐
        │ Bot Running  │
        └──────────────┘
```

---

## Next Steps

After setting up CI/CD:

1. ✅ Test automatic deployment on push
2. ✅ Test manual workflow triggers
3. ✅ Set up notifications for failed deployments
4. ✅ Configure branch protection rules
5. ✅ Monitor deployment logs regularly

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-12  
**Compatible With**: GitHub Actions, Docker Compose V2
