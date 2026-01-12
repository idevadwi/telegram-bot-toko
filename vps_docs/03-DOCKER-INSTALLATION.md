# Phase 3: Docker & Docker Compose Installation

## Overview
This document covers the secure installation and configuration of Docker and Docker Compose on Ubuntu 24.04.

**Prerequisites**: Completed Phase 1 (Initial Server Setup)  
**User**: Run as `deploy` user with sudo privileges

---

## Step 1: Remove Old Docker Versions

Remove any existing Docker installations:

```bash
# Remove old versions
sudo apt remove -y docker docker-engine docker.io containerd runc

# Clean up old data (optional, only if reinstalling)
# sudo rm -rf /var/lib/docker
# sudo rm -rf /var/lib/containerd
```

---

## Step 2: Install Docker Prerequisites

Install required packages:

```bash
# Update package index
sudo apt update

# Install prerequisites
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

---

## Step 3: Add Docker's Official GPG Key

```bash
# Create keyrings directory
sudo install -m 0755 -d /etc/apt/keyrings

# Download Docker's GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set permissions
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

---

## Step 4: Set Up Docker Repository

```bash
# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index
sudo apt update
```

---

## Step 5: Install Docker Engine

```bash
# Install Docker Engine, containerd, and Docker Compose plugin
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

**Expected Output**:
```
Docker version 24.x.x, build xxxxx
Docker Compose version v2.x.x
```

---

## Step 6: Configure Docker User Permissions

Add deploy user to docker group:

```bash
# Add current user to docker group
sudo usermod -aG docker $USER

# Verify group membership
groups $USER
```

**Important**: Log out and log back in for group changes to take effect:

```bash
# Exit current session
exit

# SSH back in
ssh deploy@YOUR_VPS_IP

# Verify docker access without sudo
docker ps
```

---

## Step 7: Configure Docker Daemon for Security

Create Docker daemon configuration:

```bash
# Create daemon.json
sudo nano /etc/docker/daemon.json
```

Add this configuration:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true,
  "icc": false,
  "default-address-pools": [
    {
      "base": "172.17.0.0/16",
      "size": 24
    }
  ]
}
```

**Configuration Explanation**:
- `log-driver`: JSON file logging
- `max-size`: Maximum log file size (10MB)
- `max-file`: Keep 3 log files
- `live-restore`: Keep containers running during daemon downtime
- `userland-proxy`: Disable userland proxy for better performance
- `no-new-privileges`: Prevent privilege escalation
- `icc`: Disable inter-container communication by default
- `default-address-pools`: Custom IP range for containers

Restart Docker to apply changes:

```bash
# Restart Docker daemon
sudo systemctl restart docker

# Verify Docker is running
sudo systemctl status docker

# Test Docker
docker run hello-world
```

---

## Step 8: Enable Docker Service on Boot

```bash
# Enable Docker service
sudo systemctl enable docker

# Enable containerd service
sudo systemctl enable containerd

# Verify services are enabled
systemctl is-enabled docker
systemctl is-enabled containerd
```

---

## Step 9: Create Docker Network for Applications

Create custom networks for better isolation:

```bash
# Create network for web applications
docker network create \
  --driver bridge \
  --subnet=172.20.0.0/16 \
  --gateway=172.20.0.1 \
  web-network

# Create network for databases
docker network create \
  --driver bridge \
  --subnet=172.21.0.0/16 \
  --gateway=172.21.0.1 \
  db-network

# Create network for Nginx Proxy Manager
docker network create \
  --driver bridge \
  --subnet=172.22.0.0/16 \
  --gateway=172.22.0.1 \
  proxy-network

# List networks
docker network ls
```

**Network Strategy**:
- `proxy-network`: Nginx Proxy Manager and exposed services
- `web-network`: Web applications (Laravel, Spring)
- `db-network`: Databases (MySQL, PostgreSQL)

---

## Step 10: Create Docker Directory Structure

