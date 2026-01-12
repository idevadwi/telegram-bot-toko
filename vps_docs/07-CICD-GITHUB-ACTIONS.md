# Phase 7: CI/CD with GitHub Actions

## Overview
This document covers setting up automated CI/CD pipelines using GitHub Actions to deploy your applications from GitHub to your VPS via SSH.

**Prerequisites**: 
- Completed Phase 1 (Initial Server Setup with SSH keys)
- GitHub repository for your application
- Applications set up on VPS

---

## Architecture

```
┌──────────────┐         ┌──────────────────┐         ┌──────────────┐
│   GitHub     │         │  GitHub Actions  │         │     VPS      │
│  Repository  │────────▶│    Workflow      │────────▶│   Server     │
│              │  Push   │                  │   SSH   │              │
└──────────────┘         └──────────────────┘         └──────────────┘
                                │
                                │ Runs Tests
                                │ Builds App
                                │ Deploys via SSH
                                ▼
                         ┌──────────────────┐
                         │   Application    │
                         │    Running       │
                         └──────────────────┘
```

---

## Part A: VPS Preparation for CI/CD

### Step 1: Create Deployment SSH Key

Create a dedicated SSH key for GitHub Actions:

```bash
# On your VPS, as deploy user
cd ~/.ssh

# Generate deployment key
ssh-keygen -t ed25519 -C "github-actions-deploy" -f github_deploy_key

# This creates:
# - github_deploy_key (private key - for GitHub Secrets)
# - github_deploy_key.pub (public key - for VPS)
```

---

### Step 2: Add Public Key to Authorized Keys

```bash
# Add public key to authorized_keys
cat github_deploy_key.pub >> ~/.ssh/authorized_keys

# Set proper permissions
chmod 600 ~/.ssh/authorized_keys
```

---

### Step 3: Display Private Key for GitHub Secrets

```bash
# Display private key (copy this for GitHub Secrets)
cat github_deploy_key

# Copy the entire output including:
# -----BEGIN OPENSSH PRIVATE KEY-----
# ... key content ...
# -----END OPENSSH PRIVATE KEY-----
```

**Important**: Keep this private key secure. You'll add it to GitHub Secrets.

---

### Step 4: Create Deployment Directories

```bash
# Create deployment directories
mkdir -p ~/deployments/laravel
mkdir -p ~/deployments/telegram-bot
mkdir -p ~/deployments/spring-kotlin

# Create logs directory
mkdir -p ~/logs/deployments
```

---

## Part B: GitHub Repository Setup

### Step 1: Add GitHub Secrets

For each repository, add these secrets:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

Add these secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `VPS_HOST` | Your VPS IP address | Server IP |
| `VPS_USERNAME` | `deploy` | SSH username |
| `VPS_SSH_KEY` | Private key content | SSH private key |
| `VPS_PORT` | `22` | SSH port |

**Application-specific secrets** (add as needed):

For Laravel:
- `DB_PASSWORD` - Database password
- `APP_KEY` - Laravel application key

For Telegram Bot:
- `TELEGRAM_BOT_TOKEN` - Bot token
- `DB_PASSWORD` - PostgreSQL password

For Spring Kotlin:
- `DB_PASSWORD` - Database password
- `JWT_SECRET` - JWT secret (if applicable)

---

## Part C: GitHub Actions Workflows

### Workflow 1: Laravel Application

Create `.github/workflows/deploy-laravel.yml` in your Laravel repository:

