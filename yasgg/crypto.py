# -*- coding: utf-8 -*-
from Crypto.Cipher import AES


class AESCipher:
    def __init__(self, key, iv):
        self.key = key
        self.iv = iv

    @classmethod
    def __bs(cls):
        return 16

    @classmethod
    def __pad(cls, string):
        return string + (cls.__bs() - len(string) % cls.__bs()) * chr(cls.__bs() - len(string) % cls.__bs())

    def encrypt(self, raw):
        raw = AESCipher.__pad(raw)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(raw)