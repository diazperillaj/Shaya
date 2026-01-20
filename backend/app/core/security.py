from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Genera un hash seguro de una contraseña utilizando bcrypt.

    La contraseña se convierte a bytes UTF-8 y se trunca a 72 bytes,
    debido a la limitación interna del algoritmo bcrypt.

    Args:
        password (str): Contraseña en texto plano.

    Returns:
        str: Hash seguro de la contraseña.
    """

    password_bytes = password.encode("utf-8")[:72]
    return pwd_context.hash(password_bytes)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña en texto plano contra su hash almacenado.
    """
    plain_bytes = plain_password.encode("utf-8")[:72]
    return pwd_context.verify(plain_bytes, hashed_password)
