import json
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

# ==========================================
# 1. Modelos Base (Reutilizáveis)
# ==========================================


class Fonte(BaseModel):
    """Estrutura para ancorar a prova no documento."""

    arquivo: str = Field(..., description="Nome do arquivo Markdown de origem.")
    folha: str = Field(
        ...,
        description="Número da folha/página onde a informação foi encontrada (ex: 'Folha 125').",
    )


class Entidade(BaseModel):
    nome: str
    documento: Optional[str] = Field(None, description="CPF ou CNPJ se disponível.")
    papel: Optional[str] = Field(
        None, description="Ex: Sócio, Administrador, Comprador, Vendedor."
    )


# ==========================================
# 2. Contrato Social
# ==========================================


class Socio(Entidade):
    cotas: Optional[str] = Field(None, description="Quantidade ou valor das cotas.")
    participacao: Optional[str] = Field(None, description="Percentual de participação.")


class ContratoSocial(BaseModel):
    tipo_documento: str = Field(
        default="Contrato Social", description="Tipo de documento"
    )
    data_assinatura: Optional[str] = Field(
        None, description="Data de assinatura ou registro do contrato."
    )
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None
    socios: List[Socio] = Field(
        default_factory=list,
        description="Lista de sócios e suas participações no quadro societário.",
    )
    clausulas_gerencia: List[str] = Field(
        default_factory=list,
        description="Resumo das cláusulas que definem quem administra a sociedade.",
    )
    clausulas_impedimento: List[str] = Field(
        default_factory=list,
        description="Resumo de cláusulas que determinam impedimentos aos sócios/administradores.",
    )
    fonte: Optional[Fonte] = Field(
        None, description="Localização principal do documento."
    )


# ==========================================
# 3. Escritura de Imóveis (Geral)
# ==========================================


class TransacaoCompraVenda(BaseModel):
    registro: str = Field(..., description="Número do Registro (R-X).")
    data: str
    vendedores: List[str]
    compradores: List[str]
    valor: str = Field(..., description="Valor da transação.")
    folha_localizacao: Optional[str] = Field(
        None, description="Número da folha no doc onde está este registro."
    )


class HipotecaOuOnus(BaseModel):
    registro_ou_averbacao: str = Field(
        ..., description="Número do registro (R) ou averbação (Av)."
    )
    data: str
    credor: str
    devedor: str
    valor_divida: str
    prazo: Optional[str] = None
    taxas: Optional[str] = None
    quitada: bool = Field(False, description="Se há averbação de cancelamento/baixa.")
    detalhes_baixa: Optional[str] = Field(
        None, description="Se baixada, data e detalhes."
    )
    folha_localizacao: Optional[str] = Field(
        None, description="Número da folha onde consta este registro."
    )


class EscrituraImovel(BaseModel):
    tipo_documento: str = Field(
        default="Escritura de Imóvel/Matrícula", description="Tipo de documento"
    )
    matricula: Optional[str] = None
    cartorio: Optional[str] = None
    transacoes_venda: List[TransacaoCompraVenda] = Field(default_factory=list)
    hipotecas_onus: List[HipotecaOuOnus] = Field(default_factory=list)


# ==========================================
# 4. Escritura Hipotecária (Instrumento Específico)
# ==========================================


class EmprestimoDetalhes(BaseModel):
    valor_dinheiro: str
    taxas: str
    prazo: str


class Assinatura(BaseModel):
    nome: str
    tipo: str = Field(..., description="Pessoa Física ou Jurídica.")
    modalidade: str = Field(..., description="'Próprio' ou 'Por Procuração'.")
    detalhe_representacao: Optional[str] = Field(
        None, description="Se por procuração, quem representa."
    )


class EscrituraHipotecaria(BaseModel):
    tipo_documento: str = Field(
        default="Escritura Hipotecária", description="Tipo de documento"
    )
    data_escritura: str
    devedores: List[str]
    credores: List[str]
    emprestimo: EmprestimoDetalhes
    assinaturas: List[Assinatura]
    fonte: Optional[Fonte] = None


# ==========================================
# 5. Procuração
# ==========================================


class Procuracao(BaseModel):
    tipo_documento: str = Field(default="Procuração", description="Tipo de documento")
    data_outorga: str
    outorgantes: List[str]
    outorgados: List[str]
    transfere_poderes_pj: bool = Field(
        ..., description="Se transfere poderes para representação de Pessoa Jurídica."
    )
    transfere_poderes_pf: bool = Field(
        ..., description="Se transfere poderes para representação de Pessoa Física."
    )
    descricao_poderes: str = Field(
        ..., description="Resumo geral dos poderes transferidos."
    )
    poderes_especificos: List[str] = Field(
        default_factory=list,
        description="Lista de poderes específicos/especiais citados.",
    )
    fonte: Optional[Fonte] = None


# ==========================================
# 6. Processos (Autos Judiciais)
# ==========================================


class EventoProcessual(BaseModel):
    data: Optional[str] = None
    tipo: str = Field(..., description="Ex: Decisão, Petição, Audiência, Certidão.")
    descricao: str = Field(..., description="Resumo do fato ou decisão.")
    folha: str = Field(..., description="Número da folha nos autos.")


class ProcessoJudicial(BaseModel):
    tipo_documento: str = Field(
        default="Processo Judicial", description="Tipo de documento"
    )
    numero_processo: Optional[str] = None
    partes: List[str] = Field(default_factory=list)
    linha_tempo: List[EventoProcessual] = Field(
        default_factory=list, description="Lista cronológica de fatos, decisões e atos."
    )


# ==========================================
# Geração dos Arquivos
# ==========================================


def generate_schemas():
    output_dir = Path("schemas")
    output_dir.mkdir(parents=True, exist_ok=True)

    schemas_map = {
        "contrato_social.schema.json": ContratoSocial,
        "escritura_imovel.schema.json": EscrituraImovel,
        "escritura_hipotecaria.schema.json": EscrituraHipotecaria,
        "procuracao.schema.json": Procuracao,
        "processo.schema.json": ProcessoJudicial,
    }

    print(f"Gerando schemas em '{output_dir.absolute()}'...")

    for filename, model in schemas_map.items():
        file_path = output_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            # dump_json_schema gera o schema compatível com OpenAPI/JSON Schema
            json_schema = model.model_json_schema()
            json.dump(json_schema, f, indent=2, ensure_ascii=False)
        print(f"✅ {filename} gerado.")


if __name__ == "__main__":
    generate_schemas()
