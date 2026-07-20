"""
Resolução local e centralizada de $ref de JSON Schema.

Garante que schemas dos extratores (`extr-*`) e qualquer outro consumidor de
`packages/shared-schemas/` validem payloads sem nenhum acesso à rede, mesmo
quando o $ref é uma URI https://juridico-cli.local/... .
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import referencing
import referencing.exceptions
import referencing.jsonschema as ref_jsonschema


class SchemaReferenceError(ValueError):
    """Levantado quando um $ref não é resolvível a partir de arquivos locais."""


def build_local_registry(schemas_dir: Path) -> referencing.Registry:
    """
    Constrói um referencing.Registry pré-carregado com todo `*.schema.json`
    sob `schemas_dir`, registrado tanto pelo seu `$id` declarado (quando
    houver) quanto pela URI `file://` do próprio arquivo — isso cobre tanto
    schemas com `$id` (`https://juridico-cli.local/...`) quanto schemas
    montados em memória sem `$id` (ex.: fatias parciais de schema), cujo
    `$ref` relativo só pode ser resolvido contra um diretório local.

    Não configura `retrieve`: qualquer URI ausente do registry permanece
    não resolvível localmente, nunca é buscada pela rede.
    """
    schemas_dir = Path(schemas_dir)
    registry = referencing.Registry()
    if not schemas_dir.is_dir():
        return registry

    for schema_path in sorted(schemas_dir.rglob("*.schema.json")):
        try:
            content = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SchemaReferenceError(
                f"Falha ao ler schema compartilhado {schema_path}: {exc}"
            ) from exc

        resource = ref_jsonschema.DRAFT202012.create_resource(content)

        schema_id = content.get("$id")
        if schema_id:
            registry = registry.with_resource(schema_id, resource)

        registry = registry.with_resource(schema_path.resolve().as_uri(), resource)

    return registry


def _ensure_refs_resolvable(node: Any, resolver: "referencing.Resolver") -> None:
    """Percorre o schema e resolve cada $ref localmente, ou falha de forma controlada."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str):
            try:
                resolver.lookup(ref)
            except referencing.exceptions.Unresolvable as exc:
                raise SchemaReferenceError(
                    f"Referência de schema não resolvível localmente: {ref!r} ({exc})"
                ) from exc
        for value in node.values():
            _ensure_refs_resolvable(value, resolver)
    elif isinstance(node, list):
        for item in node:
            _ensure_refs_resolvable(item, resolver)


def load_validator(
    schema: dict,
    schema_path: Path,
    shared_schemas_dir: Path,
) -> jsonschema.protocols.Validator:
    """
    Constrói um validador Draft 2020-12 para `schema` cujos $ref são
    resolvidos exclusivamente a partir de arquivos locais: primeiro o
    diretório de `schema_path` (o próprio schema_ref da skill — aceita
    tanto o arquivo do schema quanto seu diretório diretamente, para
    chamadores que só têm o schema em memória), depois `shared_schemas_dir`
    (root canônico de schemas compartilhados).

    Levanta SchemaReferenceError se algum $ref do schema não for
    resolvível localmente. Nunca realiza acesso à rede.
    """
    schema_path = Path(schema_path)
    shared_schemas_dir = Path(shared_schemas_dir)
    schema_dir = schema_path if schema_path.is_dir() else schema_path.parent

    registry = build_local_registry(schema_dir)
    if schema_dir.resolve() != shared_schemas_dir.resolve():
        registry = registry.combine(build_local_registry(shared_schemas_dir))

    base_uri = schema.get("$id") or schema_dir.resolve().as_uri() + "/"

    # jsonschema deriva a URI-base de resolução do próprio $id do schema
    # (vazio se ausente). Schemas montados em memória sem $id (ex.: fatias
    # parciais) precisam de um $id sintético igual ao `base_uri` usado
    # acima para que o $ref relativo resolva contra o mesmo registry
    # durante a validação real, não só na checagem antecipada.
    effective_schema = schema if "$id" in schema else {**schema, "$id": base_uri}

    # O documento efetivamente validado é registrado sob seu próprio
    # base_uri, sobrepondo qualquer versão lida do disco em build_local_registry.
    # Sem isso, um $ref interno (`#/$defs/...`) só resolve por coincidência,
    # quando `schema_path` aponta para o diretório real do arquivo em disco
    # que contém um documento idêntico — se o chamador passar um
    # `schema_path` diferente (ex.: um diretório compartilhado qualquer),
    # o base_uri nunca é registrado e a referência interna fica órfã.
    registry = registry.with_resource(
        base_uri, ref_jsonschema.DRAFT202012.create_resource(effective_schema)
    )

    resolver = registry.resolver(base_uri=base_uri)
    _ensure_refs_resolvable(effective_schema, resolver)

    validator_class = jsonschema.validators.validator_for(effective_schema)
    validator_class.check_schema(effective_schema)
    return validator_class(effective_schema, registry=registry)
