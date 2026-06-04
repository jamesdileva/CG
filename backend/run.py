#!/usr/bin/env python
"""Development runner for AI Documentary Studio backend"""
import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
