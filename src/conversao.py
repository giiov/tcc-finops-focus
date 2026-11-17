import json

import pandas as pd

from src.mapping.detector import detectar_formato
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