```bash
# Create main docker directory
mkdir -p ~/docker

# Create subdirectories for each service
mkdir -p ~/docker/nginx-proxy-manager
mkdir -p ~/docker/mysql
mkdir -p ~/docker/postgresql
mkdir -p ~/docker/laravel
mkdir -p ~/docker/telegram-bot
mkdir -p ~/docker/spring-kotlin

# Create shared volumes directory
mkdir -p ~/docker/volumes

# Set permissions
chmod -R 755 ~/docker
```

---

## Step 11: Install Docker Compose Standalone (Optional)

While Docker Compose plugin is installed, you may want standalone version:

```bash
# Download latest Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

**Note**: Use `docker compose` (plugin) or `docker-compose` (standalone) - both work the same.

---

## Step 12: Configure Docker Logging with Logrotate

Create logrotate configuration for Docker:

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/docker
```

Add this configuration:

```
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
```

Test logrotate:

```bash
# Test logrotate configuration
sudo logrotate -f /etc/logrotate.d/docker
```

---

## Step 13: Install Docker Security Tools

Install Docker Bench Security:

```bash
# Clone Docker Bench Security
cd ~/docker
git clone https://github.com/docker/docker-bench-security.git

# Run security audit
cd docker-bench-security
sudo sh docker-bench-security.sh
```

Review the output for security recommendations.

---

## Step 14: Configure Docker Resource Limits

Create default resource limits:

```bash
# Edit Docker daemon config
sudo nano /etc/docker/daemon.json
```

Update with resource limits:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true,
  "icc": false,
  "default-address-pools": [
    {
      "base": "172.17.0.0/16",
      "size": 24
    }
  ],
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
```

Restart Docker:

```bash
sudo systemctl restart docker
```

---

## Step 15: Create Docker Compose Template

Create a template for future services:

```bash
# Create template file
nano ~/docker/docker-compose.template.yml
```

Add this template:

```yaml
version: '3.8'

services:
  service-name:
    image: image:tag
    container_name: service-name
    restart: unless-stopped
    networks:
      - network-name
    environment:
      - ENV_VAR=value
    volumes:
      - ./data:/data
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

networks:
  network-name:
    external: true

volumes:
  data-volume:
    driver: local
```

---

## Step 16: Create Docker Management Scripts

Create useful management scripts:

### Script 1: Docker Cleanup

```bash
# Create cleanup script
nano ~/scripts/docker-cleanup.sh
```

Add this content:

```bash
#!/bin/bash
# Docker cleanup script

echo "Cleaning up Docker resources..."

# Remove stopped containers
echo "Removing stopped containers..."
docker container prune -f

# Remove unused images
echo "Removing unused images..."
docker image prune -a -f

# Remove unused volumes
echo "Removing unused volumes..."
docker volume prune -f

# Remove unused networks
echo "Removing unused networks..."
docker network prune -f

# Show disk usage
echo "Current Docker disk usage:"
docker system df

echo "Cleanup complete!"
```

Make executable:

```bash
chmod +x ~/scripts/docker-cleanup.sh
```

### Script 2: Docker Backup

```bash
# Create backup script
nano ~/scripts/docker-backup.sh
```

Add this content:

```bash
#!/bin/bash
# Docker volume backup script

BACKUP_DIR="$HOME/backups/docker"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Backing up Docker volumes..."

# List all volumes
VOLUMES=$(docker volume ls -q)

for volume in $VOLUMES; do
    echo "Backing up volume: $volume"
    docker run --rm \
        -v "$volume:/data" \
        -v "$BACKUP_DIR:/backup" \
        ubuntu tar czf "/backup/${volume}_${DATE}.tar.gz" -C /data .
done

echo "Backup complete! Files saved to: $BACKUP_DIR"
```

Make executable:

```bash
chmod +x ~/scripts/docker-backup.sh
```

### Script 3: Docker Monitor

```bash
# Create monitoring script
nano ~/scripts/docker-monitor.sh
```

Add this content:

```bash
#!/bin/bash
# Docker monitoring script

echo "=== Docker System Info ==="
docker version

echo -e "\n=== Running Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n=== Container Resource Usage ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo -e "\n=== Docker Disk Usage ==="
docker system df

echo -e "\n=== Docker Networks ==="
docker network ls

