from cryptography.fernet import Fernet
from django import forms
from django.conf import settings
from django.db import models


def _fernet():
    return Fernet(settings.MASTER_ENCRYPTION_KEY)


class EncryptedCharField(models.BinaryField):
    """Campo cifrato a riposo con Fernet (AES-128-CBC + HMAC).

    Stesso meccanismo di FBOPortal/catalog/fields.py e
    FBOMailer/invii/fields.py, riusato qui per il token di ingest dei siti.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', True)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.CharField}
        defaults.update(kwargs)
        return super(models.BinaryField, self).formfield(**defaults)

    def get_prep_value(self, value):
        if value is None:
            return value
        return _fernet().encrypt(value.encode())

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return _fernet().decrypt(bytes(value)).decode()

    def to_python(self, value):
        if value is None or isinstance(value, str):
            return value
        return _fernet().decrypt(bytes(value)).decode()
