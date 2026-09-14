from django.contrib import admin

from .models import Eligivel, Votante, Voto


@admin.register(Eligivel)
class EligivelAdmin(admin.ModelAdmin):
    list_display = ("nome", "grupo_impedimento")
    search_fields = ("nome", "grupo_impedimento")
    list_filter = ("grupo_impedimento",)


@admin.register(Votante)
class VotanteAdmin(admin.ModelAdmin):
    list_display = ("nome", "grupo_impedimento", "ja_votou", "identificado_em")
    search_fields = ("nome", "grupo_impedimento")
    list_filter = ("ja_votou", "grupo_impedimento")


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = ("votante", "eligivel", "data_hora")
    search_fields = ("votante__nome", "eligivel__nome")
    date_hierarchy = "data_hora"
    autocomplete_fields = ("votante", "eligivel")

    def has_add_permission(self, request):
        # Votos só devem ser criados pelo fluxo público de votação.
        return False

    def has_change_permission(self, request, obj=None):
        return False
