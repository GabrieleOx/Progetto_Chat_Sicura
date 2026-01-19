from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def encrypt(text,cipher):
    cont_pad=0
    while len(text.encode())%16!=0:#In modalità CBC il messaggio deve avere un multiplo di 16 bytes
        text+="0"
        cont_pad+=1
    print(text)
    return cont_pad,cipher.encrypt(text.encode())



text="ciao sono un testo in chiaro!!!! Il mio sogno nella vita è sempre stato essere un testo in chiaro ed ora finalmente lo sono"

AES_key=get_random_bytes(16)

cipher=AES.new(AES_key,mode=AES.MODE_CBC)#La modalità cbc è una delle modalità con la quale AES divide il messaggio in singoli blocchi
my_iv=cipher.iv#In modalità CBC abbiamo bisogno di un Initialize Vector, cioè di un valore iniziale dal quale partire a decifrare.
#Se non volete dover gestire tutte queste cose potete usare come modalità AES.MODE_ECB

pad_count,cifrato= encrypt(text,cipher)
print(cifrato)

encrypted_data=open("generate_AES_keys/encrypted","wb")
encrypted_data.write(cifrato)
encrypted_data.close()

decipher=AES.new(AES_key,mode=AES.MODE_CBC,iv=my_iv)

with open("generate_AES_keys/encrypted","rb") as f:
    print("Decifro")
    print(decipher.decrypt(f.read()))
    #Il pad count serve per sapere quanti zeri togliere alla fine