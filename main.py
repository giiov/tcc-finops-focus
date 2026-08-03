from src.converters.gcp_converter import converter_gcp

def main ():
    print("Iniciando conversão...")

    try:
        converter_gcp()

        print("Conversão concluída")

    except Exception as erro:
        print("Erro durante a conversão:") 
        print(erro) 
        
if __name__ == "__main__": 
    main()