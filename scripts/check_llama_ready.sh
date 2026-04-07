#!/usr/bin/env bash
# scripts/check_llama_ready.sh
# Pre-flight: verifica pré-requisitos para ativar o llama.cpp local via Docker Desktop.
# Detecta problemas antes de tentar subir o serviço.
#
# Uso:
#   bash scripts/check_llama_ready.sh                    # usa infra/env/.env por padrão
#   bash scripts/check_llama_ready.sh /outro/caminho/.env

set -euo pipefail

ENV_FILE="${1:-infra/env/.env}"
ERRORS=0

ok()   { printf "  %-55s [OK]\n" "$1"; }
fail() { printf "  %-55s [FALHOU] %s\n" "$1" "$2"; ERRORS=$((ERRORS + 1)); }
info() { echo "  → $1"; }

echo ""
echo "=== Pre-flight llama.cpp — juridico-cli ==="
echo "    Ambiente: Docker Desktop (Windows + WSL2)"
echo "    Env file: $ENV_FILE"
echo ""

# ---------------------------------------------------------------------------
# 1. .env existe e foi preenchido
# ---------------------------------------------------------------------------
if [ ! -f "$ENV_FILE" ]; then
    fail ".env existe ($ENV_FILE)" "não encontrado"
    info "Ação: cp infra/env/.env.example $ENV_FILE && edite o arquivo"
    echo ""
    echo "BLOQUEADO — .env não existe. Corrija e reexecute."
    exit 1
fi
ok ".env existe ($ENV_FILE)"

# lê valores do .env com grep puro — não executa o arquivo como script,
# evitando erros com valores que contêm <...> ou caracteres especiais
_env_get() {
    grep -E "^${1}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2-
}
LLAMA_MODELS_PATH="$(_env_get LLAMA_MODELS_PATH)"
LLAMA_MODEL_FILE="$(_env_get LLAMA_MODEL_FILE)"

# ---------------------------------------------------------------------------
# 2. LLAMA_MODELS_PATH definido e sem placeholder
# ---------------------------------------------------------------------------
if [ -z "${LLAMA_MODELS_PATH:-}" ]; then
    fail "LLAMA_MODELS_PATH definido" "variável vazia — edite $ENV_FILE"
elif echo "${LLAMA_MODELS_PATH}" | grep -q '<usuario>'; then
    fail "LLAMA_MODELS_PATH definido" "ainda contém placeholder '<usuario>' — edite $ENV_FILE"
else
    ok "LLAMA_MODELS_PATH = ${LLAMA_MODELS_PATH}"
fi

# ---------------------------------------------------------------------------
# 3. LLAMA_MODEL_FILE definido
# ---------------------------------------------------------------------------
if [ -z "${LLAMA_MODEL_FILE:-}" ]; then
    fail "LLAMA_MODEL_FILE definido" "variável vazia — edite $ENV_FILE"
else
    ok "LLAMA_MODEL_FILE = ${LLAMA_MODEL_FILE}"
fi

# ---------------------------------------------------------------------------
# 4. Arquivo .gguf existe (apenas para caminhos WSL2/Linux)
#    Caminhos Windows (C:\...) não são verificáveis diretamente do WSL2.
# ---------------------------------------------------------------------------
if [ -n "${LLAMA_MODELS_PATH:-}" ] && [ -n "${LLAMA_MODEL_FILE:-}" ]; then
    GGUF_PATH="${LLAMA_MODELS_PATH}/${LLAMA_MODEL_FILE}"

    if [ -f "$GGUF_PATH" ]; then
        GGUF_SIZE=$(du -sh "$GGUF_PATH" 2>/dev/null | cut -f1)
        ok "Arquivo .gguf existe: ${GGUF_PATH} (${GGUF_SIZE})"
    else
        fail "Arquivo .gguf existe (${GGUF_PATH})" "arquivo não encontrado"
        info "Ação: baixe o modelo de https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF"
        info "      coloque o arquivo .gguf em: ${LLAMA_MODELS_PATH}/"
    fi
fi

# ---------------------------------------------------------------------------
# 5. Docker Desktop disponível
# ---------------------------------------------------------------------------
if docker info > /dev/null 2>&1; then
    DOCKER_VER=$(docker info --format "{{.ServerVersion}}" 2>/dev/null)
    ok "Docker Desktop disponível (v${DOCKER_VER})"
else
    fail "Docker Desktop disponível" "Docker não está respondendo — abra o Docker Desktop"
fi

# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------
echo ""
echo "---"
if [ "$ERRORS" -eq 0 ]; then
    echo "PRONTO — todos os pré-requisitos satisfeitos."
    echo ""
    echo "Comando de subida:"
    echo "  docker compose --env-file ${ENV_FILE} \\"
    echo "    -f infra/docker/docker-compose.yml \\"
    echo "    --profile local-llm up -d"
    echo ""
    echo "Verificação após subida (aguardar ~30s para o modelo carregar):"
    echo "  curl http://localhost:8080/health"
    echo "  curl http://localhost:8080/v1/models"
else
    echo "BLOQUEADO — ${ERRORS} pré-requisito(s) não satisfeito(s)."
    echo "Corrija os itens marcados com [FALHOU] antes de tentar subir o serviço."
    exit 1
fi
