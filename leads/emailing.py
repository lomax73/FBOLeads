import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import escape

PLACEHOLDER_FIELDS = ('nome', 'email', 'telefono', 'azienda', 'messaggio', 'sito')


def _sostituisci_placeholder(testo, lead):
    """Sostituisce {{campo}} con i valori del lead. Semplice str.replace,
    non motore template Django, per non eseguire tag/codice da testo scritto
    dall'admin del sito. I valori del lead (inviati da chiunque via /ingest/)
    vengono HTML-escaped, dato che il corpo/oggetto viene poi renderizzato
    come HTML non ulteriormente sanificato."""
    if not testo:
        return ''
    for campo in PLACEHOLDER_FIELDS:
        valore = escape(str(getattr(lead, campo, '') or ''))
        testo = testo.replace('{{%s}}' % campo, valore)
    return testo


def invia_risposta_automatica(lead_id):
    """Invia la risposta automatica configurata per il sito del lead, se
    attiva. Pensata per girare in un thread separato dalla richiesta HTTP di
    /ingest/: non deve mai sollevare eccezioni verso il chiamante."""
    from .models import Lead  # import locale per evitare import circolari

    try:
        lead = Lead.objects.select_related('sorgente__risposta_automatica').get(pk=lead_id)
    except Lead.DoesNotExist:
        return

    sito = lead.sorgente
    config = getattr(sito, 'risposta_automatica', None) if sito else None
    if not config or not config.attivo or not lead.email:
        return

    try:
        oggetto = _sostituisci_placeholder(config.oggetto, lead)
        corpo = _sostituisci_placeholder(config.corpo_html, lead)
        firma = _sostituisci_placeholder(config.firma_html, lead)
        logo_url = f'{settings.PUBLIC_BASE_URL}{config.logo.url}' if config.logo else ''

        html = render_to_string('leads/email/risposta_automatica.html', {
            'corpo': corpo,
            'firma': firma,
            'logo_url': logo_url,
        })

        msg = MIMEMultipart('alternative')
        mittente = f'{config.mittente_nome} <{config.mittente_email}>' if config.mittente_nome else config.mittente_email
        msg['From'] = mittente
        msg['To'] = lead.email
        msg['Subject'] = oggetto
        msg.attach(MIMEText(html, 'html'))

        server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15)
        try:
            if config.smtp_use_tls:
                server.starttls()
            server.login(config.smtp_user or config.mittente_email, config.smtp_password or '')
            server.send_message(msg)
        finally:
            server.quit()
    except Exception as exc:
        Lead.objects.filter(pk=lead.pk).update(risposta_automatica_errore=str(exc)[:500])
        return

    Lead.objects.filter(pk=lead.pk).update(
        risposta_automatica_inviata_il=timezone.now(),
        risposta_automatica_errore='',
    )
