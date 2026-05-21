# TCC FinOps FOCUS

Projeto de TCC em desenvolvimento com foco em padronização de dados de custos cloud utilizando o modelo FOCUS (FinOps Open Cost and Usage Specification).

## Objetivo

O sistema recebe arquivos de custos cloud em diferentes formatos e realiza:

* leitura dos dados
* tratamento e normalização
* mapeamento de colunas
* conversão para o padrão FOCUS
* geração de relatórios e visualizações

## Tecnologias utilizadas

* Python
* Pandas
* Plotly
* FOCUS Specification

## Estrutura do projeto

```plaintext
TCC-FINOPS-FOCUS/
├── data/
│   ├── input/
│   └── output/
├── src/
│   ├── converters/
│   ├── mappings/
│   ├── schemas/
├── main.py
└── README.md
```

## Funcionalidades atuais

* Conversão de CSV AWS para FOCUS
* Mapeamento automático de colunas
* Geração de arquivo padronizado
* Geração de visualização dos dados

## Próximos passos

* Suporte para Azure
* Suporte para Google Cloud
* Detector automático de provedor
* Dashboard FinOps