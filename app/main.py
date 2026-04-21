import logging
from fastapi import FastAPI, Request, Response

# logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
def read_root():
    try:
        return {"message": "app running"}
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}")
        return Response(content="error", status_code=500)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response
