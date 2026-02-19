Como executar o Qdrant

```bash
bash ~/devops/juridico-cli/scripts/install_qdrant_nodocker.sh
~/.local/qdrant/qdrant --version
```

## Validador único que varre todos os *.rag.json, aplica checks estruturais
(para bj_leis) também valida “corte do índice” por página usando o MD de origem.
Ele deve falhar (exit code 1) se encontrar qualquer problema — assim você usa como
“gate” antes do Qdrant.


## Como usar (gate antes do Qdrant)

1. Rodar em tudo:

```bash
uv run python scripts/validate_rag_all.py
echo $?
```

1. Rodar só bj_leis:

```bash
uv run python scripts/validate_rag_all.py --profile bj_leis
echo $?
```
O que esse teste garante (na prática)
• RAG tem chunks válidos e não vazios.
• Não há chunk_id duplicado.
• Todo chunk tem âncora (em anchors ou no text como [[Pág. N]]).
• bj_leis: não há duplicação “1.597 vs 1597” após normalização.
• bj_leis: se sources.md existir, ele detecta a página onde começa o heading ÍNDICE no MD e falha se algum ARTIGO tiver página >= essa página (vazamento real).

Se o script retornar exit code 0, você pode prosseguir para o upsert no Qdrant com segurança.

# 2) Dependências (uma vez):
```bash
cd ~/devops/juridico-cli
uv add qdrant-client sentence-transformers pyyaml
```

# 3) Criar coleção (uma vez):
```bash
uv run python scripts/index_library_qdrant.py init
```

# 4) Index incremental (rodar quando tiver novos/alterados):
```bash
uv run python scripts/index_library_qdrant.py index --dataset bj_juris_stj --rag-dir outputs/ingest/bj_juris_stj/02_json/rag
uv run python scripts/index_library_qdrant.py index --dataset bj_leis     --rag-dir outputs/ingest/bj_leis/02_json/rag
```

# 5) Consultar (exemplos):
```bash
uv run python scripts/index_library_qdrant.py query --doc-kind jurisprudencia --court STJ --query "ônus da prova em revisão contratual" --top-k 8
uv run python scripts/index_library_qdrant.py query --doc-kind lei --query "prazo prescricional cobrança" --top-k 8
```

# =========================================
# B) QDRANT EM BACKGROUND (AUTOMÁTICO) VIA systemd --user
# =========================================
# Qdrant só precisa estar rodando quando você vai INDEXAR ou CONSULTAR.
# Para ficar automático ao abrir o WSL, habilite como user service.

```bash
mkdir -p ~/devops/juridico-cli/artifacts/qdrant/storage
cat > ~/devops/juridico-cli/artifacts/qdrant/config.yaml <<'YAML'
storage:
  storage_path: /home/kiko/devops/juridico-cli/artifacts/qdrant/storage
service:
  host: 127.0.0.1
  http_port: 6333
YAML
```

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/qdrant.service <<'UNIT'
[Unit]
Description=Qdrant Vector Database (user)
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/qdrant/qdrant --config-path %h/devops/juridico-cli/artifacts/qdrant/config.yaml
Restart=on-failure
RestartSec=2
LimitNOFILE=1048576

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now qdrant

# Status e logs:
systemctl --user status qdrant --no-pager
journalctl --user -u qdrant -n 80 --no-pager

# Teste rápido:
```bash
curl -s http://127.0.0.1:6333/collections
```

PASSO 3 — Dar permissão de execução
```bash
chmod +x scripts/index_library_qdrant.py
```
PASSO 4 — Criar a coleção no Qdrant
```bash
uv run python scripts/index_library_qdrant.py init

```
PASSO 5 — Indexar (incremental)

Jurisprudência STJ:
```bash
uv run python scripts/index_library_qdrant.py index --dataset bj_juris_stj --rag-dir outputs/ingest/bj_juris_stj/02_json/rag
```

Leis:
```bash
uv run python scripts/index_library_qdrant.py index --dataset bj_leis --rag-dir outputs/ingest/bj_leis/02_json/rag
```

PASSO 6 — Consultar

Jurisprudência (com filtro obrigatório court=STJ):
```bash
uv run python scripts/index_library_qdrant.py query --doc-kind jurisprudencia --court STJ --query "ônus da prova em revisão contratual" --top-k 8
```

Leis (sem filtro de corte):
```bash
uv run python scripts/index_library_qdrant.py query --doc-kind lei --query "prazo prescricional cobrança" --top-k 8
```

PASSO 7 — Desligar quando terminar
```bash
systemctl --user stop qdrant
```

1) Iniciar o Qdrant sob demanda (agora deve subir)
```bash
systemctl --user start qdrant
```
```bash
systemctl --user status qdrant --no-pager -l
```
```bash
curl -s http://127.0.0.1:6333/collections
```

Se o curl retornar JSON, está pronto para indexar/consultar.
