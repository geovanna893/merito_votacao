from django import forms

from .models import Eligivel


class IdentificacaoForm(forms.Form):
    nome = forms.CharField(
        label="Digite seu nome completo",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ex: MARIA DA SILVA SANTOS",
                "autofocus": True,
                "autocomplete": "off",
            }
        ),
    )


class VotoForm(forms.Form):
    eligivel = forms.ModelChoiceField(
        label="Selecione o candidato",
        queryset=Eligivel.objects.none(),
        widget=forms.RadioSelect,
        empty_label=None,
    )

    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if queryset is not None:
            self.fields["eligivel"].queryset = queryset
