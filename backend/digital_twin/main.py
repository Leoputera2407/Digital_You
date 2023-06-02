import uvicorn

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from digital_twin.config.app_config import APP_HOST, APP_PORT
from digital_twin.server.slack_event import router as slack_event_router
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logger.exception(f"{request}: {exc_str}")
    content = {"status_code": 422, "message": exc_str, "data": None}
    return JSONResponse(content=content, status_code=422)


def get_application() -> FastAPI:
    application = FastAPI(
        title="Digital Twin", debug=True, version="0.1"
    )
    application.include_router(slack_event_router)


    application.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )

    @application.on_event("startup")
    def startup_event() -> None:
        # To avoid circular imports
        from digital_twin.config.app_config import (
            QDRANT_DEFAULT_COLLECTION,
        )
        from digital_twin.vectordb.qdrant.indexing import (
            create_collection,
            list_collections,
        )

        if QDRANT_DEFAULT_COLLECTION not in {
            collection.name for collection in list_collections().collections
        }:
            logger.info(
                f"Creating collection with name: {QDRANT_DEFAULT_COLLECTION}"
            )
            create_collection(collection_name=QDRANT_DEFAULT_COLLECTION)

    return application


# Create the FastAPI application
app = get_application()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"  # Change this to the list of allowed origins if needed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    logger.info(f"Running QA Service on http://{APP_HOST}:{str(APP_PORT)}/")
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)