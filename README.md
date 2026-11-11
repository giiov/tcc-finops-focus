
# ☁️ FOCUS Multi-Cloud

> Aplicação web para padronização e análise de dados de custos de computação em nuvem, utilizando o padrão FOCUS.

---

## 📖 Sobre o projeto

O **FOCUS Multi-Cloud** é uma aplicação desenvolvida como Trabalho de Conclusão de Curso (TCC), orientado pela **Proative**, com foco em FinOps (*Financial Operations*) e na padronização de dados financeiros de ambientes de computação em nuvem.

A ferramenta recebe arquivos CSV de custos de diferentes provedores, identifica automaticamente sua origem e converte os dados para uma estrutura comum baseada no **FOCUS (FinOps Open Cost and Usage Specification)**, padrão mantido pela FinOps Foundation.

Com os dados padronizados, o usuário pode consultar os registros convertidos, visualizar indicadores e gráficos e exportar o resultado para apoiar análises financeiras e processos de Business Intelligence (BI).

> 🚧 **Projeto em desenvolvimento.** Os mapeamentos e as regras de transformação implementados correspondem ao escopo desenvolvido pelo projeto e podem não contemplar todas as informações disponíveis nos arquivos de origem ou toda a especificação FOCUS.

---

## ✦ Como funciona

O processamento é organizado em um fluxo de etapas:

`Upload do CSV` → `Detecção do provedor` → `Conversão e tratamento` → `Padronização FOCUS` → `Visualização e exportação`

1. **Entrada:** o usuário envia um arquivo CSV de custos.
2. **Detecção:** a aplicação identifica o provedor a partir das colunas presentes no arquivo.
3. **Conversão:** o conversor específico do provedor aplica os mapeamentos e as regras de transformação correspondentes.
4. **Padronização:** os dados são organizados no schema FOCUS definido pelo projeto.
5. **Exploração:** os registros convertidos podem ser consultados em tabela, analisados por gráficos e indicadores e exportados em CSV.

---

## ☁️ Provedores suportados

| Provedor | Colunas de origem mapeadas |
|----------|---------------------------:|
| AWS | 15 |
| Microsoft Azure | 14 |
| Google Cloud | 11 |
| Oracle Cloud | 11 |

A saída padronizada segue um schema com 26 colunas FOCUS, sendo 21 obrigatórias e 5 condicionais.

---

## ✦ O que fazemos?

Dados de custos de diferentes provedores podem apresentar estruturas, nomenclaturas e formatos distintos. O FOCUS Multi-Cloud simplifica esse processo por meio de um fluxo automatizado:

`Entrada` → `Detecção` → `Tratamento` → `Padronização FOCUS` → `Análise`

A proposta é transformar diferentes formatos de dados em uma estrutura comum, facilitando sua utilização em análises de custos e processos de FinOps.

---

### Sobre a assistente Ada

A Ada utiliza integração com a API do Groq e tem como objetivo esclarecer conceitos e orientar o usuário sobre FinOps, FOCUS e dados de custos em nuvem. Ela não acessa o arquivo enviado nem os dados processados na sessão; suas respostas são baseadas no contexto e nas instruções configuradas para a assistente.

---

## 📊 Funcionalidades

- Upload e identificação automática de arquivos CSV.
- Tratamento e padronização de dados de custos cloud.
- Conversão para o schema FOCUS.
- Visualização de indicadores e gráficos interativos.
- Exportação dos dados padronizados.
- Assistente virtual Ada para dúvidas sobre FinOps e FOCUS.

---

## 🖥️ Interface da aplicação

A aplicação é organizada em quatro áreas principais:

| Área | Descrição |
|---|---|
| **Início** | Envio do arquivo CSV e acompanhamento do processamento. |
| **Dados** | Consulta da tabela padronizada, identificação das colunas disponíveis e exportação do CSV. |
| **Visualizações** | Exibição de indicadores e gráficos gerados a partir dos dados convertidos. |
| **Sobre** | Apresentação do projeto, do padrão FOCUS e das tecnologias utilizadas. |

---

## 🛠️ Tecnologias utilizadas

- **Python** — linguagem principal e lógica de processamento.
- **Streamlit** — desenvolvimento da interface web.
- **Pandas** — leitura, tratamento e transformação dos dados.
- **Plotly** — geração de gráficos interativos.
- **Groq** — integração utilizada pela assistente virtual Ada.
- **python-dotenv** — carregamento de variáveis de ambiente.

---

## ▶️ Como executar o projeto

### Pré-requisitos

- Python instalado.
- Git (opcional, para clonar o repositório).

### 1. Clone o repositório

```bash
git clone https://github.com/giiov/tcc-finops-focus.git
cd tcc-finops-focus
```

### 2. Crie e ative um ambiente virtual (recomendado)

No Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

No Linux ou macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure a assistente Ada (opcional)

Para utilizar a assistente, crie um arquivo `.env` na raiz do projeto e configure sua chave da API do Groq:

```env
GROQ_API_KEY=sua_chave_aqui
```

A variável `GROQ_MODEL` também pode ser definida para selecionar outro modelo compatível. Se ela não for configurada, a aplicação utiliza o modelo padrão definido no código.

### 5. Execute a aplicação

```bash
streamlit run app_streamlit.py
```

Após a execução, o Streamlit disponibilizará o endereço local para acessar a aplicação pelo navegador.

---

## 📁 Estrutura do projeto

```text
tcc-finops-focus/
├── app_streamlit.py
├── main.py
├── requirements.txt
├── data/
│   └── input/
├── src/
│   ├── assistente/
│   │   ├── ai/
│   │   └── ui/
│   ├── converters/
│   ├── mapping/
│   ├── schemas/
│   ├── visualization/
│   └── logo_nuvem.png
└── .streamlit/
```

---

## ⚠️ Escopo e limitações atuais

- A entrada de dados pela interface é feita por arquivos **CSV**.
- A identificação automática considera as colunas presentes no arquivo e os mapeamentos implementados.
- As transformações seguem regras específicas para cada provedor e o schema FOCUS adotado no projeto.
- A disponibilidade dos campos depende das informações fornecidas pelo arquivo de origem.
- A assistente Ada não realiza análise direta do arquivo enviado nem dos dados processados.
- Integrações diretas com contas de provedores, bancos de dados e outros formatos de arquivo não fazem parte do fluxo atual da aplicação.

---

## 👥 Equipe

| Integrante | Redes |
|---|---|
| Giovana Cipulo | [GitHub](https://github.com/giiov) · [LinkedIn](https://www.linkedin.com/in/giocipulo) |
| Antonella Cobianchi | [GitHub](https://github.com/antonellapruc31) · [LinkedIn](https://www.linkedin.com/in/antonella-cobianchi-505710370/) |
| Bruno Holanda | [GitHub](https://github.com/brunohlnd) · [LinkedIn](https://www.linkedin.com/in/bhb-holanda) |
