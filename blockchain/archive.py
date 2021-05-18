# from cryptography.hazmat.primitives.asymmetric import rsa
# from cryptography.hazmat.primitives import serialization
# from cryptography.hazmat.backends import default_backend

#     self.key = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, key_size=512)

    # def get_private_key(self):
    #     private_key = self.key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption())
    #     private_key_str = private_key.decode('utf-8')
    #     return private_key_str

    # def get_public_key(self):
    #     public_key = key.public_key().public_bytes(serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH)
    #     public_key_str = public_key.decode('utf-8')
    #     return public_key_str


# https://medium.com/algorand/algorand-releases-first-open-source-code-of-verifiable-random-function-93c2960abd61