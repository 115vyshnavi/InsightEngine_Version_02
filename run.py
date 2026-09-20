#!/usr/bin/env python3
"""InsightEngine Server Startup Script."""

import uvicorn
from app.core.config import settings
from app.core.logging import logger

if __name__ == "__main__":
    logger.info(f"Launching InsightEngine API on http://{settings.HOST}:{settings.PORT} ...")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
