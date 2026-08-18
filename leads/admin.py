from django.contrib import admin
from django.contrib.auth.models import User

from .models import CampoSito, Lead, Sito


class CampoSitoInline(admin.TabularInline):
    model = CampoSito
    extra = 1


@admin.register(Sito)
class SitoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'dominio', 'attivo', 'campo_count')
    list_filter = ('attivo',)
    search_fields = ('nome', 'dominio')
    inlines = [CampoSitoInline]

    @admin.display(description='Campi')
    def campo_count(self, obj):
        return obj.campi.count()


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 'email', 'telefono', 'sito', 'sorgente', 'stato',
        'assegnato_a', 'consenso_dati', 'creato_il',
    )
    list_filter = ('stato', 'sito', 'sorgente', 'assegnato_a', 'consenso_dati')
    search_fields = ('nome', 'email', 'telefono', 'azienda', 'messaggio')
    autocomplete_fields = ['assegnato_a']
    list_select_related = ['assegnato_a', 'sorgente']
    date_hierarchy = 'creato_il'
