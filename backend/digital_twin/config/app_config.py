import os
from dotenv import load_dotenv

load_dotenv()
IS_DEV = os.environ.get("IS_DEV", "false").lower() == "true" 
#####################
# DB Configurations #
#####################
SUPABASE_URL=os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

#####################
# Authentication    #
#####################
# This is out front-end URL
WEB_DOMAIN=os.environ.get("WEB_DOMAIN", "http://localhost:3000")
# This is the backend URL
APP_HOST = os.environ.get("APP_HOST", "localhost")
APP_PORT = os.environ.get("APP_PORT", 8080)
JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"


#####################
# VectorDB Config   #
#####################
DEFAULT_VECTOR_STORE = os.environ.get("VECTOR_DB", "qdrant")
QDRANT_API_KEY=os.environ.get("QDRANT_API_KEY", "")
QDRANT_URL=os.environ.get("QDRANT_URL", "")
QDRANT_DEFAULT_COLLECTION=os.environ.get("QDRANT_DEFAULT_COLLECTION", "testing")

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

NUM_RETURNED_VECTORDB_HITS = 15
# Better to keep it loose, surfacing more results better than missing results
SEARCH_DISTANCE_CUTOFF = 0.1  # Cosine similarity (currently), range of -1 to 1 with -1 being completely opposite

# More accurate results at the expense of indexing speed 
# and index size (stores additional 4 MINI_CHUNK vectors)
ENABLE_MINI_CHUNK = False
# Mini chunks for fine-grained embedding, 
# calculated as 128 tokens for 4 additional vectors for 512 chunk size above
# Not rounded down to not lose any context in full chunk.
MINI_CHUNK_SIZE = 512



########################
# Slack Configurations #
########################
SLACK_BOT_TOKEN=os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_USER_TOKEN=os.environ.get("SLACK_USER_TOKEN", "")
SLACK_CLIENT_ID=os.environ.get("SLACK_CLIENT_ID", "")
SLACK_CLIENT_SECRET=os.environ.get("SLACK_CLIENT_SECRET", "")
SLACK_SIGNING_SECRET=os.environ.get("SLACK_SIGNING_SECRET", "")
SLACK_REDIRECT_URI=os.environ.get("SLACK_REDIRECT_URI", f"https://{APP_HOST}:{APP_PORT}/slack/oauth_redirect")

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
MIN_SCRAPED_THRESHOLD = 5


#####################
# MODEL API Keys    #
#####################
DEFAULT_LLM = os.environ.get("DEFAULT_LLM", "GPT3_5")
PERSONALITY_CHAIN_API_KEY="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"
OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY="XXXXXX"

#####################
# Connector Configs #
#####################
GOOGLE_DRIVE_INCLUDE_SHARED = False