```yaml
name: Deploy Laravel Application

on:
  push:
    branches:
      - main
      - production
  workflow_dispatch:

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: password
          MYSQL_DATABASE: testing
        ports:
          - 3306:3306
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.3'
          extensions: mbstring, xml, bcmath, mysql, zip
          coverage: none
      
      - name: Copy .env
        run: |
          cp .env.example .env
          php artisan key:generate
      
      - name: Install Composer dependencies
        run: composer install --prefer-dist --no-progress --no-interaction
      
      - name: Run tests
        env:
          DB_CONNECTION: mysql
          DB_HOST: 127.0.0.1
          DB_PORT: 3306
          DB_DATABASE: testing
          DB_USERNAME: root
          DB_PASSWORD: password
        run: php artisan test

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
          APP_NAME: laravel-app
        run: |
          ssh $VPS_USERNAME@$VPS_HOST << 'ENDSSH'
            set -e
            
            # Navigate to app directory
            cd ~/apps/laravel/$APP_NAME
            
            # Pull latest code
            git pull origin main
            
            # Install dependencies
            composer install --no-dev --optimize-autoloader --no-interaction
            
            # Run migrations
            php artisan migrate --force
            
            # Clear and cache
            php artisan config:cache
            php artisan route:cache
            php artisan view:cache
            
            # Restart PHP-FPM
            sudo systemctl restart php8.3-fpm
            
            echo "Deployment completed successfully!"
          ENDSSH
      
      - name: Deployment notification
        if: always()
        run: |
          if [ ${{ job.status }} == 'success' ]; then
            echo "✅ Deployment successful!"
          else
            echo "❌ Deployment failed!"
          fi
```

---

### Workflow 2: Python Telegram Bot

Create `.github/workflows/deploy-telegram-bot.yml`:

```yaml
name: Deploy Telegram Bot

on:
  push:
    branches:
      - main
  workflow_dispatch:

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
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest tests/ -v --cov=.

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
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        run: |
          ssh $VPS_USERNAME@$VPS_HOST << 'ENDSSH'
            set -e
            
            # Navigate to bot directory
            cd ~/docker/telegram-bot/app
            
            # Pull latest code
            git pull origin main
            
            # Navigate back to docker directory
            cd ..
            
            # Update .env file
            echo "TELEGRAM_BOT_TOKEN=${{ secrets.TELEGRAM_BOT_TOKEN }}" > .env
            echo "DB_PASSWORD=${{ secrets.DB_PASSWORD }}" >> .env
            
            # Rebuild and restart container
            docker compose down
            docker compose build --no-cache
            docker compose up -d
            
            # Wait for container to start
            sleep 10
            
            # Check if container is running
            docker compose ps
            
            echo "Telegram bot deployed successfully!"
          ENDSSH
      
      - name: Verify deployment
        env:
          VPS_HOST: ${{ secrets.VPS_HOST }}
          VPS_USERNAME: ${{ secrets.VPS_USERNAME }}
        run: |
          ssh $VPS_USERNAME@$VPS_HOST << 'ENDSSH'
            cd ~/docker/telegram-bot
            docker compose logs --tail=50
          ENDSSH
```

---

### Workflow 3: Spring Kotlin Application

Create `.github/workflows/deploy-spring.yml`:

```yaml
name: Deploy Spring Kotlin Application

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  build-and-test:
    name: Build and Test
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
      
      - name: Setup Gradle
        uses: gradle/gradle-build-action@v2
      
      - name: Build with Gradle
        run: ./gradlew build
      
      - name: Run tests
        run: ./gradlew test
      
      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: spring-app-jar
          path: build/libs/*.jar

  deploy:
    name: Deploy to VPS
    runs-on: ubuntu-latest
    needs: build-and-test
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
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        run: |
          ssh $VPS_USERNAME@$VPS_HOST << 'ENDSSH'
            set -e
            
            # Navigate to app directory
            cd ~/docker/spring-kotlin/app
            
            # Pull latest code
            git pull origin main
            
            # Navigate back to docker directory
            cd ..
            
            # Update .env file
            echo "DB_PASSWORD=${{ secrets.DB_PASSWORD }}" > .env
            
            # Rebuild and restart container
            docker compose down
            docker compose build --no-cache
            docker compose up -d
            
            # Wait for application to start
            sleep 30
            
            # Check health
            docker compose ps
            
            echo "Spring application deployed successfully!"
          ENDSSH
      
      - name: Health check
        env:
          VPS_HOST: ${{ secrets.VPS_HOST }}
          VPS_USERNAME: ${{ secrets.VPS_USERNAME }}
        run: |
          ssh $VPS_USERNAME@$VPS_HOST << 'ENDSSH'
            # Wait for health endpoint
            for i in {1..10}; do
              if docker exec spring-kotlin-app wget --spider -q http://localhost:8080/actuator/health; then
                echo "✅ Application is healthy!"
                exit 0
              fi
              echo "Waiting for application to be ready... ($i/10)"
              sleep 5
            done
            echo "❌ Application health check failed"
            exit 1
          ENDSSH
```

