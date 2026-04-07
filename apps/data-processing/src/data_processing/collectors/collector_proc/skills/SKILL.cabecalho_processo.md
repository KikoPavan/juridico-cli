---
name: cabecalho_processo
agent: collector-proc
version: "0.2.0"
target_schema: "schemas/cabecalho_processo.schema.json"
document_types:
  - cabecalho_processo
key_fields:
  - process_number
  - court
  - comarca
  - vara
  - classe
  - assunto
  - distribution_date
  - parties
  - representations
  - anchors
validation_rules:
  - literalidade
  - ancoragem_forte
  - nao_inferir_papeis
  - nao_inventar_numero_processo
---

# SKILL — cabecalho_processo (capa/cabeçalho)

## Finalidade
Extrair dados típicos de capa/cabeçalho do processo (classe, assunto, foro/vara/comarca, distribuição, partes e representantes) **somente quando explicitamente presentes**.

## Regras específicas (além do CORE)

### 1) Identificação (prioridade máxima)
- Capture `process_number` somente se estiver escrito (com âncora).
- Capture `court`, `comarca`, `vara`, `classe`, `assunto`, `distribution_date` quando existirem, cada qual com âncora própria.
- Não deduzir tribunal/vara/comarca pelo contexto; se não estiver, omita.

### 2) Partes (conforme aparecer no cabeçalho)
- Liste `parties` conforme o cabeçalho apresentar.
- Para `role`, só classifique como “autor/réu/etc.” se o texto indicar explicitamente.
- Se o rótulo for diferente (ex.: “Requerente”, “Agravado”), use:
  - `role = outro`
  - `role_raw` = rótulo literal
- Se houver qualificação (CPF/CNPJ, RG, endereço etc.), mantenha literal e ancore.

### 3) Representantes/advogados (quando constar)
- Registre `representations` apenas quando o cabeçalho trouxer advogados/representantes.
- Não “assumir” vínculo de advogado com parte se não estiver explícito.
- OAB deve ser literal; se não constar, omitir.

### 4) Âncoras (exigência reforçada)
- Cabeçalho/capa é fonte primária de identificação: exija âncora em:
  - número do processo
  - classe/assunto
  - partes
- Evite uma única âncora “genérica” para vários campos; prefira uma âncora por campo.

### 5) Não reescrever
- Preserve grafia e termos do documento (ex.: nomes completos, abreviações).
- Não normalizar criativamente (ex.: não transformar “Vara Cível” em enum inexistente).
