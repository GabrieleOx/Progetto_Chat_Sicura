from tkinter import colorchooser
from tkinter import Tk

root = Tk()
root.withdraw()  # Nasconde la finestra principale

color = colorchooser.askcolor(title="Scegli un colore")[0]  # Prende solo RGB

if color:
    print(f"Colore scelto (RGB): {color}")  # Es. (255, 0, 0)
    print(f"Hex: #{color[0]:02x}{color[1]:02x}{color[2]:02x}".upper())
else:
    print("Nessun colore selezionato.")
