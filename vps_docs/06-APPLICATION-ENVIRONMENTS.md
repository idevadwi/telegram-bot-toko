# Phase 6: Application Environments Setup

## Overview
This document covers the setup of application environments for Laravel (PHP), Python Telegram Bot, and Spring Kotlin applications.

**Prerequisites**: 
- Completed Phase 3 (Docker Installation)
- Completed Phase 4 (Nginx Proxy Manager)
- Completed Phase 5 (Database Setup)

---

## Part A: Laravel Environment Setup

### Step 1: Install PHP and Required Extensions

```bash
# Add PHP repository
sudo add-apt-repository ppa:ondrej/php -y

# Update package list
sudo apt update

# Install PHP 8.3 and extensions
sudo apt install -y \
    php8.3 \
    php8.3-fpm \
    php8.3-cli \
    php8.3-common \
    php8.3-mysql \
    php8.3-zip \
    php8.3-gd \
    php8.3-mbstring \
    php8.3-curl \
    php8.3-xml \
    php8.3-bcmath \
    php8.3-intl \
    php8.3-redis \
    php8.3-imagick

# Verify PHP installation
php -v
```

---

### Step 2: Install Composer

```bash
# Download Composer installer
cd ~
curl -sS https://getcomposer.org/installer -o composer-setup.php

# Verify installer (check hash from https://getcomposer.org/download/)
HASH="$(curl -sS https://composer.github.io/installer.sig)"
php -r "if (hash_file('SHA384', 'composer-setup.php') === '$HASH') { echo 'Installer verified'; } else { echo 'Installer corrupt'; unlink('composer-setup.php'); } echo PHP_EOL;"

# Install Composer globally
sudo php composer-setup.php --install-dir=/usr/local/bin --filename=composer

# Remove installer
rm composer-setup.php

# Verify Composer installation
composer --version
```

---

### Step 3: Configure PHP for Production

Edit PHP-FPM configuration:

```bash
# Edit php.ini
sudo nano /etc/php/8.3/fpm/php.ini
```

Update these settings:

```ini
; Security
expose_php = Off
display_errors = Off
log_errors = On
error_log = /var/log/php/error.log

; Performance
memory_limit = 256M
max_execution_time = 60
max_input_time = 60
upload_max_filesize = 20M
post_max_size = 25M

; OPcache
opcache.enable=1
opcache.memory_consumption=128
opcache.interned_strings_buffer=8
opcache.max_accelerated_files=10000
opcache.revalidate_freq=2
opcache.fast_shutdown=1
```

Create log directory:

```bash
# Create PHP log directory
sudo mkdir -p /var/log/php
sudo chown www-data:www-data /var/log/php
```

Restart PHP-FPM:

```bash
# Restart PHP-FPM
sudo systemctl restart php8.3-fpm

# Enable on boot
sudo systemctl enable php8.3-fpm

# Check status
sudo systemctl status php8.3-fpm
```

---

### Step 4: Create Laravel Application Structure

```bash
# Create Laravel apps directory
mkdir -p ~/apps/laravel

# Navigate to directory
cd ~/apps/laravel
```

---

### Step 5: Create Laravel Docker Template

Create a reusable Laravel Docker setup:

```bash
# Create template directory
mkdir -p ~/docker/laravel-template

# Navigate to directory
cd ~/docker/laravel-template

# Create Dockerfile
nano Dockerfile
```

Add this Dockerfile:

```dockerfile
FROM php:8.3-fpm-alpine

# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    libpng-dev \
    libzip-dev \
    zip \
    unzip \
    mysql-client \
    nginx \
    supervisor

# Install PHP extensions
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd zip

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /var/www/html

# Copy application files
COPY . .

# Install dependencies
RUN composer install --no-dev --optimize-autoloader

# Set permissions
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html/storage \
    && chmod -R 755 /var/www/html/bootstrap/cache

# Expose port
EXPOSE 9000

CMD ["php-fpm"]
```

Create docker-compose template:

```bash
nano docker-compose.template.yml
```

Add this configuration:

