"""
Providing utilities to generate and decrypt flags with the full process implemented.
"""

import random
from typing import Any, Iterable, Sequence

from rknazo.anura.crypto import SimpleCrypter
from rknazo.anura.exc import ValidationFailed
from rknazo.anura.flag import Flag, ValidatableFlag
from rknazo.anura.uuid import translate_from_uuid_like, translate_into_uuid_like


def _derive_key(length: int, password: Any) -> bytes:
    """
    Unified function to derive a key with `password`.

    NOTE: NOT cryptographically secure! Use at your own risk!

    Args:
        length (int): The length of data.
        password (Any): The password to generate the key.

    Returns:
        bytes: A key.
    """

    rand = random.Random(password)
    key = bytes(rand.choices(range(0xFF), k=length * 2))
    return key


def _fix_data(data: Sequence[bytes], size: int) -> list[bytes]:
    """
    Fix a sequence of data into given size.

    Args:
        data (Sequence[bytes]): The sequence of data to fix.
        size (int): The size fixing to.

    Returns:
        list[bytes]: Fixed `data` in `size`.
    """

    blocks: list[bytes] = []

    for block in data:
        if len(block) > size:
            raise ValueError(f"Block {block!r} is too big to fix.")

        padding = (size - len(block) % size) % size
        block += b"\0" * padding
        blocks.append(block)

    return blocks


_make_crypt = SimpleCrypter
"""
Unified function to make an crypt.
"""


def checksum(data: bytes, length: int = 1) -> bytes:
    """
    Generate checksum for data.

    Args:
        data (bytes): The data to checksum.
        length (int, optional): The length of checksum. Defaults to 1.

    Returns:
        int: Checksum of `data`.
    """

    result = sum(data)
    mask: int = (0x100**length) - 1
    result &= mask
    result = result.to_bytes(length, "big")
    return result


def generate_flags(data: Sequence[bytes], password: Any) -> list[Flag]:
    """
    Generate flags with given arguments.

    Args:
        data (Sequence[bytes]): The data to be encrypted and written into the flag.
        password (Any): The password used to derive the key.

    Returns:
        list[Flag]: A list of flags generated with given arguments.
    """

    if any(b"\0" in block for block in data):
        raise ValueError("NUL character is not allowed to appear in data.")

    data = _fix_data(data, 4)
    merged = b"".join(data)

    password = _derive_key(len(data), password)
    crypt = _make_crypt(password, len(merged))

    encrypted = crypt.encrypt(merged)

    flags: list[Flag] = []

    for seq, part in enumerate(data):
        partial_encrypted = encrypted[:4]
        partial_password = password[:2]
        decrypted_data_checksum = checksum(part, 2)

        flags.append(
            Flag(
                encrypted_data=partial_encrypted,
                decrypted_data_checksum=decrypted_data_checksum,
                partial_password=partial_password,
                challenge_id=seq,
            )
        )

        encrypted = encrypted[4:]
        password = password[2:]

    return flags


def make_uuid_like_flag(flag: Flag) -> str:
    """
    Translate a flag into UUID-like form.

    Args:
        flag (Flag): The flag to translate.

    Returns:
        str: A UUID-like string translated from `flag`.
    """

    if not isinstance(flag, ValidatableFlag):
        flag = ValidatableFlag.from_general(flag)

    return translate_into_uuid_like(flag)


def generate_uuid_like_flags(data: Sequence[bytes], password: Any) -> list[str]:
    """
    Generate flags in UUID-like form with given arguments.

    Args:
        data (Sequence[bytes]): The data to be encrypted and written into the flag.
        password (Any): The password used to derive the key.

    Returns:
        list[str]: A list of flags in UUID-like form generated with given arguments.
    """

    flags = generate_flags(data, password)
    translated = list(map(make_uuid_like_flag, map(ValidatableFlag.from_general, flags)))
    return translated


def validate_uuid_like_flag(flag: str) -> ValidatableFlag:
    """
    Translate a UUID-like string into validatable flag.

    Args:
        flag (str): The flag in UUID-like form to translate.

    Returns:
        ValidatableFlag: A validatable flag translated from `flag`.
    """
    return translate_from_uuid_like(ValidatableFlag, flag)


def decrypt_flags(flags: Iterable[Flag]) -> list[bytes]:
    """
    Decrypt flags.

    Args:
        flags (Iterable[Flag]): The flags to be decrypted.

    Returns:
        list[bytes]: Data decrypted from `flags`.
    """

    flags = sorted(flags, key=lambda flag: flag.challenge_id)
    encrypted = b"".join(flag.encrypted_data for flag in flags)

    password = b"".join(flag.partial_password for flag in flags)
    crypt = _make_crypt(password, len(encrypted))

    decrypted = crypt.decrypt(encrypted)

    results: list[bytes] = []

    for flag in flags:
        block = decrypted[:4]

        if flag.decrypted_data_checksum != checksum(block, 2):
            raise ValidationFailed("Decrypted data checksum validation failed.")

        results.append(block.rstrip(b"\0"))

        decrypted = decrypted[4:]

    return results


def decrypt_uuid_like_flags(flags: Iterable[str]) -> list[bytes]:
    """
    Decrypt flags in UUID-like form.

    Args:
        flags (Iterable[str]): The flags in UUID-like form to be decrypted.

    Returns:
        list[bytes]: Data decrypted from `flags`.
    """

    translated = list(map(validate_uuid_like_flag, flags))
    decrypted = decrypt_flags(translated)
    return decrypted


def wrap_flag(flag: Flag) -> str:
    """
    Wrap flag in UUID-like form with "flag{}" wrapper.

    Args:
        flag (Flag): The flag to be wrapped.

    Returns:
        str: A flag in UUID-like form with "flag{}" wrapper wrapped from `flag`.
    """

    uuid_like = make_uuid_like_flag(flag)
    return f"flag{{{uuid_like}}}"


def unwrap_flag(flag: str) -> ValidatableFlag:
    """
    Unwrap flag in UUID-like form from "flag{}" wrapper.

    Args:
        flag (str): The flag to be unwrapped.

    Returns:
        ValidatableFlag: The validatable flag unwrapped from `flag`.
    """

    if not (flag.startswith("flag{") and flag.endswith("}")):
        raise ValueError("Flag should be wrapped with 'flag{}'")
    flag = flag[5:-1]  # remove the wrapper.
    return validate_uuid_like_flag(flag)
