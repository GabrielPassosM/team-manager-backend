import os

from dotenv import load_dotenv


load_dotenv()

# Infra
DATABASE_URL = os.getenv("DATABASE_URL")
MIGRATIONS_PWD = os.getenv("MIGRATIONS_PWD")
