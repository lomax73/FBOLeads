import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import CampoSitoFormSet, LeadForm, SitoForm
from .models import CampoSito, Lead, Sito


class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = 'leads/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 50

    def get_queryset(self):
        qs = Lead.objects.select_related('assegnato_a', 'sorgente')
        stato = self.request.GET.get('stato', '')
        if stato in dict(Lead.Stato.choices):
            qs = qs.filter(stato=stato)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nome__icontains=q) | Q(email__icontains=q) |
                Q(telefono__icontains=q) | Q(azienda__icontains=q) |
                Q(sito__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stato_attivo'] = self.request.GET.get('stato', '')
        ctx['q'] = self.request.GET.get('q', '')
        ctx['stati'] = Lead.Stato.choices
        return ctx


class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    template_name = 'leads/lead_detail.html'
    context_object_name = 'lead'


class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Contatto creato.')
        return super().form_valid(form)


class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Contatto aggiornato.')
        return super().form_valid(form)


class LeadDeleteView(LoginRequiredMixin, DeleteView):
    model = Lead
    template_name = 'leads/lead_confirm_delete.html'
    success_url = reverse_lazy('lead-list')

    def form_valid(self, form):
        messages.success(self.request, 'Contatto eliminato.')
        return super().form_valid(form)


class SitoListView(LoginRequiredMixin, ListView):
    model = Sito
    template_name = 'leads/sito_list.html'
    context_object_name = 'siti'

    def get_queryset(self):
        return Sito.objects.prefetch_related('campi')


class SitoCreateView(LoginRequiredMixin, CreateView):
    model = Sito
    form_class = SitoForm
    template_name = 'leads/sito_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['campi_formset'] = CampoSitoFormSet(self.request.POST, instance=self.object)
        else:
            ctx['campi_formset'] = CampoSitoFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        self.object = form.save()
        formset = CampoSitoFormSet(self.request.POST, instance=self.object)
        if formset.is_valid():
            formset.save()
            messages.success(self.request, 'Sito creato.')
            return redirect('sito-list')
        return self.render_to_response(self.get_context_data(form=form))


class SitoUpdateView(LoginRequiredMixin, UpdateView):
    model = Sito
    form_class = SitoForm
    template_name = 'leads/sito_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['campi_formset'] = CampoSitoFormSet(self.request.POST, instance=self.object)
        else:
            ctx['campi_formset'] = CampoSitoFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        self.object = form.save()
        formset = CampoSitoFormSet(self.request.POST, instance=self.object)
        if formset.is_valid():
            formset.save()
            messages.success(self.request, 'Sito aggiornato.')
            return redirect('sito-list')
        return self.render_to_response(self.get_context_data(form=form))


class SitoDeleteView(LoginRequiredMixin, DeleteView):
    model = Sito
    template_name = 'leads/sito_confirm_delete.html'
    success_url = reverse_lazy('sito-list')

    def form_valid(self, form):
        messages.success(self.request, 'Sito eliminato.')
        return super().form_valid(form)


def _sito_per_token(provided):
    """Ritorna il Sito il cui ingest_token corrisponde a `provided`."""
    if not provided or not getattr(settings, 'MASTER_ENCRYPTION_KEY', ''):
        return None
    for sito in Sito.objects.filter(attivo=True):
        try:
            token = sito.ingest_token
        except Exception:
            continue
        if token and token == provided:
            return sito
    return None


@csrf_exempt
def lead_ingest(request):
    """Endpoint pubblico di raccolta contatti, usato dai form dei siti web.

    Attende un POST con header ``X-Ingest-Token``. Il token può essere:
    - il ``ingest_token`` di un Sito configurato (consigliato): in tal caso
      il contatto viene collegato a quel sito e i campi del form vengono
      mappati sui campi canonici seguendo il template (CampoSito);
    - il ``INGEST_TOKEN`` globale del .env (retrocompatibilità).

    Accetta JSON oppure form-encoded. I campi non riconosciuti e non
    mappati dal template finiscono in ``dati_extra`` per non perdere nulla.
    """
    if request.method != 'POST':
        return JsonResponse({'detail': 'Metodo non consentito.'}, status=405)

    provided = request.headers.get('X-Ingest-Token', '')
    sito = _sito_per_token(provided)

    if sito is None:
        global_token = getattr(settings, 'INGEST_TOKEN', '')
        if not global_token or provided != global_token:
            return JsonResponse({'detail': 'Non autorizzato.'}, status=403)

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except ValueError:
            return JsonResponse({'detail': 'JSON non valido.'}, status=400)
    else:
        data = request.POST.dict()

    known_direct = {'nome', 'email', 'telefono', 'azienda', 'sito', 'messaggio',
                    'consenso_dati', 'privacy', 'consenso'}

    # 1. Campi canonici inviati direttamente con il nome standard.
    valori = {}
    for key in ('nome', 'email', 'telefono', 'azienda', 'sito', 'messaggio'):
        if key in data:
            valori[key] = str(data[key] or '').strip()

    # Consenso: accetta vari nomi di campo e vari valori di verità.
    consenso_raw = None
    for key in ('consenso_dati', 'privacy', 'consenso'):
        if key in data:
            consenso_raw = data[key]
            break

    # 2. Template del sito: mappa i campi del form sui canonici.
    mapped_keys = set()
    if sito is not None:
        for campo in sito.campi.all():
            if campo.key not in data:
                continue
            value = data[campo.key]
            dest = campo.destinazione
            if dest == CampoSito.Destinazione.EXTRA:
                continue  # resta in dati_extra
            mapped_keys.add(campo.key)
            if dest == CampoSito.Destinazione.CONSENSO:
                if consenso_raw is None:
                    consenso_raw = value
            else:
                if not valori.get(dest):
                    valori[dest] = str(value or '').strip()

    nome = valori.get('nome', '')
    if not nome:
        return JsonResponse({'detail': 'Il campo nome è obbligatorio.'}, status=400)

    consenso = str(consenso_raw or '').strip().lower() in {
        '1', 'true', 'on', 'yes', 'si', 'sì', 'accepted', 'accettato', 'ok',
    }

    # 3. Tutto il resto finisce in dati_extra.
    extra_keys = [k for k in data if k not in known_direct and k not in mapped_keys]
    dati_extra = {k: data[k] for k in extra_keys}

    lead = Lead.objects.create(
        nome=nome,
        email=valori.get('email', ''),
        telefono=valori.get('telefono', ''),
        azienda=valori.get('azienda', ''),
        sito=valori.get('sito', '') or (sito.dominio if sito else ''),
        sorgente=sito,
        messaggio=valori.get('messaggio', ''),
        dati_extra=dati_extra,
        consenso_dati=consenso,
        consenso_dati_il=timezone.now() if consenso else None,
    )
    return JsonResponse(
        {'id': lead.id, 'nome': lead.nome, 'consenso_dati': lead.consenso_dati},
        status=201,
    )
