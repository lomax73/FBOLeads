## 2026-08-19 — sessione redflag

### Segnalazioni FBOFlag
Nessuna nota presente per FBOLeads (app non ancora comparsa tra quelle con segnalazioni su feedback.fbosolution.it al momento della sessione).

### Verifica rapida del codice
- [Scartato] `fboleads/settings.py:20` — `DEBUG = os.environ.get('DJANGO_DEBUG', 'true').lower() == 'true'`: default pericoloso (`True`) se la variabile manca dal `.env`. Stesso pattern già segnalato su Mailer/FiberReport/AIGate. Qui però `deploy/README.md` esiste e ricorda esplicitamente `DJANGO_DEBUG=false` in produzione, quindi rischio pratico basso. Utente ha deciso di lasciare così.
- [Corretto] `accounts/views.py:14` (`_check_token`) e `leads/views.py:158` (`_sito_per_token`) e `leads/views.py:185` (`lead_ingest`, token globale) — confronto token con `==`/`!=`, non a tempo costante (rischio timing attack teorico su API interna utenti e su `/ingest/`). Sostituito con `secrets.compare_digest` in tutti e tre i punti. Commit `1956041`, deployato su VPS (git pull + collectstatic + restart `fboleads-web.service`, verificato `active`).
- [Scartato] `leads/views.py` `_sito_per_token` — itera e decripta (Fernet) il token di *ogni* `Sito` attivo ad ogni richiesta di ingest invece di una lookup diretta; con al massimo una decina di siti configurati (confermato dall'utente) l'overhead è trascurabile, non introdotta alcuna ottimizzazione.
- [Da valutare] `POST /ingest/` — endpoint pubblico senza rate limiting. Protetto solo dal token (per-sito o globale), ma il token è per natura esposto lato client (form HTML/JS del sito esterno): se trapela, nulla impedisce un flood di `Lead` fasulli con credenziali valide. Rimandato su richiesta dell'utente, nessuna implementazione per ora.

### Per chi riprende questo progetto
Resta aperto il rate limiting su `/ingest/` (vedi sopra) — da riprendere se il volume di lead falsi/spam diventa un problema reale. Nessuna nota FBOFlag pendente per questa app al momento della sessione.
