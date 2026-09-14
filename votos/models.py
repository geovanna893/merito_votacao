from django.db import models
from django.core.exceptions import ValidationError


class Eligivel(models.Model):
    """Pessoa que pode RECEBER votos (base 'Elegíveis')."""

    nome = models.CharField("Nome do servidor", max_length=255, unique=True)
    grupo_impedimento = models.CharField(
        "Setor / grupo de impedimento",
        max_length=255,
        blank=True,
        null=True,
        help_text=(
            "Preenchido automaticamente quando este elegível também consta "
            "na base de votantes, com o respectivo setor. Usado para aplicar "
            "a regra de impedimento na hora da votação."
        ),
    )

    class Meta:
        verbose_name = "Elegível (pode receber voto)"
        verbose_name_plural = "Elegíveis (podem receber voto)"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Votante(models.Model):
    """Pessoa que pode VOTAR (base 'Votantes / grupo de impedimento')."""

    nome = models.CharField("Nome do servidor", max_length=255, unique=True)
    grupo_impedimento = models.CharField(
        "Setor (grupo de impedimento)", max_length=255
    )
    ja_votou = models.BooleanField("Já votou", default=False)
    identificado_em = models.DateTimeField(
        "Identificado em", null=True, blank=True
    )

    class Meta:
        verbose_name = "Votante"
        verbose_name_plural = "Votantes"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.grupo_impedimento})"


class Voto(models.Model):
    """Registro de um voto. Um votante só pode ter um voto (OneToOne)."""

    votante = models.OneToOneField(
        Votante, on_delete=models.CASCADE, related_name="voto", verbose_name="Votante"
    )
    eligivel = models.ForeignKey(
        Eligivel,
        on_delete=models.PROTECT,
        related_name="votos_recebidos",
        verbose_name="Voto para",
    )
    data_hora = models.DateTimeField("Data/hora do voto", auto_now_add=True)

    class Meta:
        verbose_name = "Voto"
        verbose_name_plural = "Votos"
        ordering = ["-data_hora"]

    def __str__(self):
        return f"{self.votante.nome} -> {self.eligivel.nome}"

    def clean(self):
        # Regra de negócio: não é permitido votar em alguém do mesmo grupo
        # de impedimento do votante.
        if (
            self.votante_id
            and self.eligivel_id
            and self.votante.grupo_impedimento
            and self.eligivel.grupo_impedimento
            and self.votante.grupo_impedimento == self.eligivel.grupo_impedimento
        ):
            raise ValidationError(
                "Este votante não pode votar em um elegível do mesmo grupo de impedimento."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
