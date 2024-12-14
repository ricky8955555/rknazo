"""
Providing `SimpleCrypter` to encrypt or decrypt data.
"""

import random
from typing import Any


class SimpleCrypter:
    """
    A simple crypter.

    NOTE: NOT cryptographically secure! Use at your own risk!
    """

    _keys: list[int]
    _shifts: list[int]

    def __init__(self, password: Any, length: int = 4) -> None:
        """
        Initialize the crypter.

        The keys are stable when password is determined.

        Args:
            password (Any): The password used to derive keys.
            length (int, optional): The length of keys (value > 0). Defaults to 4.
        """

        if length <= 0:
            raise ValueError("'length' should be a positive value.")

        rand = random.Random(password)
        self._shifts = rand.sample(range(length), k=length)
        self._keys = rand.sample(range(0xFF), k=length)

    def _apply_to(self, data: bytes) -> bytes:
        """
        Apply (either encrypt or decrypt) keys to data.

        Args:
            data (bytes): The data to be applied with keys.

        Returns:
            bytes: The data applied with keys.
        """

        key_length = len(self._keys)

        if len(data) % key_length:
            raise ValueError(f"The length of 'data' should be multiples of {key_length}.")

        applied = bytearray()

        for _ in range(len(data) // key_length):
            cur = data[:key_length]
            data = data[key_length:]

            applied.extend(b ^ key for b, key in zip(cur, self._keys))

        return bytes(applied)

    def encrypt(self, data: bytes, padding: bool = True) -> bytes:
        """
        Encrypt data.

        Args:
            data (bytes): The data to be encrypted.
            padding (bool, optional): If it is set to True, data will be auto padded when the length don't meet the requirement. Defaults to True.

        Returns:
            bytes: The data encrypted with keys.
        """

        key_length = len(self._keys)
        pad = (key_length - (len(data) % key_length)) % key_length

        if pad and not padding:
            raise ValueError(
                f"The length of 'data' should be multiples of {key_length} "
                "when 'padding' is set to False."
            )

        data += b"\0" * pad
        encrypted = self._apply_to(data)

        shifted = b"".join(
            bytes(encrypted[i + shift] for shift in self._shifts)
            for i in range(0, len(encrypted), key_length)
        )

        return shifted

    def decrypt(self, data: bytes, keep_null: bool = False) -> bytes:
        """
        Decrypt data.

        Args:
            data (bytes): The data to be decrypted.
            keep_null (bool, optional): If it is set to True, null characters in the end will be kept. Defaults to False.

        Returns:
            bytes: The data decrypted with keys.
        """

        key_length = len(self._keys)

        if len(data) % key_length:
            raise ValueError(f"The length of 'data' should be multiples of {key_length}.")

        shifted = b"".join(
            bytes(byte for _, byte in sorted(zip(self._shifts, data[i : i + key_length])))
            for i in range(0, len(data), key_length)
        )

        decrypted = self._apply_to(shifted)

        if not keep_null:
            decrypted = decrypted.rstrip(b"\0")

        return decrypted
