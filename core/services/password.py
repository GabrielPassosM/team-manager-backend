import bcrypt

from core.settings import PASSWORD_PEPPER, SALT_ROUNDS


def hash_password(password: str) -> str:
    peppered_password = (PASSWORD_PEPPER + password).encode()
    hashed_password = bcrypt.hashpw(
        peppered_password, bcrypt.gensalt(rounds=SALT_ROUNDS)
    )
    return hashed_password.decode()


def verify_password(password_sent: str, password_db: str) -> bool:
    peppered_password = (PASSWORD_PEPPER + password_sent).encode()
    return bcrypt.checkpw(peppered_password, password_db.encode())
