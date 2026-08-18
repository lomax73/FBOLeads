from django.urls import path

from . import views

urlpatterns = [
    path('', views.LeadListView.as_view(), name='lead-list'),
    path('lead/nuovo/', views.LeadCreateView.as_view(), name='lead-create'),
    path('lead/<int:pk>/', views.LeadDetailView.as_view(), name='lead-detail'),
    path('lead/<int:pk>/modifica/', views.LeadUpdateView.as_view(), name='lead-update'),
    path('lead/<int:pk>/elimina/', views.LeadDeleteView.as_view(), name='lead-delete'),

    path('siti/', views.SitoListView.as_view(), name='sito-list'),
    path('siti/nuovo/', views.SitoCreateView.as_view(), name='sito-create'),
    path('siti/<int:pk>/modifica/', views.SitoUpdateView.as_view(), name='sito-update'),
    path('siti/<int:pk>/elimina/', views.SitoDeleteView.as_view(), name='sito-delete'),

    path('ingest/', views.lead_ingest, name='lead-ingest'),
]
