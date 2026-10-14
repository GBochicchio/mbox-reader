"""
Lettore semplice di file .mbox per Windows (funziona anche su macOS/Linux).

Requisiti: Python 3.8+ (tkinter è già incluso nell'installer di python.org).
Uso:
    python mbox_reader.py                -> chiede quale file aprire
    python mbox_reader.py posta.mbox     -> apre direttamente il file
"""

import sys
import os
import re
import html
import mailbox
import email
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def messaggio_completo(f):
    return email.message_from_binary_file(f, policy=policy.default)


def solo_intestazioni(f):
    """Legge solo le intestazioni, senza caricare corpo e allegati in memoria."""
    righe = []
    while True:
        riga = f.readline()
        righe.append(riga)
        if not riga.strip():
            break
    return BytesParser(policy=policy.default).parsebytes(b"".join(righe), headersonly=True)


def apri_mbox(percorso):
    """Apre il file .mbox e ne legge l'indice dei messaggi.

    Restituisce la casella, da tenere aperta per leggere i messaggi completi
    solo quando servono, e una lista di voci (chiave, data, mittente, oggetto).
    """
    box = mailbox.mbox(percorso, factory=messaggio_completo, create=False)
    voci = []
    try:
        for chiave in box.iterkeys():
            f = box.get_file(chiave)
            try:
                msg = solo_intestazioni(f)
            finally:
                f.close()
            voci.append((chiave, data_breve(msg),
                         intestazione(msg, "From"), intestazione(msg, "Subject")))
    except Exception:
        box.close()
        raise
    return box, voci


def intestazione(msg, nome):
    """Legge un'intestazione in modo sicuro (alcune email sono malformate)."""
    try:
        valore = msg.get(nome, "")
        return str(valore) if valore else ""
    except Exception:
        return "(non leggibile)"


def data_breve(msg):
    try:
        return parsedate_to_datetime(msg["Date"]).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return intestazione(msg, "Date")


def contenuto(parte):
    """Testo di una parte; se il charset dichiarato è errato o sconosciuto
    decodifica comunque, sostituendo i caratteri illeggibili."""
    try:
        return parte.get_content()
    except Exception:
        dati = parte.get_payload(decode=True) or b""
        try:
            return dati.decode(parte.get_content_charset() or "utf-8", errors="replace")
        except LookupError:
            return dati.decode("latin-1")


