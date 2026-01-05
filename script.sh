#!/usr/bin/env bash
# script.sh - Criar estrutura .agent e .claude no projeto juridico-cli

set -e

PROJECT_ROOT="$(pwd)"

echo "==============================================="
echo " Criando estrutura .agent e .claude"
echo " Diretório do projeto: $PROJECT_ROOT"
echo "==============================================="

# Diretórios a criar
DIRS=(
  ".agent"
  ".agent/system"
  ".agent/task"
  ".agent/SOPs"
  ".claude"
  ".claude/commands"
  ".claude/hooks"
)

for d in "${DIRS[@]}"; do
  if [ ! -d "$PROJECT_ROOT/$d" ]; then
    echo "📁 Criando diretório: $d"
    mkdir -p "$PROJECT_ROOT/$d"
  else
    echo "📂 Diretório já existe, mantendo: $d"
  fi
done

# Arquivos a criar (vazios se não existirem)
FILES=(
  ".agent/readme.md"
  ".agent/system/arquitetura_geral.md"
  ".agent/system/fluxo_pipeline_juridico.md"
  ".agent/system/convenções_arquivos.md"
  ".agent/system/mapeamento_outputs.md"
  ".agent/task/exemplo_acao_nulidade.md"
  ".agent/SOPs/sop_coletor_extracao_fatos.md"
  ".agent/SOPs/sop_firac_relatorio.md"
  ".agent/SOPs/sop_case_law_pesquisa_jurisprudencia.md"
  ".agent/SOPs/sop_petition_montagem_peticao.md"
  ".agent/SOPs/sop_compliance_auditoria_peticao.md"
  ".claude/CLAUDE.md"
  ".claude/commands/juridico-plan.md"
  ".claude/commands/juridico-update-doc.md"
  ".claude/commands/juridico-coletor.md"
  ".claude/commands/juridico-firac.md"
  ".claude/commands/juridico-case-law.md"
  ".claude/commands/juridico-petition.md"
  ".claude/commands/juridico-compliance.md"
  ".claude/settings.json"
)

for f in "${FILES[@]}"; do
  if [ ! -f "$PROJECT_ROOT/$f" ]; then
    echo "📝 Criando arquivo: $f"
    touch "$PROJECT_ROOT/$f"
  else
    echo "✅ Arquivo já existe, mantendo: $f"
  fi
done

echo "-----------------------------------------------"
echo " Estrutura .agent e .claude criada/atualizada."
echo " Agora você pode preencher os .md e settings.json."
echo "-----------------------------------------------"
