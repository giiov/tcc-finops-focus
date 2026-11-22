import json

import pandas as pd

from src.mapping.detector import detectar_formato
from src.mapping.aws_mapping import AWS_MAPPING
from src.mapping.gcp_mapping import GCP_MAPPING
from src.mapping.azure_mapping import AZURE_MAPPING
from src.mapping.oracle_mapping import ORACLE_MAPPING
from src.converters.aws_converter import converter_aws
from src.converters.gcp_converter import converter_gcp
from src.converters.azure_converter import converter_azure
from src.converters.oracle_converter import converter_oracle

#cada formato detectado aponta para o conversor dele
#guardar em dicionário evita um if/elif para cada provedor
CONVERSORES = {
    "aws": converter_aws,
    "gcp": converter_gcp,
    "azure": converter_azure,
    "oracle": converter_oracle,
}

#o mapeamento de cada formato: coluna do csv de origem -> coluna FOCUS
MAPEAMENTOS = {
    "aws": AWS_MAPPING,
    "gcp": GCP_MAPPING,
    "azure": AZURE_MAPPING,
    "oracle": ORACLE_MAPPING,
}


class FormatoNaoReconhecido(Exception):
    #erro só nosso: o csv é válido, mas não parece ser de nenhum dos 4 provedores
    pass


def converter_arquivo(caminho_arquivo):
    #detecta o provedor, chama o conversor certo e devolve (formato, tabela focus)
    #não sabe nada de web: recebe um caminho e devolve uma tabela, por isso dá para testar sem a api
    try:
        formato = detectar_formato(caminho_arquivo)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        #arquivo ilegível: deixa subir como está, quem chamou decide o que responder
        raise
    except ValueError as erro:
        #o detector levanta ValueError quando nenhuma coluna bate com nenhum provedor
        raise FormatoNaoReconhecido(str(erro)) from erro

    df_focus = CONVERSORES[formato](caminho_arquivo)
    return formato, df_focus


def colunas_identificadas(caminho_arquivo, formato):
    #quais colunas do csv original foram reconhecidas e para qual coluna FOCUS cada uma foi
    #lê só o cabeçalho (nrows=0), então é barato mesmo com o arquivo grande
    colunas_csv = pd.read_csv(caminho_arquivo, nrows=0).columns
    mapa = MAPEAMENTOS[formato]
    return [{"origem": c, "focus": mapa[c]} for c in colunas_csv if c in mapa]


def colunas_focus_preenchidas(df_focus):
    #das colunas FOCUS da saída, quais têm pelo menos um valor (cada provedor preenche colunas diferentes)
    return [c for c in df_focus.columns if df_focus[c].notna().any()]


def tabela_para_registros(df, limite):
    #transforma as primeiras linhas da tabela em uma lista de dicionários que vira json
    #passar por to_json resolve NaN, NaT e datas, que o json normal do python não aceita
    return json.loads(df.head(limite).to_json(orient="records", date_format="iso"))

def custo_por_servico(df_focus, limite=10):
    #agrupa as linhas pelo nome do seviço e soma o BilledCost de cada grup
    #usa a tabela inteira, não só as 100 linhas de amostra
    soma = df_focus.groupby("ServiceName")["BilledCost"].sum()

    #ordena do maior para o menor e fica só com os limites primeiros, para melhorar a elegibilidade
    soma = soma.sort_values(ascending=False).head(limite)

    #devolve no formato do char.js: rotulos (eixo x) e valores (altura das barras)
    return {
        "rotulos": list(soma.index),
        "valores": [round(float(v), 2) for v in soma.values],
    }

def _para_lista(soma):
    #funcao auxiliar (o "_" no começo avisa que é de uso interno deste arquivo)
    #transforma uma serie do pandas no formato rotulos/valores que a api devolve
    return {
        "rotulos": [str(r) for r in soma.index],
        "valores": [round(float(v), 2) for v in soma.values],
    }


def _tem_coluna(df_focus, coluna):
    #True só se a coluna existe E tem pelo menos um valor preenchido
    #cada provedor preenche colunas diferentes, então não podemos assumir que todas existem
    return coluna in df_focus.columns and df_focus[coluna].notna().any()


def _top_positivos(df_focus, coluna, limite=None):
    #soma o custo por "coluna", ignora grupos com total zero ou negativo e ordena do maior para o menor
    #rosca, treemap e ranking não conseguem desenhar valores negativos, por isso o filtro
    if not _tem_coluna(df_focus, coluna):
        return None
    soma = df_focus.groupby(coluna)["BilledCost"].sum()
    soma = soma[soma > 0].sort_values(ascending=False)
    if limite:
        soma = soma.head(limite)
    return soma if not soma.empty else None


