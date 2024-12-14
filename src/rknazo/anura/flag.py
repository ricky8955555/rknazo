"""
Providing definition of flags.
"""

import hashlib
from dataclasses import dataclass
from typing import Self

from rknazo.anura.exc import ValidationFailed
from rknazo.anura.uuid import UuidBlocks


@dataclass(frozen=True, kw_only=True)
class Flag:
    """
    Flag.
    """

    encrypted_data: bytes
    """
    Encrypted data. (4 bytes)
    """

    partial_password: bytes
    """
    A partial part of password. (2 bytes)
    """

    decrypted_data_checksum: bytes
    """
    Checksum of decrypted data. (2 bytes)

    NOTE: The checksum process for decrypted data needs to be implemented by user.
    """

    challenge_id: int
    """
    Challenge ID. (0x00 - 0xFF)
    """

    def __post_init__(self) -> None:
        if len(self.encrypted_data) != 4:
            raise ValueError("The length of 'encrypted_data' should be equal to 4.")

        if len(self.partial_password) != 2:
            raise ValueError("The length of 'partial_password' should be equal to 2.")

        if len(self.decrypted_data_checksum) != 2:
            raise ValueError("The length of 'decrypted_data_checksum' should be equal to 2.")

        if self.challenge_id < 0:
            raise ValueError("The value of 'challenge_id' should be greater than or equal to 0.")

        if self.challenge_id > 0xFF:
            raise ValueError("The value of 'challenge_id' is too big to fit in a 1-byte block.")


VALIDATABLE_FLAG_SIGNATURE = 0xFA
"""
Signature to identify it as a validatable flag.
"""


@dataclass(frozen=True, kw_only=True)
class ValidatableFlag(Flag):
    """
    Validatable flag.

    Using checksum, hash, signature to ensure the flag is correct.
    """

    expected_hash: bytes
    """
    Expected hash of the flag. (6 bytes)

    Algo: see `ValidatableFlag.hash`.
    """

    signature: int = VALIDATABLE_FLAG_SIGNATURE
    """
    Signature (should always be the value of `VALIDATABLE_FLAG_SIGNATURE` in this module) to identify it as a validatable flag.

    Remember to pass it as a parameter of initializer if you want to check it.
    """

    def __post_init__(self) -> None:
        super().__post_init__()

        if len(self.expected_hash) != 6:
            raise ValueError("The length of 'expected_hash' should be equal to 6.")

        if self.signature != VALIDATABLE_FLAG_SIGNATURE:
            raise ValidationFailed("Signature validation failed.")

        if self.hash(self) != self.expected_hash:
            raise ValidationFailed("Hash validation failed.")

    @staticmethod
    def _identity(flag: Flag) -> bytes:
        """
        Generate identity of the flag, used to generate hash.

        Args:
            flag (Flag): The flag to generate identity.

        Returns:
            bytes: An identity referring to `flag`.
        """

        return b"".join(
            [
                flag.encrypted_data,
                flag.partial_password,
                flag.challenge_id.to_bytes(),
            ]
        )

    @classmethod
    def hash(cls, flag: Flag) -> bytes:
        """
        Hash the flag with properties.

        Algo: SHA-1 (first 6 bytes).

        Args:
            flag (Flag): The flag to hash.

        Returns:
            bytes: The hash of the flag.
        """

        identity = cls._identity(flag)
        result = hashlib.sha1(identity)
        return result.digest()[:6]

    @classmethod
    def from_general(cls, flag: Flag) -> Self:
        """
        Make an flag validatable.

        Args:
            flag (Flag): The flag to convert.

        Returns:
            ValidatableFlag: A validatable flag converted from `flag`.
        """

        return cls(
            encrypted_data=flag.encrypted_data,
            partial_password=flag.partial_password,
            decrypted_data_checksum=flag.decrypted_data_checksum,
            challenge_id=flag.challenge_id,
            expected_hash=cls.hash(flag),
        )

    def __as_uuid__(self) -> UuidBlocks:
        """
        Translate the validatable flag into UUID blocks.

        Layout:
            - `encrypted_data[4]`
            - `partial_password[2]`
            - `decrypted_data_checksum[2]`
            - `signature[1] + challenge_id[1]`
            - `expected_hash[6]`

        Returns:
            UuidBlocks: UUID blocks translated from the flag.
        """

        return (
            self.encrypted_data,
            self.partial_password,
            self.decrypted_data_checksum,
            bytes([self.signature, self.challenge_id]),
            self.expected_hash,
        )

    @classmethod
    def __from_uuid__(cls, uuid: UuidBlocks) -> Self:
        """
        Translate UUID blocks into a validatable flag.

        Layout: see `ValidatableFlag.__as_uuid__`.

        Args:
            uuid (UuidBlocks): UUID blocks to translate into a validatable flag.

        Returns:
            ValidatableFlag: A validatable flag translated from UUID blocks.
        """

        (
            encrypted_data,
            partial_password,
            decrypted_data_checksum,
            (signature, challenge_id),
            expected_hash,
        ) = uuid

        return cls(
            encrypted_data=encrypted_data,
            decrypted_data_checksum=decrypted_data_checksum,
            partial_password=partial_password,
            challenge_id=challenge_id,
            expected_hash=expected_hash,
            signature=signature,
        )
