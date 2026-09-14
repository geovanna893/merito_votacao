# Sistema de Votação (Django)

Sistema web de votação interna com 4 telas:

1. **Identificação** (`/`) — a pessoa digita o nome dela.
2. **Votação** (`/votar/`) — a pessoa escolhe em quem votar, dentre os elegíveis.
3. **Agradecimento** (`/obrigado/`) — tela de confirmação.
4. **Apuração** (`/apuracao/`) — resultado dos votos, **acesso restrito** (login de administrador do Django).

## Regras de negócio implementadas

- Existem **duas bases de pessoas diferentes**:
  - **Elegíveis** (`Eligivel`): só podem **receber** votos.
  - **Votantes** (`Votante`): só podem **votar**, cada um com um `grupo_impedimento` (setor).
- **Cada votante só pode votar uma única vez** (`Votante.ja_votou`, reforçado com `select_for_update` para evitar duplo voto em requisições concorrentes/duplo clique).
- **Regra de impedimento**: um votante não pode votar em um elegível do mesmo grupo/setor de impedimento. Como algumas pessoas aparecem nas duas bases (são elegíveis e também votantes, com setor definido), o sistema cruza os dois cadastros na importação e propaga o `grupo_impedimento` para o registro de `Eligivel` correspondente. Na tela de votação, os elegíveis do mesmo grupo do votante logado **não aparecem na lista** — e mesmo que alguém tente burlar isso enviando o formulário manualmente, o backend valida de novo e bloqueia (ver `Voto.clean()` e a view `votar`).
- A tela de apuração usa `@staff_member_required`: só usuários com acesso de equipe (staff) autenticados no Django Admin conseguem ver o resultado.

## Sobre os dados importados

Os dois PDFs enviados (`Base_Votacao_Elegiveis.pdf` e `Base_Votacao_Votantes_grupodeimpedimento.pdf`) foram convertidos para texto e colocados em `votos/data/elegiveis.txt` e `votos/data/raw_votantes.txt`.

- Alguns nomes na extração do PDF de elegíveis vieram colados um no outro (perda de quebra de linha na extração). Eles foram revisados e separados manualmente (comparando com a segunda base) antes de gerar `elegiveis.txt`.
- Na base de votantes, o comando de importação (`votos/management/commands/importar_dados.py`) separa "nome" de "setor" usando uma lista de setores conhecidos (`votos/data/setores.py`), testados do mais específico para o mais genérico. Isso deixa a importação robusta mesmo se o texto vier com quebras de linha diferentes.
- **Recomendação**: antes de usar em produção, revise a lista final de votantes/elegíveis pelo Django Admin, pois a extração de PDF pode conter pequenas imprecisões (nomes homônimos, acentuação etc.).

## Instalação

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py importar_dados      # carrega as duas bases para o banco
python manage.py createsuperuser     # cria o usuário administrador (para acessar a apuração)
python manage.py runserver
```

Acesse:
- Votação: http://127.0.0.1:8000/
- Apuração (login de admin necessário): http://127.0.0.1:8000/apuracao/
- Django Admin (gerenciar bases): http://127.0.0.1:8000/admin/

### Comando de importação

```bash
python manage.py importar_dados            # importa/atualiza
python manage.py importar_dados --limpar   # apaga Eligivel/Votante antes de importar de novo
```

## Estrutura principal

```
votacao/                  # configurações do projeto Django
votos/
  models.py                # Eligivel, Votante, Voto
  views.py                 # identificar, votar, obrigado, apuracao
  forms.py                 # IdentificacaoForm, VotoForm
  admin.py                 # cadastro no Django Admin
  urls.py
  data/                    # bases de dados de origem + lista de setores
  management/commands/importar_dados.py
  templates/                # base.html + telas
static/css/style.css        # visual (azul escuro, verde militar, branco)
```

## Paleta visual

- Azul escuro: `#0B2545`
- Verde militar: `#4B5320`
- Branco / cinza claro de fundo: `#FFFFFF` / `#F4F6F5`

## Observações de segurança para produção

- Troque `SECRET_KEY` em `votacao/settings.py`.
- Defina `DEBUG = False` e ajuste `ALLOWED_HOSTS`.
- Troque o banco SQLite por Postgres/MySQL se o volume de acesso simultâneo for alto.
- Sirva os arquivos estáticos com `collectstatic` + servidor web (Nginx) em produção.
