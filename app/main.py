import logging
from fastapi import FastAPI, Request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
def read_root():
    logger.info("Root endpoint called")
    return {"message": "app running"}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")

    response = await call_next(request)

    logger.info(f"Response status: {response.status_code}")
    return response

