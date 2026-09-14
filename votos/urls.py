from django.urls import path

from . import views

app_name = "votos"

urlpatterns = [
    path("", views.identificar, name="identificar"),
    path("votar/", views.votar, name="votar"),
    path("obrigado/", views.obrigado, name="obrigado"),
    path("apuracao/", views.apuracao, name="apuracao"),
]
