# juridico-cli — Documento Mestre do Projeto

## Status
Canônico.

## Caminho canônico
`docs/architecture/juridico_cli_documento_mestre.md`

---

## 1. Finalidade
Este documento é a única referência principal do projeto `juridico-cli`.

Ele substitui documentos antigos, intermediários, experimentais, descritivos ou históricos como base de decisão arquitetural e operacional.

Se houver divergência entre este documento e qualquer documento anterior, este documento prevalece.

---

## 2. Objetivo do projeto
Consolidar o `juridico-cli` como um monorepo de processamento documental e jurídico com arquitetura **skill-centric**, runtime canônico, infraestrutura local mínima validada e evolução controlada.

O projeto possui:

### Base vigente
- processamento documental;
- execução por skills;
- runtime canônico;
- stack mínima oficial validada.

### Expansão futura compatível
- memória persistente;
- compressão e eficiência contextual;
- mecanismos recursivos de linguagem;
- especializações jurídicas adicionais.

---

## 3. Decisão arquitetural vigente
A arquitetura oficial do projeto é **modular por domínio funcional e centrada em skills**.

### Regras canônicas
- A unidade canônica do sistema é a **skill**.
- Não existe mais arquitetura oficial baseada em agentes separados de prompts e skills.
- O runtime canônico é `platform/skill-runtime/`.
- O ponto oficial de despacho é `platform/skill-runtime/skill_dispatcher.py`.
- A camada canônica de habilidades é `platform/skills/`.
- `agents/` na raiz e partes antigas de `pipelines/` são legado congelado e não fonte de verdade.

---

## 4. Estrutura lógica vigente
```text
juridico-cli/
├── apps/
├── platform/
│   ├── skill-runtime/
│   └── skills/
├── packages/
├── var/
├── infra/
├── docs/
├── scripts/
├── tests/
├── pyproject.toml
├── uv.lock
└── README.md
```

### Papel das camadas
- `apps/` → módulos funcionais por domínio.
- `platform/skills/` → bundles canônicos de skills.
- `platform/skill-runtime/` → execução, loading, roteamento e resolução.
- `packages/` → componentes compartilhados.
- `var/` → I/O, logs, artefatos e runtime.
- `infra/` → infraestrutura local mínima.
- `docs/` → documentação oficial e arquivo histórico.

---

## 5. Runtime canônico
O runtime oficial do projeto é `platform/skill-runtime/`.

### Componentes canônicos
- `skill_dispatcher.py` → despacho real de skills.
- `bundle_loader.py` → carregamento interno de bundles.
- `skill_registry.yaml` → registro canônico de skills.
- `llm_registry.yaml` → registro canônico de perfis de execução.

### Regras do runtime
- skill nova só roda se estiver registrada em `skill_registry.yaml`;
- profile de execução deve existir em `llm_registry.yaml`;
- criar a pasta da skill, por si só, não basta;
- não deve existir arquitetura paralela de execução.

---

## 6. Stack oficial vigente
### Execução e modelos
- **Gemini via API**
- **llama.cpp local em Docker Desktop**

### Infraestrutura local
- **Qdrant local**
- **Docker Desktop**

Essa é a base mínima oficial já validada do projeto.

---

## 7. Estado vigente do projeto
### Já consolidado
- arquitetura skill-centric definida;
- runtime renomeado e alinhado;
- `skill_dispatcher.py` como caminho real de despacho;
- `apps/data-processing` integrado ao runtime canônico;
- dependência operacional de `agents/*.md` removida dos bundles `extr-*`;
- infraestrutura mínima local criada em `infra/`;
- stack mínima oficial validada.

### Ainda pendente
- criação das três skills genéricas do pipeline documental:
  - `pdf-to-md`
  - `md-clean-markdown`
  - `md-frontmatter-yaml`
- registro dessas skills no runtime após criação;
- expansão futura dos módulos ainda não plenamente implantados.

---

## 8. Próxima frente operacional
A próxima frente ativa do projeto é a criação das três skills genéricas do pipeline documental:

1. `pdf-to-md`
2. `md-clean-markdown`
3. `md-frontmatter-yaml`

### Regras obrigatórias
- criar do zero;
- não usar `agents/`;
- `SKILL.md` é a instrução principal;
- estrutura mínima:
  - `assets/`
  - `references/`
  - `scripts/`
- conteúdo genérico e agnóstico de domínio;
- especialização jurídica futura deve nascer como skill separada.

---

## 9. Mem0, TurboQuant e RLM
Esses componentes não substituem a base vigente do projeto.

Se continuarem sendo requisitos estratégicos, devem ser incorporados futuramente como camadas compatíveis com a arquitetura atual.

### Diretriz
- **Mem0** → memória persistente/episódica.
- **TurboQuant** → compressão e eficiência contextual.
- **RLM** → inferência/execução recursiva para contexto extenso.

### Regra
A eventual adoção desses elementos deve ser compatível com:
- `platform/skill-runtime/`
- `skill_dispatcher.py`
- `skill_registry.yaml`
- `llm_registry.yaml`
- separação entre pipeline genérico e especialização jurídica.

---

## 10. Módulos previstos
### Operacional hoje
- `apps/data-processing/`

### Previstos, mas não tratados como plenamente implantados
- `apps/legal-research/`
- `apps/legal-core/`
- `apps/orchestrator-cli/`

Esses módulos não devem ser tratados como frente ativa imediata sem validação real correspondente.

---

## 11. Governança documental
Este documento deve ser a única referência principal do projeto.

### Deve permanecer ativo
- `docs/architecture/juridico_cli_documento_mestre.md`
- `docs/runbooks/runbook_operacional_minimo.md`.

### Deve sair da área ativa
- documentos descritivos antigos;
- arquiteturas intermediárias;
- diagnósticos antigos;
- mapas de migração;
- documentos experimentais;
- qualquer texto que concorra com este documento.

### Destino recomendado
Mover documentos antigos para:

```text
docs/archive/juridico-cli/
```

---

## 12. Regras de manutenção
- não reintroduzir arquitetura baseada em agentes separados;
- toda nova capacidade deve nascer como skill ou ser compatível com o runtime canônico;
- não misturar pipeline genérico com especialização jurídica sem decisão explícita;
- não tratar documento histórico como vigente;
- mudanças em runtime, docs e registries devem permanecer alinhadas;
- legado congelado não deve voltar a comandar o projeto.

---

## 13. Checklist de continuidade
- [ ] A arquitetura vigente é skill-centric.
- [ ] O runtime canônico é `platform/skill-runtime/`.
- [ ] O dispatcher canônico é `skill_dispatcher.py`.
- [ ] `platform/skills/` é a camada canônica de habilidades.
- [ ] `agents/` da raiz é legado congelado.
- [ ] A stack oficial é Gemini + llama.cpp + Qdrant + Docker.
- [ ] Mem0, TurboQuant e RLM são camadas futuras compatíveis, não substituição da base vigente.
- [ ] As próximas três skills documentais devem ser genéricas.
- [ ] Skill nova só roda depois de registro no `skill_registry.yaml`.
- [ ] Documentação antiga não deve mais competir com este documento.

---

## 14. Decisão final
O `juridico-cli` deve ser conduzido por um único documento mestre, com arquitetura skill-centric, runtime canônico em `platform/skill-runtime/`, stack oficial mínima já validada e expansão futura controlada para memória, compressão e inferência recursiva.

