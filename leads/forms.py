from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import CampoSito, Lead, Sito


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'nome', 'email', 'telefono', 'azienda', 'sito', 'sorgente',
            'messaggio', 'stato', 'assegnato_a', 'consenso_dati',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assegnato_a'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['assegnato_a'].required = False


class SitoForm(forms.ModelForm):
    class Meta:
        model = Sito
        fields = ['nome', 'dominio', 'ingest_token', 'attivo', 'note']


CampoSitoFormSet = inlineformset_factory(
    Sito, CampoSito,
    fields=('key', 'etichetta', 'tipo', 'destinazione', 'obbligatorio', 'ordine'),
    extra=1,
    can_delete=True,
)
