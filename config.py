from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

# Sentry Configuration
SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")

# CORS Origins Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080,http://localhost:8000,https://www.workman.so,https://app.workman.so,https://workman-website-git-development-daniel442li.vercel.app").split(",")
# Other configurations as needed
HTML_PATH = os.getenv("HTML_PATH")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