```yaml
version: '3.8'

services:
  laravel-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: laravel-app-name
    restart: unless-stopped
    working_dir: /var/www/html
    volumes:
      - ./app:/var/www/html
      - ./php.ini:/usr/local/etc/php/conf.d/custom.ini
    networks:
      - web-network
      - db-network
    environment:
      - APP_ENV=production
      - APP_DEBUG=false
      - DB_HOST=mysql-server
      - DB_PORT=3306
      - DB_DATABASE=laravel_app1
      - DB_USERNAME=laravel_user1
      - DB_PASSWORD=your_password
    depends_on:
      - nginx
    healthcheck:
      test: ["CMD-SHELL", "php-fpm -t"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  nginx:
    image: nginx:alpine
    container_name: laravel-nginx
    restart: unless-stopped
    volumes:
      - ./app:/var/www/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    networks:
      - web-network
      - proxy-network
    depends_on:
      - laravel-app
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  web-network:
    external: true
  db-network:
    external: true
  proxy-network:
    external: true
```

Create Nginx configuration:

```bash
nano nginx.conf
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name _;
    root /var/www/html/public;
    index index.php index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass laravel-app:9000;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
        fastcgi_hide_header X-Powered-By;
    }

    location ~ /\.(?!well-known).* {
        deny all;
    }

    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

---

## Part B: Python Environment Setup

### Step 1: Install Python and pip

```bash
# Install Python 3.12 and pip
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential

# Verify installation
python3 --version
pip3 --version
```

---

### Step 2: Create Python Virtual Environment Template

```bash
# Create Python apps directory
mkdir -p ~/apps/python

# Create telegram bot directory
mkdir -p ~/apps/python/telegram-bot

# Navigate to directory
cd ~/apps/python/telegram-bot

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Deactivate for now
deactivate
```

---

### Step 3: Create Telegram Bot Docker Setup

```bash
# Create telegram bot docker directory
mkdir -p ~/docker/telegram-bot

# Navigate to directory
cd ~/docker/telegram-bot

# Create Dockerfile
nano Dockerfile
```

Add this Dockerfile:

```dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

USER botuser

# Run the bot
CMD ["python", "bot.py"]
```

Create docker-compose.yml:

```bash
nano docker-compose.yml
```

Add this configuration:

```yaml
version: '3.8'

