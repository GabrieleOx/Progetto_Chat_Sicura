from Crypto.PublicKey import RSA


public_key_data=open("public_key.pem","rb").read()
pub=RSA.import_key(public_key_data)
print(f"e={pub.e} n={pub.n}")

private_key_data=open("private_key.pem","rb").read()
pvt=RSA.import_key(private_key_data,passphrase="ciaoSonoUnaPassword")
print(f"d={pvt.d}\nn={pvt.n}")