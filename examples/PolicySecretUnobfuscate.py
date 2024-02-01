
#copied from https://raw.githubusercontent.com/xpn/sccmwtf/main/policysecretunobfuscate.py

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, ciphers
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def mscrypt_derive_key_sha1(secret:bytes):
    # Implementation of CryptDeriveKey(prov, CALG_3DES, hash, 0, &cryptKey);
    buf1 = bytearray([0x36] * 64)
    buf2 = bytearray([0x5C] * 64)

    digest = hashes.Hash(hashes.SHA1(), backend=default_backend())
    digest.update(secret)
    hash_ = digest.finalize()

    for i in range(len(hash_)):
        buf1[i] ^= hash_[i]
        buf2[i] ^= hash_[i]

    digest1 = hashes.Hash(hashes.SHA1(), backend=default_backend())
    digest1.update(buf1)
    hash1 = digest1.finalize()

    digest2 = hashes.Hash(hashes.SHA1(), backend=default_backend())
    digest2.update(buf2)
    hash2 = digest2.finalize()

    derived_key = hash1 + hash2[:4]
    return derived_key

def deobfuscate_policysecret(output:str or bytes):
    if isinstance(output, str):
        output = bytes.fromhex(output)
    
    data_length = int.from_bytes(output[52:56], 'little')
    buffer = output[64:64+data_length]

    key = mscrypt_derive_key_sha1(output[4:4+0x28])
    iv = bytes([0] * 8)
    cipher = Cipher(algorithms.TripleDES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(buffer) + decryptor.finalize()

    padder = padding.PKCS7(64).unpadder() # 64 is the block size in bits for DES3
    decrypted_data = padder.update(decrypted_data) + padder.finalize()
    return decrypted_data

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Deobfuscates the policy secret data')
    parser.add_argument('policydata', help='The output from the policy secret command')
    args = parser.parse_args()

    decrypted_data = deobfuscate_policysecret(args.policydata)
    try:
        decrypted_data = decrypted_data.decode('utf-16-le')
    except:
        decrypted_data = decrypted_data.hex()    
    print(decrypted_data)
    


if __name__ == '__main__':
    main()
