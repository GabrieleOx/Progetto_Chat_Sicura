/* Utente db per il progetto: */
create user 'progetto_chat'@'localhost'
identified by 'password-server';

/* Privilegi per l'utente: */
grant insert, select, delete
on progetto_chat_sicura.*
to 'progetto_chat'@'localhost';