---

## Part D: Advanced Workflow Features

### Workflow with Environment-Specific Deployments

Create `.github/workflows/deploy-multi-env.yml`:

```yaml
name: Multi-Environment Deployment

on:
  push:
    branches:
      - develop
      - staging
      - main

jobs:
  deploy:
    name: Deploy to ${{ github.ref_name }}
    runs-on: ubuntu-latest
    
    environment:
      name: ${{ github.ref_name }}
      url: https://${{ github.ref_name }}.yourdomain.com
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.8.0
        with:
          ssh-private-key: ${{ secrets.VPS_SSH_KEY }}
      
      - name: Deploy
        env:
          ENVIRONMENT: ${{ github.ref_name }}
        run: |
          ssh ${{ secrets.VPS_USERNAME }}@${{ secrets.VPS_HOST }} << 'ENDSSH'
            cd ~/apps/$ENVIRONMENT
            git pull origin $ENVIRONMENT
            # Environment-specific deployment commands
          ENDSSH
```

---

### Workflow with Rollback Capability

Create `.github/workflows/deploy-with-rollback.yml`:

```yaml
name: Deploy with Rollback

on:
  workflow_dispatch:
    inputs:
      action:
        description: 'Action to perform'
        required: true
        type: choice
        options:
          - deploy
          - rollback

jobs:
  deploy:
    if: github.event.inputs.action == 'deploy'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.8.0
        with:
          ssh-private-key: ${{ secrets.VPS_SSH_KEY }}
      
      - name: Deploy with backup
        run: |
          ssh ${{ secrets.VPS_USERNAME }}@${{ secrets.VPS_HOST }} << 'ENDSSH'
            set -e
            APP_DIR=~/apps/laravel/myapp
            BACKUP_DIR=~/backups/deployments
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            
            # Create backup
            mkdir -p $BACKUP_DIR
            tar czf $BACKUP_DIR/backup_$TIMESTAMP.tar.gz -C $APP_DIR .
            
            # Deploy
            cd $APP_DIR
            git pull origin main
            composer install --no-dev --optimize-autoloader
            php artisan migrate --force
            php artisan config:cache
            
            # Save deployment info
            echo $TIMESTAMP > $BACKUP_DIR/latest_deployment.txt
            
            sudo systemctl restart php8.3-fpm
          ENDSSH
  
  rollback:
    if: github.event.inputs.action == 'rollback'
    runs-on: ubuntu-latest
    steps:
      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.8.0
        with:
          ssh-private-key: ${{ secrets.VPS_SSH_KEY }}
      
      - name: Rollback to previous version
        run: |
          ssh ${{ secrets.VPS_USERNAME }}@${{ secrets.VPS_HOST }} << 'ENDSSH'
            set -e
            APP_DIR=~/apps/laravel/myapp
            BACKUP_DIR=~/backups/deployments
            
            # Get latest backup
            LATEST_BACKUP=$(ls -t $BACKUP_DIR/backup_*.tar.gz | head -1)
            
            if [ -z "$LATEST_BACKUP" ]; then
              echo "No backup found!"
              exit 1
            fi
            
            echo "Rolling back to: $LATEST_BACKUP"
            
            # Restore backup
            rm -rf $APP_DIR/*
            tar xzf $LATEST_BACKUP -C $APP_DIR
            
            # Restart services
            sudo systemctl restart php8.3-fpm
            
            echo "Rollback completed!"
          ENDSSH
```

