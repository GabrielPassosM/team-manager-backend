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
PASSWORD_PEPPER = os.getenv("PASSWORD_PEPPER")
SALT_ROUNDS = int(os.getenv("SALT_ROUNDS"))
JWT_KEY = os.getenv("JWT_KEY")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
