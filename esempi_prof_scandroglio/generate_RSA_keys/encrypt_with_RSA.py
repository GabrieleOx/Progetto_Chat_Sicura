from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long,long_to_bytes

pub_data=open("generate_RSA_keys/public_key.pem","rb").read()
pvt_data=open("generate_RSA_keys/private_key.pem","rb").read()

pub=RSA.import_key(pub_data)
pvt=RSA.import_key(pvt_data,passphrase="ciaoSonoUnaPassword")

t="ciao sono un messaggiooooo. Che bello essere un messaggio"
messaggio_trasformato_in_intero=bytes_to_long(t.encode())

#Come garantire segretezza
n=pub.n
e=pub.e

print(messaggio_trasformato_in_intero,end="\n_____________________________________________________\n")
encrypted=pow(messaggio_trasformato_in_intero,e,n)
print(encrypted,end="\n_____________________________________________________\n")

d=pvt.d
m=pow(encrypted,d,n)
print(m,end="\n_____________________________________________________\n")
print(long_to_bytes(m))