def custo_por_dia(df_focus):
    #gráfico de área: evolução do custo no tempo
    if not _tem_coluna(df_focus, "ChargePeriodStart"):
        return None

    #transforma o texto em data; datas inválidas viram vazio em vez de dar erro
    #utc=True evita erro quando o arquivo mistura fusos horários
    datas = pd.to_datetime(df_focus["ChargePeriodStart"], errors="coerce", utc=True)

    #strftime corta a hora e deixa só "2026-10-01"; agrupa por esse dia e soma
    soma = df_focus.groupby(datas.dt.strftime("%Y-%m-%d"))["BilledCost"].sum()
    if soma.empty:
        return None

    #em gráfico de tempo a ordem é a informação: ordena pela data, e não pelo valor
    return _para_lista(soma.sort_index())


def custo_por_categoria(df_focus):
    #rosca: proporção do gasto por tipo de serviço (Compute, Storage, Networking...)
    soma = _top_positivos(df_focus, "ServiceCategory")
    return _para_lista(soma) if soma is not None else None


def custo_por_tipo_cobranca(df_focus):
    #barras horizontais: uso, impostos, créditos...
    #aqui NÃO filtramos os negativos, porque os créditos é que queremos enxergar
    if not _tem_coluna(df_focus, "ChargeCategory"):
        return None
    soma = df_focus.groupby("ChargeCategory")["BilledCost"].sum()
    return _para_lista(soma.sort_values(ascending=False))


def tipos_de_custo(df_focus):
    #funil: do preço de tabela até o que foi realmente pago
    #o dicionário liga o nome da coluna FOCUS ao nome que aparece na tela
    colunas = {
        "ListCost": "Preço de lista",
        "ContractedCost": "Contratado",
        "BilledCost": "Cobrado",
        "EffectiveCost": "Efetivo",
    }
    rotulos, valores = [], []
    for coluna, nome in colunas.items():
        if _tem_coluna(df_focus, coluna):
            rotulos.append(nome)
            valores.append(round(float(df_focus[coluna].sum()), 2))
    return {"rotulos": rotulos, "valores": valores} if rotulos else None


def custo_por_tipo_recurso(df_focus, limite=10):
    #treemap: quanto cada tipo de recurso custou (máquina virtual, disco, banco de dados...)
    #agrupamos por tipo, e não por conta, porque um arquivo costuma ter uma conta só
    #(um retângulo único, como no print) mas vários tipos de recurso
    soma = _top_positivos(df_focus, "ResourceType", limite)
    return _para_lista(soma) if soma is not None else None


def top_recursos(df_focus, limite=5):
    #barras radiais: os recursos mais caros (uma máquina, um banco...)
    soma = _top_positivos(df_focus, "ResourceId", limite)
    if soma is None:
        return None
    lista = _para_lista(soma)
    #o id completo é enorme (um caminho inteiro); ficamos só com o pedaço depois da última "/"
    lista["rotulos"] = [r.split("/")[-1] for r in lista["rotulos"]]
    return lista


def custo_por_tag(df_focus, limite=8):
    #radar: gasto por valor de uma tag (equipe, ambiente, projeto...)
    if "Tags" not in df_focus.columns:
        return None

    def ler(valor):
        #a coluna Tags pode vir como dicionário ou como texto json; aceitamos os dois
        if isinstance(valor, dict):
            return valor
        if isinstance(valor, str):
            try:
                lido = json.loads(valor)
                return lido if isinstance(lido, dict) else {}
            except ValueError:
                return {}
        return {}

    tags = df_focus["Tags"].apply(ler)

    #descobre qual chave de tag aparece em mais linhas e usa essa (ex.: "ambiente")
    chaves = pd.Series([k for t in tags for k in t]).value_counts()
    if chaves.empty:
        return None
    chave = chaves.index[0]

    #para cada linha pega o valor dessa tag (ou vazio, que o groupby ignora) e soma o custo
    valor_da_tag = tags.apply(lambda t: str(t[chave]) if chave in t else None)
    soma = df_focus.groupby(valor_da_tag)["BilledCost"].sum()
    soma = soma[soma > 0].sort_values(ascending=False).head(limite)
    if soma.empty:
        return None

    lista = _para_lista(soma)
    lista["chave"] = str(chave)
    return lista


def resumo_custos(df_focus):
    #cartões do topo: números grandes que resumem o arquivo
    custo = df_focus["BilledCost"]
    por_servico = custo.groupby(df_focus["ServiceName"]).sum()

    moeda = None
    if _tem_coluna(df_focus, "BillingCurrency"):
        moeda = str(df_focus["BillingCurrency"].dropna().iloc[0])

    return {
        "custo_total": round(float(custo.sum()), 2),
        "qtd_servicos": int(df_focus["ServiceName"].nunique()),
        "servico_mais_caro": str(por_servico.idxmax()) if not por_servico.empty else None,
        #créditos e descontos aparecem como valores negativos no BilledCost
        "creditos": round(float(custo[custo < 0].sum()), 2),
        "moeda": moeda,
    }