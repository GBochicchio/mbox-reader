# Lettore MBOX

Un lettore di file `.mbox` semplice e leggero, con interfaccia grafica, scritto in Python.
Un solo file e nessuna dipendenza esterna: basta Python.

Utile per consultare archivi di posta esportati, per esempio da **Google Takeout (Gmail)**,
Thunderbird o Apple Mail, senza doverli importare in un client email.

## Funzionalità

- Elenco dei messaggi con data, mittente e oggetto
- Ricerca istantanea su mittente e oggetto
- Lettura del messaggio con intestazioni (Da, A, Cc, Data, Oggetto) ed elenco degli allegati
- Le email solo in HTML vengono convertite in testo leggibile
- Esportazione del messaggio selezionato in tre formati:
  - **`.eml`**: l'email originale, byte per byte, con tutti gli allegati (si apre con Outlook, Thunderbird, ecc.)
  - **`.html`**: pagina web apribile nel browser e stampabile in PDF
  - **`.txt`**: testo semplice
- Adatto anche a file di grandi dimensioni: all'apertura vengono lette solo le intestazioni,
  il contenuto di un messaggio viene caricato solo quando lo selezioni
- Tollerante verso email malformate o con codifiche dei caratteri errate

## Requisiti

- Python 3.8 o successivo
- `tkinter`, già incluso nell'installer di Python per Windows e macOS scaricato da
  [python.org](https://www.python.org/downloads/).
  Su Linux potrebbe servire installarlo a parte, per esempio su Debian/Ubuntu:

  ```bash
  sudo apt install python3-tk
  ```

## Utilizzo

Scarica `mbox_reader.py` (oppure clona il repository) e avvialo:

```bash
python mbox_reader.py
```

Si apre la finestra: premi **Apri file .mbox…** e scegli il file.

Puoi anche passare il file direttamente da riga di comando:

```bash
python mbox_reader.py "C:\percorso\della\posta.mbox"
```

Su Windows, se hai installato Python da python.org, puoi anche fare doppio clic su
`mbox_reader.py`. Rinominandolo in `mbox_reader.pyw` si evita la finestra nera del terminale.

### Esportare un messaggio

1. Seleziona un messaggio nell'elenco
2. Premi **Esporta mail…**
3. Scegli il formato dal menu "Salva come" (`.eml`, `.html` o `.txt`)

## Limiti

- È solo un **lettore**: il file `.mbox` non viene mai modificato.
- La ricerca considera mittente e oggetto, non il testo dei messaggi.
- Nell'anteprima l'HTML viene mostrato come testo semplice, senza immagini né formattazione:
  per vedere l'email com'era in origine esportala in `.html` o `.eml`.
- Gli allegati si salvano esportando il messaggio in `.eml` e aprendolo con un client di posta.

## Privacy

Il programma funziona interamente in locale: nessun dato viene inviato in rete.
Il file `.gitignore` del repository esclude i file `.mbox`, `.mbx` ed `.eml`, per evitare
di pubblicare per errore la propria posta.

## Licenza

Distribuito con licenza [MIT](LICENSE).
