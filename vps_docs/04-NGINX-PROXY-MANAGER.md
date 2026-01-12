# Phase 4: Nginx Proxy Manager Setup

## Overview
Nginx Proxy Manager (NPM) provides a user-friendly web interface for managing Nginx proxy hosts, SSL certificates, and access control. This is the recommended solution for managing multiple websites and domains on your VPS.

**Prerequisites**: 
- Completed Phase 1 (Initial Server Setup)
- Completed Phase 3 (Docker Installation)
- Ports 80, 443 open in UFW
- Domain names pointed to your VPS IP

---

## Why Nginx Proxy Manager?

### Advantages
✅ **User-Friendly Web UI** - No need to edit Nginx config files  
✅ **Built-in Let's Encrypt** - Automatic SSL certificate management  
✅ **Multi-Domain Support** - Easy management of multiple websites  
✅ **Access Lists** - Built-in authentication and IP whitelisting  
✅ **WebSocket Support** - Perfect for real-time applications  
✅ **Custom Locations** - Advanced routing capabilities  
✅ **Stream Support** - TCP/UDP proxying  
✅ **Docker Native** - Runs in a container, isolated and secure  

---

## Step 1: Create Nginx Proxy Manager Directory

```bash
# Create NPM directory
mkdir -p ~/docker/nginx-proxy-manager

# Navigate to directory
cd ~/docker/nginx-proxy-manager
```

---

## Step 2: Create Docker Compose Configuration

Create the docker-compose.yml file:

```bash
nano docker-compose.yml
```

Add this configuration:

```yaml
version: '3.8'

services:
  nginx-proxy-manager:
    image: 'jc21/nginx-proxy-manager:latest'
    container_name: nginx-proxy-manager
    restart: unless-stopped
    ports:
      # Public HTTP Port
      - '80:80'
      # Public HTTPS Port
      - '443:443'
      # Admin Web Port
      - '81:81'
    environment:
      DB_MYSQL_HOST: "npm-db"
      DB_MYSQL_PORT: 3306
      DB_MYSQL_USER: "npm_user"
      DB_MYSQL_PASSWORD: "CHANGE_THIS_SECURE_PASSWORD"
      DB_MYSQL_NAME: "npm_db"
      DISABLE_IPV6: 'true'
    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt
    networks:
      - proxy-network
    depends_on:
      - npm-db
    healthcheck:
      test: ["CMD", "/bin/check-health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  npm-db:
    image: 'jc21/mariadb-aria:latest'
    container_name: npm-db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: "CHANGE_THIS_ROOT_PASSWORD"
      MYSQL_DATABASE: "npm_db"
      MYSQL_USER: "npm_user"
      MYSQL_PASSWORD: "CHANGE_THIS_SECURE_PASSWORD"
    volumes:
      - ./mysql:/var/lib/mysql
    networks:
      - proxy-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  proxy-network:
    external: true
```

---

## Step 3: Generate Secure Passwords

Generate strong passwords for the database:

```bash
# Generate password for npm_user
openssl rand -base64 32

# Generate password for root
openssl rand -base64 32
```

**Important**: Copy these passwords and update them in the docker-compose.yml file:
- Replace `CHANGE_THIS_SECURE_PASSWORD` (appears twice - keep them the same)
- Replace `CHANGE_THIS_ROOT_PASSWORD`

Save the passwords securely for future reference.

---

## Step 4: Create Required Directories

```bash
# Create data directories
mkdir -p data letsencrypt mysql

# Set proper permissions
chmod -R 755 data letsencrypt
chmod -R 700 mysql
```

---

## Step 5: Deploy Nginx Proxy Manager

```bash
# Start the services
docker compose up -d

# Check if containers are running
docker compose ps

# View logs
docker compose logs -f
```

Wait for the services to start (about 30-60 seconds).

---

## Step 6: Access Nginx Proxy Manager Web Interface

Open your browser and navigate to:

```
http://YOUR_VPS_IP:81
```

**Default Login Credentials**:
- Email: `admin@example.com`
- Password: `changeme`

**IMPORTANT**: You will be prompted to change these credentials immediately after first login.

---

## Step 7: Initial Configuration

### Change Admin Credentials

1. Log in with default credentials
2. You'll be prompted to modify your details
3. Set new admin email and strong password
4. Save changes

### Recommended Settings

Navigate to **Settings** → **Default Site**:
- Set a default site or 404 page
- Configure SSL settings

---

## Step 8: Secure the Admin Port (Recommended)

After initial setup, restrict access to the admin port (81):

### Option 1: Restrict to Specific IP (Recommended)

```bash
# Allow admin port only from your IP
sudo ufw allow from YOUR_HOME_IP to any port 81 proto tcp comment 'NPM Admin'

# Check UFW status
sudo ufw status numbered
```

### Option 2: Change Admin Port

Edit docker-compose.yml:

```yaml
ports:
  - '80:80'
  - '443:443'
  - '8181:81'  # Changed from 81:81
```

Then restart:

```bash
docker compose down
docker compose up -d
```

### Option 3: Use SSH Tunnel (Most Secure)

Remove port 81 from docker-compose.yml and access via SSH tunnel:

```yaml
ports:
  - '80:80'
  - '443:443'
  # Remove: - '81:81'
```

From your local machine:

```powershell
# Create SSH tunnel
ssh -L 8181:localhost:81 deploy@YOUR_VPS_IP

# Access NPM at: http://localhost:8181
```

