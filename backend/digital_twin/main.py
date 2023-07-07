import uvicorn
import nltk

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from digital_twin.config.app_config import APP_HOST, APP_PORT, WEB_DOMAIN
from digital_twin.server.slack_event import router as slack_event_router
from digital_twin.server.account import router as account_router
from digital_twin.server.connector_admin import router as connector_admin_router
from digital_twin.server.connector_user import router as connector_user_router
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
    application.include_router(account_router)
    application.include_router(connector_admin_router)
    application.include_router(connector_user_router)

    application.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )

    @application.on_event("startup")
    def startup_event() -> None:
        # To avoid circular imports
        from digital_twin.config.app_config import (
            QDRANT_DEFAULT_COLLECTION,
            TYPESENSE_DEFAULT_COLLECTION,
        )
        from digital_twin.indexdb.qdrant.indexing import (
            create_collection,
            list_collections,
        )
        from digital_twin.indexdb.typesense.store import (
            check_typesense_collection_exist,
            create_typesense_collection,
        )

        nltk.download("stopwords")
        nltk.download("wordnet")
        nltk.download("punkt")

        if QDRANT_DEFAULT_COLLECTION not in {
            collection.name for collection in list_collections().collections
        }:
            logger.info(
                f"Creating collection with name: {QDRANT_DEFAULT_COLLECTION}"
            )
            create_collection(collection_name=QDRANT_DEFAULT_COLLECTION)
        
        if not check_typesense_collection_exist(TYPESENSE_DEFAULT_COLLECTION):
            logger.info(
                f"Creating Typesense collection with name: {TYPESENSE_DEFAULT_COLLECTION}"
            )
            create_typesense_collection(collection_name=TYPESENSE_DEFAULT_COLLECTION)

    return application


# Create the FastAPI application
app = get_application()

allowed_origins = [
    # TODO:  Replace with your Next.js app's domain
    "http://localhost:3000", 
    "https://localhost:8080",
    WEB_DOMAIN,
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    logger.info(f"Running QA Service on http://{APP_HOST}:{str(APP_PORT)}/")
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)