---

## Part E: Deployment Monitoring

### Create Deployment Notification Script

```bash
nano ~/scripts/notify-deployment.sh
```

Add this content:

```bash
#!/bin/bash
# Deployment notification script

APP_NAME=$1
STATUS=$2
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

LOG_FILE="$HOME/logs/deployments/deployment.log"

mkdir -p "$(dirname "$LOG_FILE")"

echo "[$TIMESTAMP] $APP_NAME - $STATUS" >> "$LOG_FILE"

# Optional: Send to monitoring service
# curl -X POST https://your-monitoring-service.com/webhook \
#   -H "Content-Type: application/json" \
#   -d "{\"app\":\"$APP_NAME\",\"status\":\"$STATUS\",\"timestamp\":\"$TIMESTAMP\"}"
```

Make executable:

```bash
chmod +x ~/scripts/notify-deployment.sh
```

---

## Part F: Security Best Practices

### 1. Rotate Deployment Keys Regularly

```bash
# Generate new deployment key
ssh-keygen -t ed25519 -C "github-actions-deploy-$(date +%Y%m)" -f ~/.ssh/github_deploy_key_new

# Add new key to authorized_keys
cat ~/.ssh/github_deploy_key_new.pub >> ~/.ssh/authorized_keys

# Update GitHub Secrets with new private key
# Then remove old key from authorized_keys
```

### 2. Limit SSH Key Permissions

Edit `~/.ssh/authorized_keys` and prepend restrictions:

```bash
# Edit authorized_keys
nano ~/.ssh/authorized_keys
```

Add restrictions before the key:

```
command="~/scripts/deploy-only.sh",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-ed25519 AAAA...
```

Create restricted deployment script:

```bash
nano ~/scripts/deploy-only.sh
```

```bash
#!/bin/bash
# Restricted deployment script

case "$SSH_ORIGINAL_COMMAND" in
  "cd ~/apps"*|"git pull"*|"composer install"*|"php artisan"*|"docker compose"*|"sudo systemctl restart php8.3-fpm")
    eval "$SSH_ORIGINAL_COMMAND"
    ;;
  *)
    echo "Command not allowed"
    exit 1
    ;;
esac
```

Make executable:

```bash
chmod +x ~/scripts/deploy-only.sh
```

---

## Verification Checklist

- [x] Deployment SSH key created and configured
- [x] GitHub Secrets added to repositories
- [x] GitHub Actions workflows created
- [x] Test deployment successful
- [x] Rollback procedure tested
- [x] Deployment logging configured
- [x] Security restrictions applied

---

## Testing Your CI/CD Pipeline

### Test Laravel Deployment

```bash
# In your Laravel repository
git add .
git commit -m "Test CI/CD deployment"
git push origin main

# Watch GitHub Actions tab for workflow execution
```

### Test Telegram Bot Deployment

```bash
# In your bot repository
git add .
git commit -m "Test bot deployment"
git push origin main
```

### Test Spring Deployment

```bash
# In your Spring repository
git add .
git commit -m "Test Spring deployment"
git push origin main
```

---

## Troubleshooting

### SSH Connection Issues

```bash
# Test SSH connection from GitHub Actions
ssh -i ~/.ssh/github_deploy_key deploy@YOUR_VPS_IP "echo 'Connection successful'"
```

### Permission Denied Errors

```bash
# Check SSH key permissions
ls -la ~/.ssh/

# Ensure correct permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/github_deploy_key
```

### Deployment Fails

```bash
# Check deployment logs
tail -f ~/logs/deployments/deployment.log

# Check application logs
docker compose logs -f
```

---

## Next Steps

Proceed to [`08-MONITORING-MAINTENANCE.md`](08-MONITORING-MAINTENANCE.md) for monitoring and maintenance procedures.

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-07  
**Tested On**: Ubuntu 24.04 LTS with GitHub Actions
