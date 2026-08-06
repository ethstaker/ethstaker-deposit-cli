import os
import json
import pytest
from jsonschema.exceptions import ValidationError as JSValidationError

from ethstaker_deposit.key_handling.keystore import (
    Keystore,
    ScryptKeystore,
    Pbkdf2Keystore,
)

test_vector_password = '𝔱𝔢𝔰𝔱𝔭𝔞𝔰𝔰𝔴𝔬𝔯𝔡🔑'
test_vector_secret = bytes.fromhex('000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f')
test_vector_folder = os.path.join(os.getcwd(), 'tests', 'test_key_handling', 'keystore_test_vectors')
_, _, test_vector_files = next(os.walk(test_vector_folder))  # type: ignore

test_vector_keystores = [Keystore.from_file(os.path.join(test_vector_folder, f)) for f in test_vector_files]


def test_json_serialization() -> None:
    for keystore, keystore_json_file in zip(test_vector_keystores, test_vector_files):
        keystore_json_path = os.path.join(test_vector_folder, keystore_json_file)
        with open(keystore_json_path, encoding='utf-8') as f:
            assert json.loads(keystore.as_json()) == json.load(f)


def test_encrypt_decrypt_test_vectors() -> None:
    for tv in test_vector_keystores:
        aes_iv = tv.crypto.cipher.params['iv']
        kdf_salt = tv.crypto.kdf.params['salt']
        keystore = Pbkdf2Keystore if 'pbkdf' in tv.crypto.kdf.function else ScryptKeystore
        generated_keystore = keystore.encrypt(
            secret=test_vector_secret,
            password=test_vector_password,
            aes_iv=aes_iv,
            kdf_salt=kdf_salt)
        assert generated_keystore.decrypt(test_vector_password) == test_vector_secret


def test_generated_keystores() -> None:
    for tv in test_vector_keystores:
        aes_iv = tv.crypto.cipher.params['iv']
        kdf_salt = tv.crypto.kdf.params['salt']
        keystore = Pbkdf2Keystore if 'pbkdf' in tv.crypto.kdf.function else ScryptKeystore
        generated_keystore = keystore.encrypt(
            secret=test_vector_secret,
            password=test_vector_password,
            aes_iv=aes_iv,
            kdf_salt=kdf_salt)
        assert generated_keystore.crypto == tv.crypto


def test_encrypt_decrypt_pbkdf2_random_iv() -> None:
    generated_keystore = Pbkdf2Keystore.encrypt(secret=test_vector_secret, password=test_vector_password)
    assert generated_keystore.decrypt(test_vector_password) == test_vector_secret


def test_encrypt_decrypt_scrypt_random_iv() -> None:
    generated_keystore = ScryptKeystore.encrypt(secret=test_vector_secret, password=test_vector_password)
    assert generated_keystore.decrypt(test_vector_password) == test_vector_secret


def test_encrypt_decrypt_incorrect_password() -> None:
    generated_keystore = ScryptKeystore.encrypt(secret=test_vector_secret, password=test_vector_password)
    incorrect_password = test_vector_password + 'incorrect'
    with pytest.raises(ValueError):
        generated_keystore.decrypt(incorrect_password)


@pytest.mark.parametrize(
    'kdf_salt, decryption_key',
    [
        (b'\x00' * 31, b'\x00' * 32),
        (b'\x00' * 33, b'\x00' * 32),
        (b'\x00' * 32, b'\x00' * 31),
        (b'\x00' * 32, b'\x00' * 33),
    ],
)
def test_decrypt_rejects_invalid_cached_key_lengths(kdf_salt: bytes, decryption_key: bytes) -> None:
    generated_keystore = ScryptKeystore.encrypt(secret=test_vector_secret, password=test_vector_password)
    with pytest.raises(ValueError):
        generated_keystore.decrypt(test_vector_password, kdf_salt, decryption_key)


@pytest.mark.parametrize(
    'password,processed_password',
    [
        ['\a', b''], ['\b', b''], ['\t', b''],
        ['a', b'a'], ['abc', b'abc'], ['a\bc', b'ac'],
    ]
)
def test_process_password(password: str, processed_password: bytes) -> None:
    assert Keystore._process_password(password) == processed_password


