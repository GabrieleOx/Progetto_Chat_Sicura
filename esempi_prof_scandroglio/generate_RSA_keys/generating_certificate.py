from Crypto.PublicKey import RSA

#Genera una chiave RSA a 2048 bits
k=RSA.generate(2048)

# Possiamo esportare la chiave in formato .pem, formato usato solitamente per salvare le chiavi pubbliche delle certifiction authority fidate all'interno di un 
# computer

pk=k.public_key().export_key()
with open("generate_RSA_keys/public_key.pem","wb") as f:
    f.write(pk)

#Possiamo allo stesso modo salvare la chiave privata
pvt=k.export_key(passphrase="ciaoSonoUnaPassword")#La chiave privata ha senso cifrarla
with open("generate_RSA_keys/private_key.pem","wb") as f2:
    f2.write(pvt)

print(f"n={k.n}\nd={k.d}\ne={k.e}\n")