#!/usr/bin/env python
"""Development runner for AI Documentary Studio backend"""
import uvicorn
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    # Add project root to path so imports work
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    os.chdir(project_root)

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
