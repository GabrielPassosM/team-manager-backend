import os

from dotenv import load_dotenv


load_dotenv()

# Infra
DATABASE_URL = os.getenv("DATABASE_URL")
ENV_CONFIG = os.getenv("ENV_CONFIG")

# Security
MIGRATIONS_PWD = os.getenv("MIGRATIONS_PWD")
SWAGGER_USERNAME = os.getenv("SWAGGER_USERNAME")
SWAGGER_PASSWORD = os.getenv("SWAGGER_PASSWORD")
