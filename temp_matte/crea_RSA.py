from Crypto.PublicKey import RSA

chiave_client_corrente = RSA.generate(3072)
pb_corrente = chiave_client_corrente.public_key().export_key(format="DER")
with open("public_corrente.der", "wb") as file:
    file.write(pb_corrente)
pv_corrente = chiave_client_corrente.export_key(format="DER", pkcs=8, passphrase="ciaooo122")
with open("private_corrente.der", "wb") as file:
    file.write(pv_corrente)

chiave_client_altro = RSA.generate(3072)
pb_altro = chiave_client_altro.public_key().export_key(format="DER")
with open("public_altro.der", "wb") as file:
    file.write(pb_altro)
pv_altro = chiave_client_altro.export_key(format="DER", pkcs=8, passphrase="hallooo275")
with open("private_altro.der", "wb") as file:
    file.write(pv_altro)