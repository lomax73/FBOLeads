from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import CampoSito, Lead, RispostaAutomatica, Sito


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


class RispostaAutomaticaForm(forms.ModelForm):
    smtp_password = forms.CharField(
        label='Password SMTP',
        widget=forms.PasswordInput(render_value=True), required=False,
        help_text="Lascia vuoto per non cambiarla (in modifica).",
    )

    class Meta:
        model = RispostaAutomatica
        fields = [
            'attivo', 'mittente_nome', 'mittente_email', 'oggetto', 'corpo_html',
            'logo', 'firma_html', 'smtp_host', 'smtp_port', 'smtp_user',
            'smtp_password', 'smtp_use_tls',
        ]
        widgets = {
            'corpo_html': forms.Textarea(attrs={'rows': 8}),
            'firma_html': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_smtp_password(self):
        password = self.cleaned_data.get('smtp_password')
        if not password and self.instance.pk:
            return self.instance.smtp_password
        return password
