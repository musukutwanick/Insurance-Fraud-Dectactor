"""Start server and write output to log file."""
import sys
import os
import logging

# Set up file logging before importing anything else
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_startup.log', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

try:
    logger.info("Starting server...")
    logger.info(f"Python: {sys.executable}")
    logger.info(f"CWD: {os.getcwd()}")
    
    # Test imports
    import fastapi
    logger.info(f"FastAPI: {fastapi.__version__}")
    import uvicorn
    logger.info(f"Uvicorn: {uvicorn.__version__}")
    
    # Try importing the app
    logger.info("Importing app...")
    from app.main import app
    logger.info("App imported successfully")
    
    # Start server
    logger.info("Starting uvicorn...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    
except Exception as e:
    logger.error(f"FATAL ERROR: {e}", exc_info=True)
    with open('server_startup.log', 'a') as f:
        import traceback
        f.write(f"\nFATAL ERROR: {e}\n")
        traceback.print_exc(file=f)