def test_keystore_validation_missing_element() -> None:
    incorrect_json = {
    "crypto": {
        "kdf": {
            "function": "scrypt",
            "params": {
                "dklen": 32,
                "n": 262144,
                "r": 8,
                "p": 1,
                "salt": "142040bf2b106694c7652e974f2063ef1a64daf6c0035a37f947dca9670d5025"
            },
            "message": ""
        },
        "checksum": {
            "function": "sha256",
            "params": {}
        },
        "cipher": {
            "function": "aes-128-ctr",
            "params": {
                "iv": "f8f201877665b43f21efd17e087c61eb"
            },
            "message": "3cb260b57ed4aee69762c3a20948f016ff8e357b8ea2ef75f603626d941ea18c"
        }
    },
    "description": "",
    "pubkey": "a610be328703ca298317a87b8a5b1de081ab5b32e63af79d16a9078510203c93b5d0c14e1232c361a35e4abb1977a643",
    "path": "m/12381/3600/0/0/0",
    "uuid": "1484b6f7-467d-4718-bd4b-32c9b45fde56",
    "version": 4
}
    with pytest.raises(JSValidationError):
        assert Keystore.from_json(incorrect_json) == 1


def test_keystore_validation_wrong_type() -> None:
    incorrect_json = {
    "crypto": {
        "kdf": {
            "function": "scrypt",
            "params": {
                "dklen": 32,
                "n": "262144",
                "r": 8,
                "p": 1,
                "salt": "142040bf2b106694c7652e974f2063ef1a64daf6c0035a37f947dca9670d5025"
            },
            "message": ""
        },
        "checksum": {
            "function": "sha256",
            "params": {},
            "message": "d81cfb226ef615e4b09f9e84ab2b9d4b5062d1092224651b2a4dd9f4613d3454"
        },
        "cipher": {
            "function": "aes-128-ctr",
            "params": {
                "iv": "f8f201877665b43f21efd17e087c61eb"
            },
            "message": "3cb260b57ed4aee69762c3a20948f016ff8e357b8ea2ef75f603626d941ea18c"
        }
    },
    "description": "",
    "pubkey": "a610be328703ca298317a87b8a5b1de081ab5b32e63af79d16a9078510203c93b5d0c14e1232c361a35e4abb1977a643",
    "path": "m/12381/3600/0/0/0",
    "uuid": "1484b6f7-467d-4718-bd4b-32c9b45fde56",
    "version": 4
}
    with pytest.raises(JSValidationError):
        assert Keystore.from_json(incorrect_json) == 1


def test_keystore_validation_too_many_args() -> None:
    incorrect_json = {
    "crypto": {
        "kdf": {
            "function": "scrypt",
            "params": {
                "dklen": 32,
                "n": 262144,
                "r": 8,
                "p": 1,
                "salt": "142040bf2b106694c7652e974f2063ef1a64daf6c0035a37f947dca9670d5025"
            },
            "message": ""
        },
        "checksum": {
            "function": "sha256",
            "params": {},
            "message": "d81cfb226ef615e4b09f9e84ab2b9d4b5062d1092224651b2a4dd9f4613d3454"
        },
        "cipher": {
            "function": "aes-128-ctr",
            "params": {
                "iv": "f8f201877665b43f21efd17e087c61eb",
                "p": 1
            },
            "message": "3cb260b57ed4aee69762c3a20948f016ff8e357b8ea2ef75f603626d941ea18c"
        }
    },
    "description": "",
    "pubkey": "a610be328703ca298317a87b8a5b1de081ab5b32e63af79d16a9078510203c93b5d0c14e1232c361a35e4abb1977a643",
    "path": "m/12381/3600/0/0/0",
    "uuid": "1484b6f7-467d-4718-bd4b-32c9b45fde56",
    "version": 4
}
    with pytest.raises(JSValidationError):
        assert Keystore.from_json(incorrect_json) == 1


def test_keystore_validation_wrong_version() -> None:
    incorrect_json = {
    "crypto": {
        "kdf": {
            "function": "scrypt",
            "params": {
                "dklen": 32,
                "n": "262144",
                "r": 8,
                "p": 1,
                "salt": "142040bf2b106694c7652e974f2063ef1a64daf6c0035a37f947dca9670d5025"
            },
            "message": ""
        },
        "checksum": {
            "function": "sha256",
            "params": {},
            "message": "d81cfb226ef615e4b09f9e84ab2b9d4b5062d1092224651b2a4dd9f4613d3454"
        },
        "cipher": {
            "function": "aes-128-ctr",
            "params": {
                "iv": "f8f201877665b43f21efd17e087c61eb"
            },
            "message": "3cb260b57ed4aee69762c3a20948f016ff8e357b8ea2ef75f603626d941ea18c"
        }
    },
    "description": "",
    "pubkey": "a610be328703ca298317a87b8a5b1de081ab5b32e63af79d16a9078510203c93b5d0c14e1232c361a35e4abb1977a643",
    "path": "m/12381/3600/0/0/0",
    "uuid": "1484b6f7-467d-4718-bd4b-32c9b45fde56",
    "version": 2
}
    with pytest.raises(JSValidationError):
        assert Keystore.from_json(incorrect_json) == 1
