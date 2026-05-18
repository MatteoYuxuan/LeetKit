"""Cookie 加密模块"""
import os
import base64
from cryptography.fernet import Fernet

# 从环境变量获取密钥，如果没有则生成一个并保存到 .env 文件
def _get_or_create_key() -> bytes:
    key = os.environ.get('LEETKIT_SECRET_KEY')
    if key:
        return key.encode()

    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('LEETKIT_SECRET_KEY='):
                    return line.split('=', 1)[1].strip().encode()

    # 生成新密钥
    key = Fernet.generate_key()
    with open(env_path, 'a') as f:
        f.write(f'\nLEETKIT_SECRET_KEY={key.decode()}\n')
    return key

_fernet = None

def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_get_or_create_key())
    return _fernet

def encrypt_cookie(cookie: str) -> str:
    """加密 Cookie"""
    f = _get_fernet()
    return f.encrypt(cookie.encode()).decode()

def decrypt_cookie(encrypted: str) -> str:
    """解密 Cookie"""
    f = _get_fernet()
    return f.decrypt(encrypted.encode()).decode()
