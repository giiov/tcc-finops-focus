import pandas as pd

from src.mapping.gcp_mapping import GCP_MAPPING
from src.mapping.aws_mapping import AWS_MAPPING
from src.mapping.azure_mapping import AZURE_MAPPING

#identifica se um arquivo csv é do formato gcp ou aws
#comparando as colunas com as chaves de cada mapping
def detectar_formato(caminho_arquivo):

    #lê apenas o cabeçalho do arquivo (nrows=0), sem carregar os dados, pra saber quais colunas existem
    colunas_arquivo = set(pd.read_csv(caminho_arquivo, nrows=0).columns)

    #transforma as chaves de cada mapping em conjunto, para a comparação
    colunas_gcp = set(GCP_MAPPING.keys())
    colunas_aws = set(AWS_MAPPING.keys())
    colunas_azure = set(AZURE_MAPPING.keys())

    #calcula quantas colunas do arquivo batem com cada formato
    intersecao_gcp = colunas_arquivo & colunas_gcp
    intersecao_aws = colunas_arquivo & colunas_aws
    intersecao_azure = colunas_arquivo & colunas_azure

    #decide pelo formato que teve mais colunas em comum
    maior_intersecao = max(len(intersecao_gcp), len(intersecao_aws), len(intersecao_azure))

    if maior_intersecao == 0:
        raise ValueError(f"Não foi possível identificar o formato do arquivo: {caminho_arquivo}")

    if maior_intersecao == len(intersecao_gcp):
        return "gcp"
    elif maior_intersecao == len(intersecao_aws):
        return "aws"
    elif maior_intersecao == len(intersecao_azure):
        return "azure"

    else:
        #nenhum dos dois bateu (ou bateram igual)
        raise ValueError (f"Não foi possível identificar o formato do arquivo: {caminho_arquivo}")
