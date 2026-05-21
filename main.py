from src.converters.aws_converter import converter_aws

def main ():
    print("Iniciando conversão...")

    try:
        converter_aws()

        print("Conversão concluída")

    except Exception as erro:
        print("Erro durante a conversão:") 
        print(erro) 
        
if __name__ == "__main__": 
    main()