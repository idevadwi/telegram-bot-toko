# ModuleNotFoundError Fix - Docker Import Issue

## Problem Description

After running `docker compose up`, the Telegram bot container was failing to start with the following error:

```
ModuleNotFoundError: No module named 'core'
```

The error occurred in `/app/src/bot/bot.py` at line 10 when trying to import:
```python
from core.config import load_config
```

## Root Cause Analysis

The issue was a Python path configuration problem in the Docker container:

1. **Original Configuration**: The [`Dockerfile`](../docker/Dockerfile) set `PYTHONPATH=/app`
2. **Module Location**: The `core` module is located at `/app/src/core/`
3. **Import Statement**: The code uses `from core.config import load_config`, which expects `core` to be directly in the Python path
4. **Mismatch**: With `PYTHONPATH=/app`, Python could not find the `core` module because it was actually at `/app/src/core/`

## The Fix

Changed the PYTHONPATH environment variable in [`docker/Dockerfile`](../docker/Dockerfile:22) from:
```dockerfile
ENV PYTHONPATH=/app
```

To:
```dockerfile
ENV PYTHONPATH=/app:/app/src
```

This adds `/app/src` to the Python path, allowing Python to find the `core` module when the import statement is executed.

## How to Apply the Fix

### Step 1: Stop and Remove Existing Containers

From the `docker` directory:
```bash
cd ~/apps/telegram-bot-toko/docker
docker compose down
```

### Step 2: Rebuild the Docker Image

Since the Dockerfile was modified, you need to rebuild the image:
```bash
docker compose build --no-cache
```

### Step 3: Start the Containers

```bash
docker compose up -d
```

### Step 4: Verify the Fix

Check the logs to ensure the bot starts successfully:
```bash
docker compose logs -f
```

You should see the bot starting without the `ModuleNotFoundError`. The logs should show something like:
```
telegram-bot-toko  | Bot is running...
```

## Alternative Solutions

If you prefer not to modify PYTHONPATH, you could also:

### Option 1: Use Relative Imports
Change imports in [`src/bot/bot.py`](../src/bot/bot.py) from:
```python
from core.config import load_config
```
To:
```python
from ..core.config import load_config
```

### Option 2: Change Working Directory
Modify the CMD in Dockerfile to run from `/app/src`:
```dockerfile
WORKDIR /app/src
CMD ["python", "-m", "bot.bot"]
```

However, the PYTHONPATH solution is the cleanest approach as it maintains the current import structure and allows both absolute and relative imports to work correctly.

## Verification Checklist

- [ ] Docker image rebuilt successfully
- [ ] Container starts without errors
- [ ] Bot responds to `/start` command
- [ ] Bot can search products
- [ ] No `ModuleNotFoundError` in logs

## Related Files

- [`docker/Dockerfile`](../docker/Dockerfile) - Modified PYTHONPATH configuration
- [`docker/docker-compose.yml`](../docker/docker-compose.yml) - Container orchestration
- [`src/bot/bot.py`](../src/bot/bot.py) - Main bot entry point with imports
- [`src/core/config.py`](../src/core/config.py) - Configuration module being imported
