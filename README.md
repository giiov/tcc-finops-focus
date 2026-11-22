# FOCUS Multi-Cloud — API

> API em FastAPI que identifica, converte e analisa dados de custos de computação em nuvem usando o padrão FOCUS.

Este repositório é o **backend** do FOCUS Multi-Cloud. A interface web fica em outro repositório: [tcc-focus-frontend](https://github.com/giiov/tcc-focus-frontend).

---

## Sobre o projeto

O **FOCUS Multi-Cloud** é uma aplicação desenvolvida como Trabalho de Conclusão de Curso (TCC), com foco em FinOps (*Financial Operations*) e na padronização de dados financeiros de ambientes de computação em nuvem.

A API recebe arquivos CSV de custos de diferentes provedores, identifica a origem de cada arquivo e converte os dados para uma estrutura comum baseada no **FOCUS (FinOps Open Cost and Usage Specification)**, padrão mantido pela FinOps Foundation. Ela também calcula os indicadores usados nos gráficos do frontend e atende a assistente virtual **Ada**.

> **Projeto em desenvolvimento.** Os mapeamentos e as regras de transformação correspondem ao escopo desenvolvido pelo projeto e podem não contemplar todas as informações dos arquivos de origem nem toda a especificação FOCUS.

---

## Como funciona

`Upload do CSV` → `Detecção do provedor` → `Conversão` → `Schema FOCUS` → `Indicadores`

1. **Entrada:** o frontend envia o CSV para `POST /converter`, já autenticado.
2. **Detecção:** o provedor é identificado pelas colunas do arquivo. Vence o formato com mais colunas em comum.
3. **Conversão:** o conversor do provedor aplica os mapeamentos e as regras de transformação.
4. **Padronização:** os dados ficam no schema FOCUS do projeto.
5. **Resposta:** a API devolve o formato detectado, o total de linhas, as colunas, uma amostra das primeiras 100 linhas e os indicadores dos gráficos, calculados sobre a tabela inteira.

O arquivo é processado em uma pasta temporária e apagado ao fim da requisição. A API não guarda o CSV nem os dados convertidos.

A documentação interativa de todas as rotas (Swagger) é gerada automaticamente e fica em `/docs`.

---

## Assistente Ada

A Ada usa a API do **Groq** e esclarece conceitos de FinOps, do padrão FOCUS e de dados de custos em nuvem.

- Cada conversa é salva no banco, e a Ada lembra das últimas 10 mensagens.
- Se o usuário preencheu o perfil (cargo e provedores), ela adapta o nível técnico e os exemplos.
- Futuramente terá acesso às conversões feitas no site.

---

## Autenticação e banco de dados

O login é feito no frontend com o **Supabase Auth**. A API confere o token de cada requisição e consulta o banco **como aquele usuário**, e as regras de **RLS** (*Row Level Security*) garantem que cada pessoa só veja as próprias conversas e mensagens. Os scripts SQL das tabelas e das regras estão na pasta `db/`.

---

## Tecnologias

- **Python** e **FastAPI** (servidor Uvicorn)
- **Pandas**: leitura e transformação dos CSVs
- **Supabase**: autenticação e banco PostgreSQL
- **Groq**: modelo de linguagem da Ada
- **python-dotenv**: variáveis de ambiente

---

## Configuração

A API está publicada no **Render**. Ela usa estas variáveis de ambiente, definidas no painel do Render ou em um `.env` (veja o `.env.example`):

| Variável | Descrição |
|---|---|
| `GROQ_API_KEY` | Chave da API do Groq. |
| `GROQ_MODEL` | Modelo do Groq. Opcional. |
| `SUPABASE_URL` | URL do projeto no Supabase. |
| `SUPABASE_PUBLISHABLE_KEY` | Chave publishable do Supabase. |
| `FRONTEND_URLS` | Endereços do frontend liberados no CORS, separados por vírgula. |

Para rodar na sua máquina:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## Estrutura do projeto

```text
tcc-finops-focus/
├── main.py                 # app FastAPI, CORS e rota /converter
├── requirements.txt
├── .env.example
├── data/input/             # CSVs de exemplo de cada provedor
├── db/                     # scripts SQL do Supabase (tabelas e RLS)
└── src/
    ├── autenticacao.py     # valida o token do usuário
    ├── conversao.py        # detecta, converte e calcula os indicadores
    ├── rotas_conversas.py  # rotas das conversas da Ada
    ├── assistente/ai/      # cliente do Groq, prompt e lógica da Ada
    ├── converters/         # um conversor por provedor
    ├── mapping/            # mapeamentos de colunas e detector de provedor
    ├── schemas/            # schema FOCUS
    └── visualization/      # legado (versão Streamlit), não usado pela API
```

---

## Escopo e limitações atuais

- A entrada de dados é feita por arquivos **CSV**, com limite de 50 MB.
- A identificação automática considera as colunas do arquivo e os mapeamentos implementados.
- As transformações seguem regras específicas de cada provedor e o schema FOCUS adotado no projeto.
- A disponibilidade dos campos depende das informações do arquivo de origem.
- Os dados convertidos não são armazenados: a API devolve a amostra e os indicadores na própria resposta.
- A Ada não analisa o arquivo enviado nem os dados processados.
- Integrações diretas com contas de provedores e outros formatos de arquivo não fazem parte do fluxo atual.

---

## Equipe

| Integrante | Redes |
|---|---|
| Giovana Cipulo | [GitHub](https://github.com/giiov) · [LinkedIn](https://www.linkedin.com/in/giocipulo) |
| Antonella Cobianchi | [GitHub](https://github.com/antonellapruc31) · [LinkedIn](https://www.linkedin.com/in/antonella-cobianchi-505710370/) |
| Bruno Holanda | [GitHub](https://github.com/brunohlnd) · [LinkedIn](https://www.linkedin.com/in/bhb-holanda) |