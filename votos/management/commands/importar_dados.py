# -*- coding: utf-8 -*-
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from votos.models import Eligivel, Votante
from votos.data.setores import SETORES_ORDENADOS

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
ELEGIVEIS_PATH = os.path.join(DATA_DIR, "elegiveis.txt")
VOTANTES_PATH = os.path.join(DATA_DIR, "raw_votantes.txt")


def parse_linha_votante(linha):
    """
    Recebe uma linha no formato "NOME DO SERVIDOR Setor do Grupo de Impedimento"
    e devolve (nome, setor), casando o setor pelo sufixo da linha usando a
    lista de setores conhecidos (testados do mais longo para o mais curto).
    """
    linha = linha.strip()
    if not linha:
        return None
    for setor in SETORES_ORDENADOS:
        sufixo = " " + setor
        if linha.endswith(sufixo):
            nome = linha[: -len(sufixo)].strip()
            if nome:
                return nome, setor
        # também aceita quando a linha é EXATAMENTE o setor (nome vazio) -> ignora
    return None


class Command(BaseCommand):
    help = "Importa as bases de elegíveis e votantes/grupo de impedimento para o banco."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpar",
            action="store_true",
            help="Apaga os dados de Eligivel e Votante antes de importar.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["limpar"]:
            self.stdout.write("Limpando dados existentes (Eligivel e Votante)...")
            Votante.objects.all().delete()
            Eligivel.objects.all().delete()

        # 1) Importar elegíveis (quem pode receber voto)
        criados_elegiveis = 0
        atualizados_elegiveis = 0
        with open(ELEGIVEIS_PATH, encoding="utf-8") as f:
            nomes_elegiveis = [linha.strip() for linha in f if linha.strip()]

        for nome in nomes_elegiveis:
            _, criado = Eligivel.objects.get_or_create(nome=nome)
            if criado:
                criados_elegiveis += 1
            else:
                atualizados_elegiveis += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Elegíveis: {criados_elegiveis} criados, {atualizados_elegiveis} já existiam."
            )
        )

        # 2) Importar votantes (quem pode votar) + setor / grupo de impedimento
        criados_votantes = 0
        atualizados_votantes = 0
        nao_reconhecidas = []

        with open(VOTANTES_PATH, encoding="utf-8") as f:
            linhas = [linha for linha in f if linha.strip()]

        for linha in linhas:
            resultado = parse_linha_votante(linha)
            if resultado is None:
                nao_reconhecidas.append(linha.strip())
                continue
            nome, setor = resultado
            votante, criado = Votante.objects.update_or_create(
                nome=nome, defaults={"grupo_impedimento": setor}
            )
            if criado:
                criados_votantes += 1
            else:
                atualizados_votantes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Votantes: {criados_votantes} criados, {atualizados_votantes} atualizados."
            )
        )
        if nao_reconhecidas:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(nao_reconhecidas)} linha(s) da base de votantes não "
                    f"foram reconhecidas (setor não identificado) e foram ignoradas:"
                )
            )
            for linha in nao_reconhecidas[:20]:
                self.stdout.write(f"  - {linha}")

        # 3) Cruzar elegíveis com votantes: se um elegível também é votante,
        #    herda o mesmo grupo de impedimento (regra de negócio).
        atualizados_cruzamento = 0
        votantes_por_nome = {v.nome: v.grupo_impedimento for v in Votante.objects.all()}
        for eligivel in Eligivel.objects.all():
            setor = votantes_por_nome.get(eligivel.nome)
            if setor and eligivel.grupo_impedimento != setor:
                eligivel.grupo_impedimento = setor
                eligivel.save(update_fields=["grupo_impedimento"])
                atualizados_cruzamento += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Cruzamento elegível <-> votante: {atualizados_cruzamento} "
                f"elegível(is) receberam grupo de impedimento."
            )
        )
        self.stdout.write(self.style.SUCCESS("Importação concluída com sucesso."))
