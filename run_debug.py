import sys
import logging
import traceback

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, force=True)

try:
    import uvicorn
    from app.main import app
    print("Starting uvicorn...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