---

## Step 9: Configure Your First Proxy Host

### Example: Laravel Application

1. Navigate to **Hosts** → **Proxy Hosts**
2. Click **Add Proxy Host**
3. Fill in the details:

**Details Tab**:
- Domain Names: `example.com`, `www.example.com`
- Scheme: `http`
- Forward Hostname/IP: `laravel-app` (container name)
- Forward Port: `80`
- Cache Assets: ✓ (optional)
- Block Common Exploits: ✓
- Websockets Support: ✓ (if needed)

**SSL Tab**:
- SSL Certificate: Request a new SSL Certificate
- Force SSL: ✓
- HTTP/2 Support: ✓
- HSTS Enabled: ✓
- Email Address: your@email.com
- Agree to Let's Encrypt ToS: ✓

4. Click **Save**

NPM will automatically obtain and configure SSL certificate from Let's Encrypt.

---

## Step 10: Configure Access Lists (Optional)

Create access lists for protected applications:

1. Navigate to **Access Lists**
2. Click **Add Access List**
3. Configure:
   - Name: `Admin Access`
   - Satisfy Any: ✓ (allow if any condition matches)

**Authorization Tab**:
- Add username/password combinations

**Access Tab**:
- Allow: Add your IP addresses
- Deny: Add `all` to deny everyone else

4. Apply access list to proxy hosts as needed

---

## Step 11: Backup Nginx Proxy Manager

Create backup script:

```bash
nano ~/scripts/backup-npm.sh
```

Add this content:

```bash
#!/bin/bash
# Nginx Proxy Manager backup script

BACKUP_DIR="$HOME/backups/npm"
DATE=$(date +%Y%m%d_%H%M%S)
NPM_DIR="$HOME/docker/nginx-proxy-manager"

mkdir -p "$BACKUP_DIR"

echo "Backing up Nginx Proxy Manager..."

# Stop containers
cd "$NPM_DIR"
docker compose down

# Backup data
tar czf "$BACKUP_DIR/npm-data_$DATE.tar.gz" -C "$NPM_DIR" data letsencrypt mysql docker-compose.yml

# Start containers
docker compose up -d

echo "Backup complete: $BACKUP_DIR/npm-data_$DATE.tar.gz"

# Keep only last 7 backups
find "$BACKUP_DIR" -name "npm-data_*.tar.gz" -mtime +7 -delete
```

Make executable:

```bash
chmod +x ~/scripts/backup-npm.sh
```

---

## Step 12: Set Up Automated Backups

Create cron job for daily backups:

```bash
# Edit crontab
crontab -e
```

Add this line (backup daily at 2 AM):

```
0 2 * * * /home/deploy/scripts/backup-npm.sh >> /home/deploy/logs/npm-backup.log 2>&1
```

---

## Step 13: Monitor Nginx Proxy Manager

### View Logs

```bash
# View all logs
cd ~/docker/nginx-proxy-manager
docker compose logs -f

# View only NPM logs
docker compose logs -f nginx-proxy-manager

# View only database logs
docker compose logs -f npm-db
```

### Check Container Health

```bash
# Check container status
docker compose ps

# Check health status
docker inspect nginx-proxy-manager | grep -A 10 Health
```

---

## Verification Checklist

- [x] Nginx Proxy Manager container running
- [x] Database container running
- [x] Can access admin interface on port 81
- [x] Default credentials changed
- [x] Admin port secured (IP restriction or SSH tunnel)
- [x] Backup script created and tested
- [x] Automated backups scheduled

---

## Security Best Practices

1. **Always use SSL/TLS** - Enable Force SSL for all proxy hosts
2. **Restrict admin access** - Use IP whitelisting or SSH tunnel
3. **Use strong passwords** - For both NPM admin and database
4. **Regular backups** - Automated daily backups
5. **Monitor logs** - Check for suspicious activity
6. **Keep updated** - Regularly update NPM container

---

## Common Proxy Host Examples

### Static Website
```
Forward Hostname/IP: nginx-static
Forward Port: 80
```

### Laravel Application
```
Forward Hostname/IP: laravel-app
Forward Port: 80
Websockets: Enabled
```

### Spring Boot Application
```
Forward Hostname/IP: spring-app
Forward Port: 8080
```

### Python Telegram Bot (if has web interface)
```
Forward Hostname/IP: telegram-bot
Forward Port: 5000
```

---

## Troubleshooting

### Cannot Access Admin Interface

```bash
# Check if container is running
docker ps | grep nginx-proxy-manager

# Check logs
docker logs nginx-proxy-manager

# Verify port is open
sudo netstat -tulpn | grep :81
```

### SSL Certificate Issues

```bash
# Check Let's Encrypt logs
docker exec nginx-proxy-manager cat /data/logs/letsencrypt.log

# Verify domain DNS
nslookup your-domain.com

# Ensure port 80 is accessible
curl -I http://your-domain.com
```

### Database Connection Issues

```bash
# Check database container
docker logs npm-db

# Test database connection
docker exec -it npm-db mysql -u npm_user -p npm_db
```

---

## Next Steps

Proceed to [`05-DATABASE-SETUP.md`](05-DATABASE-SETUP.md) to set up MySQL and PostgreSQL databases.

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-07  
**Tested On**: Ubuntu 24.04 LTS with Nginx Proxy Manager 2.x
