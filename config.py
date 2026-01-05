import os
from dotenv import load_dotenv

load_dotenv()

# Your LinkedIn App's Client ID & Client Secret
CLIENT_ID = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")

# Access Token (get using OAuth flow)
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

# Organization ID (Company Page ID)
ORGANIZATION_ID = os.getenv("ORGANIZATION_ID", "")

# LinkedIn API version
LINKEDIN_API_VERSION = os.getenv("LINKEDIN_API_VERSION", "202502")  # always use latest

REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5000/callback")
SECRET_KEY = os.getenv("SECRET_KEY", "dev")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./oauth_tokens.sqlite")
