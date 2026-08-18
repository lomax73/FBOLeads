# Deploy di FBOLeads sul VPS

Stesso pattern delle altre app FBO (repo separato, utente di sistema
dedicato, venv proprio, Gunicorn su socket Unix, Nginx su IP nudo con
porta dedicata). FBOLeads usa la porta **8451** (8443 Portale, 8444
Collaudi, 8445 Preventivi, 8446 RackReport, 8447 NetVault, 8448 Squadfy).

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
# DJANGO_ALLOWED_HOSTS=94.177.161.127, MASTER_ENCRYPTION_KEY,
# INTERNAL_API_TOKEN, INGEST_TOKEN, PORTAL_PUBLIC_URL
sudo -u fboleads venv/bin/python manage.py migrate
sudo -u fboleads venv/bin/python manage.py collectstatic --noinput
sudo -u fboleads venv/bin/python manage.py createsuperuser

# Nginx deve poter attraversare /opt/fboleads per servire staticfiles/
chmod 751 /opt/fboleads

cp deploy/fboleads-web.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now fboleads-web.service

mkdir -p /etc/ssl/fboleads
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/ssl/fboleads/selfsigned.key \
    -out /etc/ssl/fboleads/selfsigned.crt \
    -subj "/CN=94.177.161.127"

cp deploy/nginx-fboleads-ip-provisional.conf /etc/nginx/sites-available/fboleads
ln -s /etc/nginx/sites-available/fboleads /etc/nginx/sites-enabled/fboleads
nginx -t && systemctl reload nginx
ufw allow 8451/tcp comment 'FBOLeads HTTPS'
```

## API interna di gestione utenti (per il Portale)

`/api/internal/` è esposto **solo in loopback** (location block dedicato in
Nginx). Configurare nel Portale (admin → AppLink FBOLeads):
- `internal_base_url = https://127.0.0.1:8451`
- `API token` = stesso valore di `INTERNAL_API_TOKEN` del `.env` di FBOLeads

## Endpoint di raccolta contatti (pubblico)

`POST https://94.177.161.127:8451/ingest/` con header
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
