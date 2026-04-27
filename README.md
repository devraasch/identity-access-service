# identity-access-service

Serviço de autenticação, autorização e auditoria para APIs internas (base incipiente).

## Variáveis de ambiente

A aplicação **não** embute URLs, segredos nem credenciais no código. Tudo o que for operacionalmente sensível tem de existir no ambiente ou no ficheiro `.env` (carregado por Pydantic Settings).

1. Copie `.env.example` para `.env`.
2. Garanta **pelo menos** `IAC_DATABASE_URL` e `IAC_JWT_SECRET` (e, com PostgreSQL do Compose, coerência entre `IAC_DB_*` e o URL, com `db` como host).
3. Ajuste outras chaves (nome da app, TTL de tokens, limites de listagem) conforme o descrito em `.env.example`.
4. Nunca comite o ficheiro `.env`.

O prefixo de ambiente do código é `IAC_`. O `docker-compose` injeta o ficheiro `.env` no serviço `app`; o serviço `db` continua a usar as variáveis `IAC_DB_*` para o PostgreSQL.

### Obrigatórias (sem predefinição no código)

| Variável | Descrição |
|----------|-----------|
| `IAC_DATABASE_URL` | URL de base de dados (SQLAlchemy / AnyUrl). |
| `IAC_JWT_SECRET` | Segredo da assinatura HS256; sem valor no código. |

### Opcionais (predefinições mínimas em `Settings`)

| Variável | Exemplo (predefinição) | Conteúdo |
|----------|------------------------|----------|
| `IAC_APP_NAME` | `identity-access-service` | Título lógico. |
| `IAC_DEBUG` | `false` | Depuração. |
| `IAC_JWT_ALGORITHM` | `HS256` | Algoritmo JWT. |
| `IAC_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Validade do access token. |
| `IAC_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Validade do refresh (persistido em `refresh_tokens`). |
| `IAC_MIN_PASSWORD_LENGTH` | `8` | Tamanho mínimo de senha (aplicado na camada de aplicação). |
| `IAC_MAX_NAME_LENGTH` | `255` | Tamanho máximo do nome. |
| `IAC_LIST_DEFAULT_LIMIT` / `IAC_LIST_MAX_LIMIT` / `IAC_LIST_MAX_SKIP` | `100` / `500` / `1000000` | Paginação de listas. |

## API de autenticação

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/auth/login` | Email e palavra-passe; devolve `access_token`, `refresh_token`, `expires_in`. |
| `POST` | `/auth/refresh` | Corpo `{ "refresh_token": "..." }`; novo access token. |
| `POST` | `/auth/logout` | Corpo com `refresh_token`; revoga a sessão de refresh. |
| `GET` | `/auth/me` | Cabeçalho `Authorization: Bearer <access_token>`; devolve o utilizador sem segredos. |

## Com Docker Compose e PostgreSQL local

- Em `IAC_DATABASE_URL`, use o host `db` se a API correr no contentor; no host, use `localhost` com a porta mapeada.
- As credenciais do URL devem coincidir com `IAC_DB_USER`, `IAC_DB_PASSWORD` e `IAC_DB_NAME` quando o mesmo PostgreSQL for levantado pelo `docker compose`.

## Execução com `uv`

```bash
cp .env.example .env
# edite .env
uv sync --all-groups
alembic upgrade head
uv run uvicorn identity_access_service.main:app --reload --host 0.0.0.0 --port 8000
```

## Com Docker

```bash
cp .env.example .env
# ajuste IAC_DATABASE_URL (ex.: postgresql+psycopg://... @db:5432/...), IAC_JWT_SECRET e IAC_DB_*
docker compose up --build
```

As migrações Alembic correm no arranque (ver `entrypoint.sh`).

## Testes

A definição de variáveis para testes e fixtures partilhadas estão em `tests/conftest.py` (não requerem o seu `.env`).

```bash
uv run pytest
```
