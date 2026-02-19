## 1) Subir Qdrant sem Docker (binário + systemd no WSL)

Execute no Ubuntu/WSL:

### 1.1. Dependências básicas
```bash
sudo apt-get update && sudo apt-get install -y curl tar
```

### 1.2. Baixar e instalar o Qdrant em ~/.local/qdrant/
```bash
mkdir -p ~/.local/qdrant && cd ~/.local/qdrant
```
• Descobrir a URL do “linux x86_64” do release mais recente no GitHub e baixar (ex.: `curl -L -o qdrant.tar.gz "<URL_DO_RELEASE>"`)

• `tar -xzf qdrant.tar.gz`

• Garanta que exista o binário qdrant dentro da pasta extraída e copie para:

 • `cp -f ./qdrant ~/.local/qdrant/qdrant`

 • `chmod +x ~/.local/qdrant/qdrant`

### 1.3. Config (persistência dentro do seu repo)

```bash
mkdir -p ~/devops/juridico-cli/artifacts/qdrant/storage
```

• Crie `~/devops/juridico-cli/artifacts/qdrant/config.yaml` com:

 • `storage_path: /home/kiko/devops/juridico-cli/artifacts/qdrant/storage`

 • `service: host 127.0.0.1, http_port 6333`

### 1.4. Service (systemd user)
```bash
mkdir -p ~/.config/systemd/user
```
• Crie `~/.config/systemd/user/qdrant.service apontando para ~/.local/qdrant/qdrant --config-path .../config.yaml`

• `systemctl --user daemon-reload`

• `systemctl --user enable --now qdrant`

• Teste: `curl -s http://127.0.0.1:6333/collections | head`

## 2) Indexar bj_juris_stj e bj_leis na coleção legal_library_chunks_v1

No seu venv/uv do juridico-cli, instale deps (uma vez):

```bash
uv add qdrant-client sentence-transformers pyyaml
```

Depois rode o script abaixo para:

• criar a coleção (se não existir)

• indexar todos os `*.rag.json de outputs/ingest/bj_juris_stj/02_json/rag/ e outputs/ingest/bj_leis/02_json/rag/`

• consultar com filtros (doc_kind e court obrigatório para jurisprudência)




---
1) Manter o Qdrant rodando

Você já está com ele rodando nesse terminal. Para indexar/consultar, mantenha assim (ou depois transforme em serviço).
Teste (em outro terminal):

1) Criar a coleção e alimentar (indexar) com seus RAGs
3.1 Criar coleção
3.2 Indexar jurisprudência STJ
3.3 Indexar leis
