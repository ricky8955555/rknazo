"""
Providing protocol and functions to handle with uuid-like strings.
"""

import string
from typing import Protocol, Self, TypeVar, cast

UuidBlocks = tuple[bytes, bytes, bytes, bytes, bytes]


class UuidLikeTranslatable(Protocol):
    """
    The object can be translated into or from a UUID-like string.
    """

    def __as_uuid__(self) -> UuidBlocks:
        """
        Translate the object into UUID blocks.

        Returns:
            UuidBlocks: UUID blocks translated from the object.
        """

        ...

    @classmethod
    def __from_uuid__(cls, uuid: UuidBlocks) -> Self:
        """
        Translate UUID blocks into an object.

        Args:
            uuid (UuidBlocks): UUID blocks to translate into object.

        Returns:
            Self: An object translated from UUID blocks.
        """

        ...


_T = TypeVar("_T", bound=UuidLikeTranslatable)


def make_uuid_like(blocks: UuidBlocks) -> str:
    """
    Make a UUID-like string from given UUID blocks.

    Example: `a1b2c3d4-abcd-dcba-adbc-a1b2c3d4e5f6` (`4-2-2-2-6` bytes in hex form).

    Args:
        blocks (UuidBlocks): The blocks used to make the UUID-like string.

    Returns:
        str: A UUID-like string made from `blocks`.
    """

    if list(map(len, blocks)) != [4, 2, 2, 2, 6]:
        raise ValueError("Some blocks do not meet the length requirements.")

    result = "-".join(map(bytes.hex, blocks))
    return result


def parse_uuid_like(uuid: str) -> UuidBlocks:
    """
    Parse a UUID-like string into blocks.

    Example: `a1b2c3d4-abcd-dcba-adbc-a1b2c3d4e5f6` (`4-2-2-2-6` bytes in hex form).

    Args:
        uuid (str): The UUID-like string to parse.

    Returns:
        UuidBlocks: UUID blocks extracted from `uuid`.
    """

    blocks = uuid.split("-")

    if len(blocks) != 5:
        raise ValueError("Too many or too few blocks for a UUID-like string.")

    if list(map(len, blocks)) != [8, 4, 4, 4, 12]:
        raise ValueError("Some blocks do not meet the length requirements.")

    if any(c not in string.hexdigits for block in blocks for c in block):
        raise ValueError("Some characters are not valid for hex.")

    blocks = tuple(map(bytes.fromhex, blocks))
    return cast(UuidBlocks, blocks)


def translate_into_uuid_like(obj: UuidLikeTranslatable) -> str:
    """
    Translate a UUID-like translatable object into a UUID-like string.

    Args:
        obj (UuidLikeTranslatable): The object to translate.

    Returns:
        str: A UUID-like string translated from `obj`.
    """

    blocks = obj.__as_uuid__()
    result = make_uuid_like(blocks)
    return result


def translate_from_uuid_like(typ: type[_T], uuid: str) -> _T:
    """
    Translate a UUID-like string into a UUID-like translatable object.

    Args:
        typ (type[_T]): The type of object to translate into.
        uuid (str): The UUID-like string to translate.

    Returns:
        _T: An object of `typ` translated from `uuid`.
    """

    blocks = parse_uuid_like(uuid)
    obj = typ.__from_uuid__(blocks)
    return obj