echo -e "\n=== Docker Volumes ==="
docker volume ls
```

Make executable:

```bash
chmod +x ~/scripts/docker-monitor.sh
```

---

## Step 17: Set Up Docker Monitoring with cAdvisor (Optional)

Deploy cAdvisor for container monitoring:

```bash
# Create cAdvisor directory
mkdir -p ~/docker/cadvisor

# Create docker-compose.yml
nano ~/docker/cadvisor/docker-compose.yml
```

Add this configuration:

```yaml
version: '3.8'

services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    restart: unless-stopped
    privileged: true
    devices:
      - /dev/kmsg
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "8080:8080"
    networks:
      - proxy-network

networks:
  proxy-network:
    external: true
```

**Note**: We'll expose cAdvisor through Nginx Proxy Manager later.

---

## Verification Checklist

Run these commands to verify Docker installation:

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker compose version

# Check Docker service status
sudo systemctl status docker

# Check Docker info
docker info

# List Docker networks
docker network ls

# Check user can run Docker without sudo
docker ps

# Run test container
docker run --rm hello-world

# Check Docker disk usage
docker system df

# List running containers
docker ps -a
```

---

## Security Checklist

- [x] Docker installed from official repository
- [x] Deploy user added to docker group
- [x] Docker daemon configured with security options
- [x] Log rotation configured
- [x] Resource limits set
- [x] Custom networks created for isolation
- [x] No-new-privileges enabled
- [x] Inter-container communication disabled by default
- [x] Docker service enabled on boot
- [x] Management scripts created

---

## Docker Security Best Practices

### 1. Never Run Containers as Root
```yaml
user: "1000:1000"  # Use non-root user
```

### 2. Use Read-Only Filesystems When Possible
```yaml
read_only: true
tmpfs:
  - /tmp
```

### 3. Limit Container Resources
```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

### 4. Use Specific Image Tags
```yaml
image: nginx:1.25.3  # Not nginx:latest
```

### 5. Scan Images for Vulnerabilities
```bash
# Install Trivy
sudo apt install -y wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt update
sudo apt install -y trivy

# Scan an image
trivy image nginx:latest
```

---

## Common Docker Commands Reference

### Container Management
```bash
# List running containers
docker ps

# List all containers
docker ps -a

# Start container
docker start container-name

# Stop container
docker stop container-name

# Restart container
docker restart container-name

# Remove container
docker rm container-name

# View container logs
docker logs container-name

# Follow container logs
docker logs -f container-name

# Execute command in container
docker exec -it container-name bash
```

### Image Management
```bash
# List images
docker images

# Pull image
docker pull image:tag

# Remove image
docker rmi image:tag

# Build image
docker build -t image:tag .

# Tag image
docker tag source:tag target:tag
```

### Network Management
```bash
# List networks
docker network ls

# Inspect network
docker network inspect network-name

# Connect container to network
docker network connect network-name container-name

# Disconnect container from network
docker network disconnect network-name container-name
```

### Volume Management
```bash
# List volumes
docker volume ls

# Create volume
docker volume create volume-name

# Inspect volume
docker volume inspect volume-name

# Remove volume
docker volume rm volume-name
```

### Docker Compose Commands
```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# Restart services
docker compose restart

# Pull latest images
docker compose pull

# Rebuild services
docker compose up -d --build
```

---

## Troubleshooting

### Cannot connect to Docker daemon
```bash
# Check Docker service
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Check user groups
groups $USER

# Re-login if needed
exit
```

### Permission denied errors
```bash
# Ensure user is in docker group
sudo usermod -aG docker $USER

# Log out and back in
exit
```

### Container networking issues
```bash
# Check network
docker network inspect network-name

# Restart Docker networking
sudo systemctl restart docker
```

### Disk space issues
```bash
# Check disk usage
docker system df

# Clean up
docker system prune -a

# Remove specific items
docker container prune
docker image prune -a
docker volume prune
```

---

## Next Steps

Proceed to [`04-NGINX-PROXY-MANAGER.md`](04-NGINX-PROXY-MANAGER.md) to set up the web server management interface.

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-07  
**Tested On**: Ubuntu 24.04 LTS with Docker 24.x
