import os
from dotenv import load_dotenv

load_dotenv()
IS_DEV = os.environ.get("IS_DEV", "false").lower() == "true" 
#####################
# DB Configurations #
#####################
SUPABASE_URL=os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
# below are intended to match the env variables names used by the official postgres docker image
# https://hub.docker.com/_/postgres
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "password")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")

#####################
# Authentication    #
#####################
# This is out front-end URL
WEB_DOMAIN=os.environ.get("WEB_DOMAIN", "http://localhost:3000")
# This is the backend URL
APP_HOST = os.environ.get("APP_HOST", "localhost")
APP_PORT = os.environ.get("APP_PORT", 8080)
JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", "")
DISABLE_AUTHENTICATION = os.environ.get("DISABLE_AUTHENTICATION", "false").lower() == "true" 
JWT_ALGORITHM = "HS256"


#####################
# VectorDB Config   #
#####################
DEFAULT_VECTOR_STORE = os.environ.get("VECTOR_DB", "qdrant")

QDRANT_API_KEY=os.environ.get("QDRANT_API_KEY", "")
QDRANT_URL=os.environ.get("QDRANT_URL", "")
QDRANT_DEFAULT_COLLECTION=os.environ.get("QDRANT_DEFAULT_COLLECTION", "testing")
# Host / Port are used for connecting to local Qdrant instance
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = 6333

# The first few sentences for each Section in a Chunk
BLURB_LENGTH = 500 
# Chunking docs to this number of characters not including finishing the last word and the overlap words below
# Calculated by ~4000 to 8192 tokens max * average 4 chars per token
# I'll be consersative and pick 2000 tokens
CHUNK_SIZE = 8000
BATCH_SIZE_ENCODE_CHUNKS = 8
# Each chunk includes an additional 5 `words` from previous chunk
# in extreme cases, may cause some words at the end to be truncated by embedding model
CHUNK_OVERLAP = 5
# Number of documents in a batch during indexing (further batching done by chunks before passing to bi-encoder)
INDEX_BATCH_SIZE = 16

NUM_RETURNED_HITS = 100
NUM_RERANKED_RESULTS = 15
# Better to keep it loose, surfacing more results better than missing results
SEARCH_DISTANCE_CUTOFF = 0.1  # Cosine similarity (currently), range of -1 to 1 with -1 being completely opposite

# More accurate results at the expense of indexing speed 
# and index size (stores additional 4 MINI_CHUNK vectors)
ENABLE_MINI_CHUNK = False
# Mini chunks for fine-grained embedding, 
# calculated as 128 tokens for 4 additional vectors for 512 chunk size above
# Not rounded down to not lose any context in full chunk.
MINI_CHUNK_SIZE = 512



#########################
# Keyword Search Config #
#########################
TYPESENSE_DEFAULT_COLLECTION = os.environ.get(
    "TYPESENSE_DEFAULT_COLLECTION", "testing"
)
TYPESENSE_HOST = os.environ.get("TYPESENSE_HOST", "localhost")
TYPESENSE_PORT = os.environ.get("TYPESENSE_PORT", 8108)
TYPESENSE_PROTOCOL = os.environ.get("TYPESENSE_PROTOCOL", "http")
TYPESENSE_API_KEY = os.environ.get("TYPESENSE_API_KEY", "")


########################
# Slack Configurations #
########################
SLACK_BOT_TOKEN=os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_USER_TOKEN=os.environ.get("SLACK_USER_TOKEN", "")
SLACK_CLIENT_ID=os.environ.get("SLACK_CLIENT_ID", "")
SLACK_CLIENT_SECRET=os.environ.get("SLACK_CLIENT_SECRET", "")
SLACK_SIGNING_SECRET=os.environ.get("SLACK_SIGNING_SECRET", "")
SLACK_REDIRECT_URI=os.environ.get("SLACK_REDIRECT_URI", f"https://{APP_HOST}:{APP_PORT}/slack/oauth_redirect")
NUM_SLACK_CHAT_PAIRS_TO_SHOW=10
SLACK_DAYS_TO_RESCRAPE=30

#########################
# Notion Configurations #
#########################
NOTION_CLIENT_ID=os.environ.get("NOTION_CLIENT_ID", "")
NOTION_CLIENT_SECRET=os.environ.get("NOTION_CLIENT_SECRET", "")


#####################
# QA Config         #
#####################
# OPENAI
DOC_EMBEDDING_DIM = 1536
NUM_DOCS=5
MIN_SCRAPED_THRESHOLD = 5 # 80 letters
MIN_CHAT_PAIRS_THRESHOLD = 5
DEFAULT_QA_TIMEOUT = 10


#####################
# MODEL API Keys    #
#####################
DEFAULT_MODEL_TYPE = os.environ.get("DEFAULT_LLM", "AZURE")
MODEL_API_KEY = os.environ.get("MODEL_API_KEY", "")
EMBEDDING_OPENAI_API_KEY = os.environ.get("EMBEDDING_OPENAI_API_KEY", "")

#######################
# EMAIL Sender Config #
#######################
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "your-email@gmail.com")
# Remember, if this is for gmail, this should be your app password, not your email password
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "your-gmail-password")


#####################
# Cohere API Keys    #
#####################
COHERE_KEY=os.environ.get("COHERE_KEY", "")

#####################
# Connector Configs #
#####################
GOOGLE_DRIVE_INCLUDE_SHARED = False
