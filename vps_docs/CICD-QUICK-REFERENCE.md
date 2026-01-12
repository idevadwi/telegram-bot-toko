# CI/CD Quick Reference Guide

**Project:** Telegram Bot Toko | **Version:** 1.0 | **Updated:** 2026-01-12

---

## 🚀 Quick Start Checklist

### Prerequisites (One-Time Setup)
- [ ] SSH key generated on VPS: `~/.ssh/github_deploy_key`
- [ ] Public key added to authorized_keys
- [ ] All 9 GitHub Secrets configured
- [ ] Workflow file exists: `.github/workflows/deploy-telegram-bot-toko.yml`
- [ ] VPS has project at: `~/apps/telegram-bot-toko/`

---

## 🔐 Required GitHub Secrets

Configure these at: `Settings → Secrets and variables → Actions`

| Secret Name | Description | Example |
|------------|-------------|---------|
| `VPS_HOST` | VPS IP address | `123.45.67.89` |
| `VPS_USERNAME` | SSH username | `deploy` |
| `VPS_SSH_KEY` | Private SSH key content | Full key with BEGIN/END |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `123456:ABC-DEF...` |
| `DROPBOX_APP_KEY` | Dropbox API key | From Dropbox Console |
| `DROPBOX_APP_SECRET` | Dropbox API secret | From Dropbox Console |
| `DROPBOX_REFRESH_TOKEN` | Dropbox refresh token | OAuth generated |
| `DB_PASSWORD` | PostgreSQL password | Your DB password |
| `ALLOWED_USERS` | Telegram user IDs | `123456,789012` |

---

## 🔧 SSH Key Setup Commands

```bash
# Generate SSH key on VPS
ssh deploy@your-vps-ip
cd ~/.ssh
ssh-keygen -t ed25519 -C "github-actions-telegram-bot" -f github_deploy_key

# Add to authorized_keys
cat github_deploy_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Display private key (copy for GitHub Secret)
cat github_deploy_key

# Test connection
ssh -i ~/.ssh/github_deploy_key deploy@localhost "echo 'Success'"
```

---

## 🎯 Deployment Workflows

### Automatic Deployment (Push to Main)
```bash
# Make changes locally
git add .
git commit -m "feat: your change description"
git push origin main

# GitHub Actions triggers automatically
# Check status: https://github.com/YOUR_USERNAME/telegram-bot-toko/actions
```

### Manual Triggers
Go to: **Repository → Actions → Deploy Telegram Bot Toko → Run workflow**

**Available Actions:**
- **deploy** - Full deployment (pull, rebuild, restart)
- **sync** - Run data sync from Dropbox
- **restart** - Simply restart the container

---

## 📊 Monitoring Commands

### Check Deployment Status
```bash
# On GitHub
# Go to: Repository → Actions tab

# On VPS - Check latest commit
ssh deploy@your-vps-ip "cd ~/apps/telegram-bot-toko && git log -1"

# Check container status
ssh deploy@your-vps-ip "cd ~/apps/telegram-bot-toko/docker && docker compose ps"

# View logs
ssh deploy@your-vps-ip "cd ~/apps/telegram-bot-toko/docker && docker compose logs --tail=50 telegram-bot-toko"
```

### Real-Time Log Monitoring
```bash
# SSH to VPS
ssh deploy@your-vps-ip

# Navigate to docker directory
cd ~/apps/telegram-bot-toko/docker

# Follow logs
docker compose logs -f telegram-bot-toko
```

---

## 🔄 Rollback Procedures

### Quick Rollback (SSH)
```bash
ssh deploy@your-vps-ip
cd ~/apps/telegram-bot-toko

# View commits
git log --oneline -10

# Rollback to specific commit
git checkout <commit-hash>

# Rebuild and restart
cd docker
docker compose build --no-cache
docker compose up -d

# Verify
docker compose logs -f telegram-bot-toko
```

### Rollback via Git Revert (Recommended)
```bash
# On local machine
git log --oneline -10
git revert <bad-commit-hash>
git push origin main  # Triggers auto-deployment
```

---

## 🐛 Troubleshooting Quick Fixes

### Issue: SSH Connection Failed
```bash
# Verify key permissions on VPS
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/github_deploy_key

# Check if key is in authorized_keys
grep "github-actions-telegram-bot" ~/.ssh/authorized_keys
```

### Issue: Git Pull Fails
```bash
ssh deploy@your-vps-ip
cd ~/apps/telegram-bot-toko
git reset --hard HEAD  # Discard local changes
git pull origin main
```

### Issue: Docker Build Fails
```bash
# Check Docker is running
ssh deploy@your-vps-ip
sudo systemctl status docker

# Check disk space
df -h

# Clean up old images
docker system prune -a --volumes
```

