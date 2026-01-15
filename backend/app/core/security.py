from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    # Convertir a bytes UTF-8 y truncar 72 bytes
    password_bytes = password.encode("utf-8")[:72]
    return pwd_context.hash(password_bytes)
