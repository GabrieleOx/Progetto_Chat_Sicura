# Progetto_Chat_Sicura
Chat Sicura p2mp con architettura client-server e database MariaDB<br>

**Sicurezza:**<br>
Cifratura asimmetrica per lo scambio di chiavi simmetriche: RSA 3072 B<br>
Cifratura simmetrica con controllo di integrità: AES-GCM<br>

**Implementazione:**<br>
UI: Python Textual<br>
Chat: Le chat comprendono da un minimo di 2 ad un massimo di N interlocutori (che possono essere aggiunti anche a chat già avviata)<br>
Multi-Chat: Ogni chat creata dispone di un suo canale cifrato<br>
Notifiche: Alla creazione e all'arrivo di messaggi si viene notificati<br>
Colori: E' possibili scegliere un colore personalizzato da avere su tutte le chat alla registrazione<br>

**Creatori:**<br>
Gabriele Ossola, Federico Baldini, Matteo Grasselli Fontana<br>

**Divisione del lavoro:**<br>
Gabriele: principalmente gestione database e server<br>
Federico: principalmente UI e gestione chat<br>
Matteo: principalmente crittografia e scambio di chiavi<br>

**Futuri sviluppi:**<br>
- Supporto grafico per dispositivi mobili<br>