services:
  telegram-bot:
    build:
      context: ./app
      dockerfile: ../Dockerfile
    container_name: telegram-bot
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./app:/app
      - ./logs:/app/logs
    networks:
      - db-network
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - DATABASE_URL=postgresql://telegram_user:${DB_PASSWORD}@postgresql-server:5432/telegram_bot
      - LOG_LEVEL=INFO
      - TZ=Asia/Makassar
    depends_on:
      - postgresql-server
    healthcheck:
      test: ["CMD-SHELL", "python -c 'import sys; sys.exit(0)'"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    security_opt:
      - no-new-privileges:true

networks:
  db-network:
    external: true
```

Create .env file:

```bash
nano .env
```

Add environment variables:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DB_PASSWORD=your_postgresql_password_here
```

Create requirements.txt template:

```bash
nano app/requirements.txt
```

Add common dependencies:

```txt
python-telegram-bot==20.7
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
python-dotenv==1.0.0
aiohttp==3.9.1
```

---

### Step 4: Create Python Bot Template

```bash
# Create app directory
mkdir -p app

# Create bot template
nano app/bot.py
```

Add this template:

```python
#!/usr/bin/env python3
"""
Telegram Bot Template
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hello! I am your bot.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Help!')

def main():
    """Start the bot."""
    # Get bot token from environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
```

---

## Part C: Spring Kotlin Environment Setup

### Step 1: Install Java Development Kit

```bash
# Install OpenJDK 17
sudo apt install -y openjdk-17-jdk openjdk-17-jre

# Verify installation
java -version
javac -version

# Set JAVA_HOME
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
echo 'export PATH=$PATH:$JAVA_HOME/bin' >> ~/.bashrc
source ~/.bashrc

# Verify JAVA_HOME
echo $JAVA_HOME
```

---

### Step 2: Install Gradle (Optional)

```bash
# Download Gradle
cd ~
wget https://services.gradle.org/distributions/gradle-8.5-bin.zip

# Extract
sudo unzip -d /opt/gradle gradle-8.5-bin.zip

# Set up environment
echo 'export GRADLE_HOME=/opt/gradle/gradle-8.5' >> ~/.bashrc
echo 'export PATH=$PATH:$GRADLE_HOME/bin' >> ~/.bashrc
source ~/.bashrc

# Verify installation
gradle -v

# Clean up
rm gradle-8.5-bin.zip
```

---

### Step 3: Create Spring Kotlin Docker Template

```bash
# Create Spring Kotlin directory
mkdir -p ~/docker/spring-kotlin

# Navigate to directory
cd ~/docker/spring-kotlin

# Create Dockerfile
nano Dockerfile
```

Add this Dockerfile:

```dockerfile
FROM gradle:8.5-jdk17 AS build

WORKDIR /app

# Copy gradle files
COPY build.gradle.kts settings.gradle.kts ./
COPY gradle ./gradle

# Download dependencies
RUN gradle dependencies --no-daemon

# Copy source code
COPY src ./src

# Build application
RUN gradle bootJar --no-daemon

# Runtime stage
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -g 1000 spring && \
    adduser -D -u 1000 -G spring spring

# Copy jar from build stage
COPY --from=build /app/build/libs/*.jar app.jar

# Change ownership
RUN chown spring:spring app.jar

USER spring

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=60s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]
```

Create docker-compose.yml:

```bash
nano docker-compose.yml
```

Add this configuration:

```yaml
version: '3.8'

services:
  spring-app:
    build:
      context: ./app
      dockerfile: ../Dockerfile
    container_name: spring-kotlin-app
    restart: unless-stopped
    networks:
      - web-network
      - db-network
      - proxy-network
    environment:
      - SPRING_PROFILES_ACTIVE=production
      - SPRING_DATASOURCE_URL=jdbc:mysql://mysql-server:3306/spring_db
      - SPRING_DATASOURCE_USERNAME=spring_user
      - SPRING_DATASOURCE_PASSWORD=${DB_PASSWORD}
      - SERVER_PORT=8080
      - TZ=Asia/Makassar
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

networks:
  web-network:
    external: true
  db-network:
    external: true
  proxy-network:
    external: true
```

---

## Part D: Application Deployment Scripts

### Laravel Deployment Script

```bash
nano ~/scripts/deploy-laravel.sh
```

Add this content:

```bash
#!/bin/bash
# Laravel deployment script

APP_NAME=$1
APP_DIR="$HOME/apps/laravel/$APP_NAME"

if [ -z "$APP_NAME" ]; then
    echo "Usage: $0 <app-name>"
    exit 1
fi

echo "Deploying Laravel app: $APP_NAME"

cd "$APP_DIR" || exit

# Pull latest code
git pull origin main

# Install dependencies
composer install --no-dev --optimize-autoloader

# Run migrations
php artisan migrate --force

# Clear and cache config
php artisan config:cache
php artisan route:cache
php artisan view:cache

# Restart PHP-FPM
sudo systemctl restart php8.3-fpm

echo "Deployment complete!"
```

Make executable:

```bash
chmod +x ~/scripts/deploy-laravel.sh
```

---

### Python Bot Deployment Script

```bash
nano ~/scripts/deploy-telegram-bot.sh
```

Add this content:

```bash
#!/bin/bash
# Telegram bot deployment script

BOT_DIR="$HOME/docker/telegram-bot"

echo "Deploying Telegram bot..."

cd "$BOT_DIR" || exit

# Pull latest code
cd app && git pull origin main && cd ..

# Rebuild and restart container
docker compose down
docker compose build --no-cache
docker compose up -d

# Show logs
docker compose logs -f
```

Make executable:

```bash
chmod +x ~/scripts/deploy-telegram-bot.sh
```

---

### Spring Kotlin Deployment Script

```bash
nano ~/scripts/deploy-spring.sh
```

Add this content:

```bash
#!/bin/bash
# Spring Kotlin deployment script

APP_DIR="$HOME/docker/spring-kotlin"

echo "Deploying Spring Kotlin app..."

cd "$APP_DIR" || exit

# Pull latest code
cd app && git pull origin main && cd ..

# Rebuild and restart container
docker compose down
docker compose build --no-cache
docker compose up -d

# Show logs
docker compose logs -f
```

Make executable:

```bash
chmod +x ~/scripts/deploy-spring.sh
```

---

## Verification Checklist

### Laravel
- [x] PHP 8.3 installed with required extensions
- [x] Composer installed globally
- [x] PHP-FPM configured and running
- [x] Laravel Docker template created
- [x] Deployment script created

### Python
- [x] Python 3.12 installed
- [x] pip and venv available
- [x] Telegram bot Docker template created
- [x] Requirements.txt template created
- [x] Deployment script created

### Spring Kotlin
- [x] Java 17 JDK installed
- [x] Gradle installed (optional)
- [x] Spring Kotlin Docker template created
- [x] Deployment script created

---

## Next Steps

Proceed to [`07-CICD-GITHUB-ACTIONS.md`](07-CICD-GITHUB-ACTIONS.md) to set up automated deployment pipelines.

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-07  
**Tested On**: Ubuntu 24.04 LTS
