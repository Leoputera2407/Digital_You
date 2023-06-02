import os
from dotenv import load_dotenv

load_dotenv()
#####################
# DB Configurations #
#####################
DEFAULT_VECTOR_STORE = os.environ.get("VECTOR_DB", "qdrant")
SUPABASE_URL=os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
QDRANT_API_KEY=os.environ.get("QDRANT_API_KEY", "")
QDRANT_URL=os.environ.get("QDRANT_URL", "")
QDRANT_DEFAULT_COLLECTION=os.environ.get("QDRANT_DEFAULT_COLLECTION", "testing")



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


########################
# Slack Configurations #
########################
SLACK_BOT_TOKEN=os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CLIENT_ID=os.environ.get("SLACK_CLIENT_ID", "")
SLACK_CLIENT_SECRET=os.environ.get("SLACK_CLIENT_SECRET", "")
SLACK_SIGNING_SECRET=os.environ.get("SLACK_SIGNING_SECRET", "")
SLACK_REDIRECT_URI=os.environ.get("SLACK_REDIRECT_URI", f"https://{APP_HOST}:{APP_PORT}/slack/oauth_redirect")

#####################
# QA Config         #
#####################
# OPENAI
DOC_EMBEDDING_DIM = 1536
# The first few sentences for each Section in a Chunk
BLURB_LENGTH = 200 
# Chunking docs to this number of characters not including finishing the last word and the overlap words below
# Calculated by ~4000 to 8192 tokens max * average 4 chars per token
# I'll be consersative and pick 4000 tokens
CHUNK_SIZE = 16000
# Each chunk includes an additional 5 `words` from previous chunk
# in extreme cases, may cause some words at the end to be truncated by embedding model
CHUNK_OVERLAP = 5
NUM_RETURNED_VECTORDB_HITS = 15
NUM_DOCS=5
MIN_SCRAPED_THRESHOLD = 5



#####################
# MODEL API Keys    #
#####################
DEFAULT_LLM = os.environ.get("DEFAULT_LLM", "GPT3_5")
PERSONALITY_CHAIN_API_KEY="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"
OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY="XXXXXX"

