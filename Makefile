.PHONY: help install test run bot sync clean docker-build docker-up docker-down health-check monitor backup backup-config

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run tests
	pytest tests/ -v

run: ## Run the bot
	python -m src.bot.bot

sync: ## Run sync process
	python scripts/sync.py

bot: ## Run bot in background
	nohup python -m src.bot.bot > logs/bot.log 2>&1 &

clean: ## Clean up
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker images
	docker-compose -f docker/docker-compose.yml build

docker-up: ## Start Docker containers
	docker-compose -f docker/docker-compose.yml up -d

docker-down: ## Stop Docker containers
	docker-compose -f docker/docker-compose.yml down

docker-logs: ## Show Docker logs
	docker-compose -f docker/docker-compose.yml logs -f

health-check: ## Run health check script
	./scripts/health_check.sh

monitor: ## Run monitoring script
	./scripts/monitor.sh

backup: ## Run manual backup script
	./scripts/backup.sh

backup-config: ## Backup configuration files
	./scripts/backup_config.sh
