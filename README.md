# FBOLeads

Raccolta e archiviazione dei contatti provenienti dai siti web della famiglia
FBO. Ogni contatto può essere assegnato a un utente e segue uno stato
(Nuovo → Contattato → Archiviato).

App satellite del Portale FBO (stesso pattern di FBOMailer/FBOPreventivi):
- espone l'API interna di gestione utenti (`accounts/`, su `/api/internal/users/`)
  per la gestione centralizzata dal Portale;
- espone un endpoint pubblico `POST /ingest/` a cui i form dei siti inviano
  i contatti, protetto da token (per-sito o globale).

## Siti e template dati

Ogni sito web può essere registrato come `Sito` (admin) con:
- `ingest_token` dedicato (cifrato a riposo con Fernet);
- un template di campi (`CampoSito`) che mappa i campi del form sui campi
  canonici del Lead: `nome`, `email`, `telefono`, `azienda`, `messaggio`,
  `consenso` (dati personali) oppure `extra` (solo archivio in `dati_extra`).

Così form diversi, con campi e quantità diverse, confluiscono tutti negli
stessi campi canonici senza perdere i campi specifici del sito.

## Sviluppo locale

```
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env   # valorizzare i token
venv/bin/python manage.py migrate
venv/bin/python manage.py createsuperuser
venv/bin/python manage.py runserver
```

## Endpoint di raccolta contatti (`POST /ingest/`)

Header richiesto: `X-Ingest-Token`. Il token può essere:
- l'`ingest_token` di un `Sito` configurato (consigliato): il contatto viene
  collegato al sito e i campi vengono mappati dal template;
- il `INGEST_TOKEN` globale del `.env` (retrocompatibilità).

Campi riconosciuti (JSON o form-encoded): `nome` (obbligatorio), `email`,
`telefono`, `azienda`, `sito`, `messaggio`. Qualsiasi altro campo non
mappato dal template viene salvato in `dati_extra` senza essere perso.

Consenso al trattamento dei dati personali (GDPR): accettato come
`consenso_dati`, `privacy` o `consenso`, con valori di verità come `on`,
`1`, `true`, `si`, `accepted`. Se presente, viene registrato anche il
momento esatto del consenso (`consenso_dati_il`).

Esempio (curl):

```
curl -X POST http://127.0.0.1:8000/ingest/ \
  -H "X-Ingest-Token: IL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Mario Rossi","email":"mario@example.com","sito":"www.calcioolgiate.it","messaggio":"Info"}'
```

## Registrazione nel Portale

La card nel launcher è registrata dalla migration
`FBOPortal/catalog/migrations/0011_seed_fboleads.py`.
