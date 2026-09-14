from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import IdentificacaoForm, VotoForm
from .models import Eligivel, Votante, Voto

SESSION_KEY = "votante_id"


def identificar(request):
    """Tela 1: a pessoa informa o nome dela para ser identificada como votante."""
    # Se já existe uma sessão de votação em andamento, limpa (nova identificação).
    if request.method == "POST":
        form = IdentificacaoForm(request.POST)
        if form.is_valid():
            nome_digitado = form.cleaned_data["nome"].strip()
            votante = Votante.objects.filter(nome__iexact=nome_digitado).first()

            if votante is None:
                messages.error(
                    request,
                    "Nome não encontrado na lista de votantes habilitados. "
                    "Verifique se digitou seu nome completo corretamente.",
                )
            elif votante.ja_votou:
                messages.warning(
                    request, "Você já registrou seu voto anteriormente. Obrigado por participar!"
                )
                return redirect("votos:obrigado")
            else:
                request.session[SESSION_KEY] = votante.id
                votante.identificado_em = timezone.now()
                votante.save(update_fields=["identificado_em"])
                return redirect("votos:votar")
    else:
        form = IdentificacaoForm()

    return render(request, "votos/identificar.html", {"form": form})


def _get_votante_da_sessao(request):
    votante_id = request.session.get(SESSION_KEY)
    if not votante_id:
        return None
    return Votante.objects.filter(id=votante_id).first()


def votar(request):
    """Tela 2: a pessoa identificada escolhe em quem votar."""
    votante = _get_votante_da_sessao(request)
    if votante is None:
        messages.info(request, "Primeiro informe seu nome para votar.")
        return redirect("votos:identificar")

    if votante.ja_votou:
        return redirect("votos:obrigado")

    # Regra de negócio: excluir da lista os elegíveis do mesmo grupo de
    # impedimento do votante.
    candidatos = Eligivel.objects.exclude(
        grupo_impedimento=votante.grupo_impedimento
    ).order_by("nome")

    if request.method == "POST":
        form = VotoForm(request.POST, queryset=candidatos)
        if form.is_valid():
            eligivel = form.cleaned_data["eligivel"]
            try:
                with transaction.atomic():
                    # Trava a linha do votante para evitar votos em duplicidade
                    # em caso de duplo clique / requisições concorrentes.
                    votante_travado = Votante.objects.select_for_update().get(
                        id=votante.id
                    )
                    if votante_travado.ja_votou:
                        messages.warning(request, "Você já votou anteriormente.")
                        return redirect("votos:obrigado")

                    if eligivel.grupo_impedimento == votante_travado.grupo_impedimento:
                        messages.error(
                            request,
                            "Você não pode votar em uma pessoa do seu próprio "
                            "grupo de impedimento.",
                        )
                        return render(
                            request,
                            "votos/votar.html",
                            {"form": form, "votante": votante, "candidatos": candidatos},
                        )

                    Voto.objects.create(votante=votante_travado, eligivel=eligivel)
                    votante_travado.ja_votou = True
                    votante_travado.save(update_fields=["ja_votou"])
            except Exception:
                messages.error(
                    request,
                    "Não foi possível registrar seu voto. Tente novamente.",
                )
                return render(
                    request,
                    "votos/votar.html",
                    {"form": form, "votante": votante, "candidatos": candidatos},
                )

            del request.session[SESSION_KEY]
            return redirect("votos:obrigado")
    else:
        form = VotoForm(queryset=candidatos)

    return render(
        request,
        "votos/votar.html",
        {"form": form, "votante": votante, "candidatos": candidatos},
    )


def obrigado(request):
    """Tela 3: agradecimento."""
    return render(request, "votos/obrigado.html")


@staff_member_required
def apuracao(request):
    """Tela 4: apuração de votos - somente para administradores."""
    resultado = (
        Eligivel.objects.annotate(total_votos=Count("votos_recebidos"))
        .order_by("-total_votos", "nome")
    )
    total_votos = Voto.objects.count()
    total_votantes = Votante.objects.count()
    total_ja_votaram = Votante.objects.filter(ja_votou=True).count()
    percentual_participacao = (
        round((total_ja_votaram / total_votantes) * 100, 1) if total_votantes else 0
    )

    contexto = {
        "resultado": resultado,
        "total_votos": total_votos,
        "total_votantes": total_votantes,
        "total_ja_votaram": total_ja_votaram,
        "percentual_participacao": percentual_participacao,
    }
    return render(request, "votos/apuracao.html", contexto)