### Issue: Container Not Starting
```bash
# Check logs for errors
ssh deploy@your-vps-ip
cd ~/apps/telegram-bot-toko/docker
docker compose logs telegram-bot-toko

# Check .env file
cat ../config/.env

# Restart container
docker compose restart telegram-bot-toko
```

### Issue: Environment Variables Not Updating
```bash
# SSH to VPS
ssh deploy@your-vps-ip
cd ~/apps/telegram-bot-toko/config

# Verify .env content
cat .env

# Manually update if needed
nano .env

# Restart
cd ../docker
docker compose restart telegram-bot-toko
```

---

## 🧪 Testing Deployment

### Initial Test
```bash
# Make small change
echo "# CI/CD test" >> README.md
git add README.md
git commit -m "test: verify CI/CD"
git push origin main

# Watch: https://github.com/YOUR_USERNAME/telegram-bot-toko/actions

# Verify on VPS
ssh deploy@your-vps-ip "cd ~/apps/telegram-bot-toko && git log -1"
```

### Manual Trigger Test
1. Go to: **Actions → Deploy Telegram Bot Toko**
2. Click: **Run workflow**
3. Select: **sync**
4. Click: **Run workflow** (green button)
5. Watch execution and verify completion

---

## 📁 Important Paths

### Local Development
- Workflow file: `.github/workflows/deploy-telegram-bot-toko.yml`
- Environment example: `config/.env.example`
- Documentation: `vps_docs/07-CICD-GITHUB-ACTIONS.md`

### VPS Production
- Project root: `~/apps/telegram-bot-toko/`
- Docker compose: `~/apps/telegram-bot-toko/docker/docker-compose.yml`
- Environment: `~/apps/telegram-bot-toko/config/.env`
- Logs: `~/apps/telegram-bot-toko/logs/`
- Data: `~/apps/telegram-bot-toko/data/`
- SSH key: `~/.ssh/github_deploy_key`

---

## 🔒 Security Best Practices

### SSH Key Rotation (Every 3 Months)
```bash
# Generate new key
cd ~/.ssh
ssh-keygen -t ed25519 -C "github-actions-$(date +%Y%m)" -f github_deploy_key_new

# Add new public key
cat github_deploy_key_new.pub >> authorized_keys

# Update GitHub Secret VPS_SSH_KEY with new private key
cat github_deploy_key_new

# After testing, remove old key from authorized_keys
```

### Audit Deployment History
```bash
# View deployment history
ssh deploy@your-vps-ip
cd ~/apps/telegram-bot-toko
git log --oneline --graph --all -20

# View container restart history
cd docker
docker compose logs --since 7d telegram-bot-toko | grep "Starting"
```

---

## 💡 Common Operations

### Force Rebuild Container
```bash
ssh deploy@your-vps-ip
cd ~/apps/telegram-bot-toko/docker
docker compose build --no-cache
docker compose up -d
```

### View Container Stats
```bash
ssh deploy@your-vps-ip
docker stats telegram-bot-toko
```

### Check Database Connection
```bash
ssh deploy@your-vps-ip
cd ~/apps/telegram-bot-toko/docker
docker compose exec telegram-bot-toko python -c "from src.core.config import Config; print('DB:', Config.DB_HOST)"
```

### Manual Sync Data
```bash
ssh deploy@your-vps-ip
cd ~/apps/telegram-bot-toko/docker
docker compose exec telegram-bot-toko python -m scripts.sync
```

### Restart PostgreSQL
```bash
ssh deploy@your-vps-ip
cd ~/apps/telegram-bot-toko/docker
docker restart postgresql-server
```

---

## 📞 Support & Resources

- **Full Documentation:** [07-CICD-GITHUB-ACTIONS.md](07-CICD-GITHUB-ACTIONS.md)
- **GitHub Actions Docs:** [https://docs.github.com/en/actions](https://docs.github.com/en/actions)
- **Docker Compose Docs:** [https://docs.docker.com/compose/](https://docs.docker.com/compose/)
- **Telegram Bot API:** [https://core.telegram.org/bots/api](https://core.telegram.org/bots/api)

---

## ✅ Success Indicators

Your CI/CD is working correctly when:
- ✅ Push to main triggers workflow automatically
- ✅ Workflow completes with green checkmark
- ✅ Latest code appears on VPS (`git log -1`)
- ✅ Container shows "Up" status
- ✅ Bot responds on Telegram
- ✅ No errors in logs
- ✅ Manual triggers work (sync, restart, deploy)

---

## 🆘 Emergency Contacts

**If deployment breaks production:**

1. **Quick fix:** Use manual rollback commands above
2. **Investigate:** Check GitHub Actions logs + VPS container logs
3. **Restore:** Rollback to last known working commit
4. **Fix forward:** Fix issue locally, test, push new commit

**Key principle:** Never panic. You can always rollback.

---

**Keep this guide handy for quick reference during deployments!**

**Document Version:** 1.0 | **Last Updated:** 2026-01-12
