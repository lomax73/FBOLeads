# Deploy di FBOLeads sul VPS

Stesso pattern delle altre app FBO (repo separato, utente di sistema
dedicato, venv proprio, Gunicorn su socket Unix, Nginx).

**Dominio**: `lead.fbosolution.it` (Let's Encrypt), stesso schema di
`mailer.fbosolution.it` / `aigate.fbosolution.it`. L'API interna di
gestione utenti resta esposta **solo su loopback** (`127.0.0.1:8451`)
per il Portale.

## Provisioning iniziale (una tantum)

```bash
# da root sul VPS (mkremote-vps)
adduser --system --group --home /opt/fboleads fboleads
mkdir -p /opt/fboleads/app
chown fboleads:fboleads /opt/fboleads/app

sudo -u fboleads git clone https://github.com/lomax73/FBOLeads.git /opt/fboleads/app
cd /opt/fboleads/app
sudo -u fboleads python3 -m venv venv
sudo -u fboleads venv/bin/pip install -r requirements.txt

cp .env.example .env
# valorizzare: DJANGO_SECRET_KEY, DJANGO_DEBUG=false,
# DJANGO_ALLOWED_HOSTS=lead.fbosolution.it,94.177.161.127,127.0.0.1,localhost
# MASTER_ENCRYPTION_KEY, INTERNAL_API_TOKEN, INGEST_TOKEN, PORTAL_PUBLIC_URL
sudo -u fboleads venv/bin/python manage.py migrate
sudo -u fboleads venv/bin/python manage.py collectstatic --noinput
sudo -u fboleads venv/bin/python manage.py createsuperuser

# Nginx deve poter attraversare /opt/fboleads per servire staticfiles/
chmod 751 /opt/fboleads

cp deploy/fboleads-web.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now fboleads-web.service

# Certificato Let's Encrypt (richiede che il DNS lead.fbosolution.it
# punti già al VPS):
cp deploy/nginx-fboleads-80.conf /etc/nginx/sites-available/fboleads-80
ln -s /etc/nginx/sites-available/fboleads-80 /etc/nginx/sites-enabled/fboleads-80
nginx -t && systemctl reload nginx
certbot certonly --webroot -w /var/www/html -d lead.fbosolution.it

# Server block del dominio + loopback interno:
cp deploy/nginx-fboleads.conf /etc/nginx/sites-available/fboleads
ln -s /etc/nginx/sites-available/fboleads /etc/nginx/sites-enabled/fboleads
nginx -t && systemctl reload nginx
```

## API interna di gestione utenti (per il Portale)

`/api/internal/` è esposto **solo in loopback** (`127.0.0.1:8451`).
Configurare nel Portale (admin → AppLink FBOLeads):
- `URL` = `https://lead.fbosolution.it/`
- `internal_base_url` = `https://127.0.0.1:8451`
- `Certificato TLS (pinning)` = `/etc/ssl/pinned-certs/lead.pem`
- `API token` = stesso valore di `INTERNAL_API_TOKEN` del `.env` di FBOLeads

## Endpoint di raccolta contatti (pubblico)

`POST https://lead.fbosolution.it/ingest/` con header
`X-Ingest-Token: <ingest_token del Sito o INGEST_TOKEN globale>`.

## Deploy di un aggiornamento

```bash
ssh mkremote-vps
cd /opt/fboleads/app
sudo -u fboleads git pull origin main
sudo -u fboleads venv/bin/pip install -r requirements.txt
sudo -u fboleads venv/bin/python manage.py migrate
sudo -u fboleads venv/bin/python manage.py collectstatic --noinput
systemctl restart fboleads-web.service
```
