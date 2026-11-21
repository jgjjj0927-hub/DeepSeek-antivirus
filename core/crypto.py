import os
from cryptography.fernet import Fernet
from core.config import APP_DIR

_fernet_instance = None


def _get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance
    key_file = APP_DIR / ".master.key"
    if key_file.exists():
        key = key_file.read_bytes()
    else:
        key = Fernet.generate_key()
        key_file.write_bytes(key)
        try:
            os.chmod(key_file, 0o600)
        except Exception:
            pass
    _fernet_instance = Fernet(key)
    return _fernet_instance


def encrypt_str(plain: str) -> str:
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_str(token: str) -> str:
    return _get_fernet().decrypt(token.encode()).decode()
