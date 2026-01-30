from tkinter import colorchooser
from tkinter import Tk

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

root = Tk()
root.withdraw()  

color = colorchooser.askcolor(title="Scegli un colore")[0] 

if color:
    print(f"Colore scelto (RGB): {color}")
    print(f"Hex: #{color[0]:02x}{color[1]:02x}{color[2]:02x}".upper())
else:
    print("Nessun colore selezionato.")

rgb=hex_to_rgb(f"{color[0]:02x}{color[1]:02x}{color[2]:02x}")
luminanza = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
if(luminanza>=100):
    print("il colore è chiaro")
else:
    print("il colore è scuro")