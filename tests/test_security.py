"""security.py 加密模块测试"""
import pytest
import os
import tempfile
from security import encrypt_cookie, decrypt_cookie


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        """测试加密后能正确解密"""
        original = "test_cookie_value_12345"
        encrypted = encrypt_cookie(original)
        decrypted = decrypt_cookie(encrypted)
        assert decrypted == original

    def test_encrypted_is_different(self):
        """确保加密后的值与原文不同"""
        original = "my_secret_cookie"
        encrypted = encrypt_cookie(original)
        assert encrypted != original

    def test_different_inputs_different_outputs(self):
        """不同输入应产生不同输出"""
        enc1 = encrypt_cookie("cookie1")
        enc2 = encrypt_cookie("cookie2")
        assert enc1 != enc2

    def test_decrypt_wrong_data_fails(self):
        """错误的密文应解密失败"""
        with pytest.raises(Exception):
            decrypt_cookie("invalid_encrypted_data")