def html_a_testo(testo_html):
    """Conversione essenziale da HTML a testo leggibile."""
    t = re.sub(r"(?is)<(script|style|head)\b.*?</\1\s*>", "", testo_html)
    t = re.sub(r"(?i)<br\s*/?>", "\n", t)
    t = re.sub(r"(?i)</(p|div|tr|li|h[1-6]|table|blockquote)\s*>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t).replace("\xa0", " ")
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def corpo_testo(msg):
    """Estrae il testo del messaggio, preferendo la versione in testo semplice."""
    try:
        parte = msg.get_body(preferencelist=("plain", "html"))
        if parte is None:
            return "(nessun contenuto testuale)"
        testo = contenuto(parte)
        if parte.get_content_type() == "text/html":
            testo = "[convertito da HTML]\n\n" + html_a_testo(testo)
        return testo
    except Exception as e:
        return f"(impossibile leggere il contenuto: {e})"


def allegati(msg):
    nomi = []
    try:
        for parte in msg.iter_attachments():
            nomi.append(parte.get_filename() or "(senza nome)")
    except Exception:
        pass
    return nomi


def righe_intestazione(msg):
    """Coppie (etichetta, valore) delle intestazioni principali da mostrare."""
    coppie = [("Da", intestazione(msg, "From")), ("A", intestazione(msg, "To"))]
    cc = intestazione(msg, "Cc")
    if cc:
        coppie.append(("Cc", cc))
    coppie += [("Data", intestazione(msg, "Date")),
               ("Oggetto", intestazione(msg, "Subject"))]
    nomi_allegati = allegati(msg)
    if nomi_allegati:
        coppie.append(("Allegati", ", ".join(nomi_allegati)))
    return coppie


def testo_completo(msg):
    """Il messaggio come testo semplice: intestazioni + corpo."""
    righe = [f"{(etichetta + ':'):<8} {valore}" for etichetta, valore in righe_intestazione(msg)]
    righe.append("-" * 80)
    righe.append(corpo_testo(msg))
    return "\n".join(righe)


def pagina_html(msg):
    """Il messaggio come pagina HTML autonoma (apribile nel browser o stampabile in PDF)."""
    titolo = html.escape(intestazione(msg, "Subject") or "(senza oggetto)")
    tabella = "\n".join(
        f"<tr><th>{html.escape(etichetta)}</th><td>{html.escape(valore)}</td></tr>"
        for etichetta, valore in righe_intestazione(msg)
    )
    try:
        parte = msg.get_body(preferencelist=("html", "plain"))
        if parte is None:
            corpo = "<p><em>(nessun contenuto testuale)</em></p>"
        elif parte.get_content_type() == "text/html":
            corpo = contenuto(parte)
        else:
            corpo = f"<pre>{html.escape(contenuto(parte))}</pre>"
    except Exception as e:
        corpo = f"<p><em>(impossibile leggere il contenuto: {html.escape(str(e))})</em></p>"
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{titolo}</title>
<style>
body {{ font-family: "Segoe UI", sans-serif; margin: 20px; }}
table.intestazioni {{ border-collapse: collapse; margin-bottom: 12px; }}
table.intestazioni th {{ text-align: left; padding: 2px 12px 2px 0; vertical-align: top; }}
pre {{ white-space: pre-wrap; font-family: inherit; }}
</style></head><body>
<table class="intestazioni">
{tabella}
</table>
<hr>
{corpo}
</body></html>
"""


def nome_file_sicuro(testo, massimo=80):
    """Rende un oggetto email utilizzabile come nome di file su Windows."""
    pulito = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", testo)[:massimo].strip(" .")
    return pulito or "messaggio"


class LettoreMbox(tk.Tk):
    def __init__(self, percorso=None):
        super().__init__()
        self.title("Lettore MBOX")
        self.geometry("1000x650")
        self.box = None
        self.voci = []
        self.msg_corrente = None   # (chiave, messaggio)
        self._timer_cerca = None
        self.protocol("WM_DELETE_WINDOW", self.chiudi)

        # Barra superiore
        barra = ttk.Frame(self, padding=6)
        barra.pack(fill="x")
        ttk.Button(barra, text="Apri file .mbox…", command=self.apri).pack(side="left")
        self.pulsante_esporta = ttk.Button(barra, text="Esporta mail…",
                                           command=self.esporta, state="disabled")
        self.pulsante_esporta.pack(side="left", padx=(6, 0))
        ttk.Label(barra, text="Cerca:").pack(side="left", padx=(15, 4))
        self.cerca_var = tk.StringVar()
        self.cerca_var.trace_add("write", lambda *a: self.programma_ricerca())
        ttk.Entry(barra, textvariable=self.cerca_var, width=40).pack(side="left")
        self.stato = ttk.Label(barra, text="Nessun file aperto")
        self.stato.pack(side="right")

        # Pannello diviso: elenco sopra, contenuto sotto
        pannello = ttk.PanedWindow(self, orient="vertical")
        pannello.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        cornice_elenco = ttk.Frame(pannello)
        colonne = ("data", "mittente", "oggetto")
        self.elenco = ttk.Treeview(cornice_elenco, columns=colonne, show="headings",
                                   selectmode="browse")
        self.elenco.heading("data", text="Data")
        self.elenco.heading("mittente", text="Mittente")
        self.elenco.heading("oggetto", text="Oggetto")
        self.elenco.column("data", width=130, stretch=False)
        self.elenco.column("mittente", width=280)
        self.elenco.column("oggetto", width=550)
        scroll1 = ttk.Scrollbar(cornice_elenco, command=self.elenco.yview)
        self.elenco.configure(yscrollcommand=scroll1.set)
        self.elenco.pack(side="left", fill="both", expand=True)
        scroll1.pack(side="right", fill="y")
        self.elenco.bind("<<TreeviewSelect>>", self.mostra_messaggio)
        pannello.add(cornice_elenco, weight=1)

        cornice_testo = ttk.Frame(pannello)
        self.testo = tk.Text(cornice_testo, wrap="word", font=("Segoe UI", 10))
        scroll2 = ttk.Scrollbar(cornice_testo, command=self.testo.yview)
        self.testo.configure(yscrollcommand=scroll2.set, state="disabled")
        self.testo.pack(side="left", fill="both", expand=True)
        scroll2.pack(side="right", fill="y")
        pannello.add(cornice_testo, weight=2)

        if percorso:
            self.after(100, lambda: self.carica(percorso))

    def apri(self):
        percorso = filedialog.askopenfilename(
            title="Scegli un file .mbox",
            filetypes=[("File MBOX", "*.mbox *.mbx"), ("Tutti i file", "*.*")],
        )
        if percorso:
            self.carica(percorso)

    def chiudi_box(self):
        if self.box is not None:
            self.box.close()
            self.box = None

    def chiudi(self):
        self.chiudi_box()
        self.destroy()

    def carica(self, percorso):
        self.stato.config(text="Caricamento…")
        self.config(cursor="watch")
        self.update()
        self.chiudi_box()
        self.voci = []
        self.msg_corrente = None
        self.pulsante_esporta.configure(state="disabled")
        self.mostra_testo("")
        try:
            self.box, self.voci = apri_mbox(percorso)
            self.title(f"Lettore MBOX - {percorso}")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aprire il file:\n{e}")
            self.title("Lettore MBOX")
        finally:
            self.config(cursor="")
        self.aggiorna_elenco()

    def programma_ricerca(self):
        """Aggiorna l'elenco solo quando si smette di digitare (utile con molti messaggi)."""
        if self._timer_cerca is not None:
            self.after_cancel(self._timer_cerca)
        self._timer_cerca = self.after(250, self.aggiorna_elenco)

    def aggiorna_elenco(self):
        self._timer_cerca = None
        filtro = self.cerca_var.get().lower().strip()
        self.elenco.delete(*self.elenco.get_children())
        mostrati = 0
        for chiave, data, mittente, oggetto in self.voci:
            if filtro and filtro not in (mittente + " " + oggetto).lower():
                continue
            self.elenco.insert("", "end", iid=str(chiave), values=(data, mittente, oggetto))
            mostrati += 1
        if self.box is not None:
            self.stato.config(text=f"{mostrati} di {len(self.voci)} messaggi")
        else:
            self.stato.config(text="Nessun file aperto")

    def mostra_testo(self, testo):
        self.testo.configure(state="normal")
        self.testo.delete("1.0", "end")
        self.testo.insert("1.0", testo)
        self.testo.configure(state="disabled")

    def mostra_messaggio(self, _evento=None):
        selezione = self.elenco.selection()
        if not selezione or self.box is None:
            return
        chiave = int(selezione[0])
        try:
            msg = self.box[chiave]
        except Exception as e:
            self.msg_corrente = None
            self.pulsante_esporta.configure(state="disabled")
            self.mostra_testo(f"(impossibile leggere il messaggio: {e})")
            return
        self.msg_corrente = (chiave, msg)
        self.pulsante_esporta.configure(state="normal")
        self.mostra_testo(testo_completo(msg))

    def esporta(self):
        if self.msg_corrente is None:
            return
        chiave, msg = self.msg_corrente
        percorso = filedialog.asksaveasfilename(
            title="Esporta mail",
            initialfile=nome_file_sicuro(intestazione(msg, "Subject")),
            defaultextension=".eml",
            filetypes=[
                ("Email originale con allegati (*.eml)", "*.eml"),
                ("Pagina web (*.html)", "*.html"),
                ("Testo semplice (*.txt)", "*.txt"),
            ],
        )
        if not percorso:
            return
        estensione = os.path.splitext(percorso)[1].lower()
        try:
            if estensione in (".html", ".htm"):
                with open(percorso, "w", encoding="utf-8") as f:
                    f.write(pagina_html(msg))
            elif estensione == ".txt":
                with open(percorso, "w", encoding="utf-8") as f:
                    f.write(testo_completo(msg))
            else:
                # Byte originali dal file .mbox: nessuna riscrittura delle intestazioni
                with open(percorso, "wb") as f:
                    f.write(self.box.get_bytes(chiave))
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile esportare la mail:\n{e}")
            return
        self.stato.config(text=f"Esportata in {os.path.basename(percorso)}")


if __name__ == "__main__":
    file_iniziale = sys.argv[1] if len(sys.argv) > 1 else None
    LettoreMbox(file_iniziale).mainloop()
