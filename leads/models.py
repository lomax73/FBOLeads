from django.conf import settings
from django.db import models

from .fields import EncryptedCharField


class Sito(models.Model):
    """Sorgente da cui arrivano i contatti (un sito web della famiglia FBO).

    Ogni sito può avere un token di ingest dedicato e un template di campi
    (vedi CampoSito) per mappare i campi del proprio form sui campi
    canonici del Lead.
    """

    nome = models.CharField(max_length=120, unique=True)
    dominio = models.CharField(
        max_length=200, blank=True,
        help_text='Es. www.calcioolgiate.it — usato per valorizzare lead.sito.',
    )
    ingest_token = EncryptedCharField(
        blank=True, null=True,
        help_text='Token con cui il sito autentica le chiamate a /ingest/ '
                  '(header X-Ingest-Token). Cifrato a riposo.',
    )
    attivo = models.BooleanField(default=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'sito'
        verbose_name_plural = 'siti'

    def __str__(self):
        return self.nome


class CampoSito(models.Model):
    """Definizione di un campo del form di un sito (template dati).

    `key` è il nome esatto del campo inviato dal form. `destinazione` dice
    dove va a finire: su un campo canonico del Lead oppure in dati_extra.
    """

    class Tipo(models.TextChoices):
        TESTO = 'testo', 'Testo'
        TESTO_LUNGO = 'testo_lungo', 'Testo lungo'
        EMAIL = 'email', 'Email'
        TELEFONO = 'telefono', 'Telefono'
        DATA = 'data', 'Data'
        NUMERO = 'numero', 'Numero'
        CHECKBOX = 'checkbox', 'Checkbox'

    class Destinazione(models.TextChoices):
        NOME = 'nome', 'Nome'
        EMAIL = 'email', 'Email'
        TELEFONO = 'telefono', 'Telefono'
        AZIENDA = 'azienda', 'Azienda'
        MESSAGGIO = 'messaggio', 'Messaggio'
        CONSENSO = 'consenso', 'Consenso dati personali'
        EXTRA = 'extra', 'Extra (solo archivio)'

    sito = models.ForeignKey(Sito, on_delete=models.CASCADE, related_name='campi')
    key = models.CharField(max_length=120)
    etichetta = models.CharField(max_length=120, blank=True)
    tipo = models.CharField(
        max_length=20, choices=Tipo.choices, default=Tipo.TESTO,
    )
    destinazione = models.CharField(
        max_length=20, choices=Destinazione.choices, default=Destinazione.EXTRA,
    )
    obbligatorio = models.BooleanField(default=False)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sito', 'ordine', 'key']
        unique_together = [('sito', 'key')]
        verbose_name = 'campo del sito'
        verbose_name_plural = 'campi dei siti'

    def __str__(self):
        return f'{self.sito.nome} · {self.key}'


class Lead(models.Model):
    class Stato(models.TextChoices):
        NUOVO = 'nuovo', 'Nuovo'
        CONTATTATO = 'contattato', 'Contattato'
        ARCHIVIATO = 'archiviato', 'Archiviato'

    nome = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=40, blank=True)
    azienda = models.CharField(max_length=120, blank=True)
    sito = models.CharField(
        max_length=120, blank=True,
        help_text='Sito web da cui proviene il contatto.',
    )
    sorgente = models.ForeignKey(
        Sito, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lead',
        help_text='Sito configurato da cui è arrivato il contatto.',
    )
    messaggio = models.TextField(blank=True)
    dati_extra = models.JSONField(
        default=dict, blank=True,
        help_text='Eventuali campi aggiuntivi inviati dal form del sito.',
    )
    stato = models.CharField(
        max_length=20, choices=Stato.choices, default=Stato.NUOVO,
    )
    consenso_dati = models.BooleanField(
        'Consenso al trattamento dei dati personali',
        default=False,
        help_text='Autorizzazione acquisita dal form del sito (GDPR).',
    )
    consenso_dati_il = models.DateTimeField(
        'Data del consenso', null=True, blank=True,
        help_text='Compilata automaticamente alla ricezione del consenso.',
    )
    assegnato_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='lead_assegnati',
        verbose_name='Assegnato a',
    )
    creato_il = models.DateTimeField(auto_now_add=True)
    aggiornato_il = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creato_il']
        verbose_name = 'contatto'
        verbose_name_plural = 'contatti'

    def __str__(self):
        return self.nome
