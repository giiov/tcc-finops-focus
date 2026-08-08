import os

from src.mapping.detector import detectar_formato
from src.converters.aws_converter import converter_aws
from src.converters.gcp_converter import converter_gcp

def main ():
    print("Iniciando conversão...")

    caminho_arquivo = "data/input/custos_gcp.csv"

    try:
        formato = detectar_formato(caminho_arquivo)

        if formato == "gcp":
            df_focus = converter_gcp(caminho_arquivo)
        elif formato == "aws":
            df_focus = converter_aws(caminho_arquivo)

        caminho_saida = "data/output/focus.csv"
        os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
        df_focus.to_csv(caminho_saida, index=False)

        print("Conversão concluída ({formato.upper()}) - salvo em {caminho_saida}")

    except Exception as erro:
        print("Erro durante a conversão:") 
        print(erro) 
        
if __name__ == "__main__": 
    main()