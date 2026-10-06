"""
Crea un usuario administrador en una base nueva (p. ej. el entorno de demo).

    python -m scripts.create_admin --username admin --name "Administración Shaya"

La contraseña se pide por la terminal (no queda en el historial ni en el
comando). Si el usuario ya existe, no cambia nada.
"""

import argparse
import getpass
import sys
from typing import Optional

from app import models_registry  # noqa: F401
from app.core.db.base import engine
from app.core.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models.person import Person
from app.models.user import User

MIN_LENGTH = 8


def main(argv: Optional[list] = None) -> int:
    engine.echo = False
    parser = argparse.ArgumentParser(description="Crea un usuario administrador")
    parser.add_argument("--username", required=True, help="nombre de usuario para iniciar sesión")
    parser.add_argument("--name", default="Administrador", help="nombre completo (Administrador)")
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == args.username).first():
            print(f"✗ El usuario «{args.username}» ya existe: no se cambió nada.", file=sys.stderr)
            return 1
        password = getpass.getpass("Contraseña: ")
        if len(password) < MIN_LENGTH:
            print(f"✗ La contraseña debe tener al menos {MIN_LENGTH} caracteres.", file=sys.stderr)
            return 1
        if getpass.getpass("Repite la contraseña: ") != password:
            print("✗ Las contraseñas no coinciden.", file=sys.stderr)
            return 1
        db.add(User(username=args.username, hashed_password=get_password_hash(password), role="admin",
                    person=Person(full_name=args.name)))
        db.commit()
    finally:
        db.close()
    print(f"✓ Administrador «{args.username}» creado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
