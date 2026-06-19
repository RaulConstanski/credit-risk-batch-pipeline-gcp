# Pipeline Batch Serverless para Escoragem de Risco de Crédito (GCP & MLOps)

![GCP](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![BigQuery](https://img.shields.io/badge/BigQuery-669DF2?style=for-the-badge&logo=google-cloud&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/scikit_learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)

## 1. Introdução e Motivação do Estudo de Caso

O objetivo deste projeto é realizar a **transição de um modelo de Machine Learning acadêmico (desenvolvido em ambiente isolado com o Google Colab) para um ambiente de produção industrializado e serverless na nuvem**. 

Focado no mercado financeiro e de concessão de crédito, o estudo de caso aborda o desafio de processar dados volumosos de faturas de cartões de crédito para prever a probabilidade de inadimplência dos clientes (*default*). A arquitetura simula a virada de ciclo de faturas de uma instituição financeira, onde a esteira de crédito consome dados históricos mensais (Safras) para calcular o risco da carteira de forma automatizada e escalável.

---

## 2. Arquitetura de MLOps (Shadow Deployment)

O ecossistema foi desenhado adotando a estratégia de **Shadow Deployment (Implementação de Sombra)** para governança e validação de modelos em produção:

1. **Modelo Oficial (Champion):** Um modelo baseado em **SVM (Support Vector Machine)** atua como o decisor oficial da política de crédito, gerando os flags de decisão e os cortes de risco (*cut-off*).
2. **Modelo Sombra (Shadow):** Uma rede neural **LSTM (Long Short-Term Memory)** roda em paralelo dentro do mesmo container. Ela consome o mesmo dado tratado, porém estruturado em um cubo temporal tridimensional (Amostras, 6 Meses, 14 Features), gravando seus scores na tabela final para fins de monitoramento, auditoria e calibração antes de uma futura substituição de modelo. Maiores detalhes dentro do meu repositório: https://github.com/RaulConstanski/TCC_Previsao_Inadimplencia_Credito_com_Machine_Learning

### O Fluxo dos Dados:
* **Ingestão/Simulador:** Um simulador local faz o papel dos sistemas legados da instituição, injetando safras de dados incrementais diretamente na tabela de entrada do **Google BigQuery** criada por **terraform**.
* **Processamento Batch:** O **Cloud Run Jobs** acorda sob demanda (Aqui não fiz um gatilho, poderia ser uma data do mês, mas o ideal seria a ingestão dos dados no bigquery), puxa a imagem Docker correspondente do **Artifact Registry**, processa a safra alvo na memória através do pipeline Python, gera as predições de ambos os modelos de IA e desliga o processamento imediatamente.
* **Consolidação:** Os resultados escorados (probabilidades individuais, modelo decisor, flag de risco e timestamp de execução) são consolidados via operação de *Append* em uma tabela histórica no BigQuery para consumo de dashboards ou motores de decisão analíticos.

---

## 3. Ferramentas e Tecnologias Utilizadas

* **Python 3.12:** Linguagem base de todo o pipeline, tratamento analítico e engenharia de recursos.
* **Google BigQuery:** Data Warehouse corporativo escalável, utilizado como Landing Zone dos dados brutos e Storage analítico dos scores finais.
* **Google Cloud Run Jobs:** Engine serverless ideal para cargas de trabalho batch computacionalmente densas. Garante cobrança estrita por segundo de execução do container.
* **Google Artifact Registry:** Repositório seguro e centralizado para gerenciamento e versionamento das imagens Docker.
* **Terraform (IaC):** Infraestrutura como Código utilizada para provisionar, versionar e destruir de forma transparente e idempotente todos os recursos necessários na GCP (Datasets, Tabelas, Permissões IAM e Jobs).
* **Docker:** Tecnologia de containerização para garantir o isolamento completo de todas as dependências do modelo (incluindo ambientes densos como TensorFlow e Scikit-Learn).

---

## 4. Desafios de MLOps Superados (Lições de Produção)

A transição do modelo do notebook para o ambiente de nuvem, claro, não funcionou perfeitamente de primeira, exigiu a resolução de problemas de ambiente, verificados pelos logs de execução do job:

### 4.1. Alinhamento de Imutabilidade e Deserialização do Keras
* **O Problema:** Durante os testes na nuvem, a rede LSTM quebrou com erros de deserialização na camada oculta (`Dense layer could not be deserialized properly - unrecognized keyword arguments: quantization_config`), embora o pipeline funcionasse localmente.
* **A Causa:** O container Docker inicial utilizava o `python:3.10-slim`, enquanto o ambiente onde os artefatos binários (`.keras`) foram exportados operava em `Python 3.12`. Essa discrepância alterava a ordenação e leitura de dicionários de baixo nível do Keras.
* **A Solução:** O ambiente do container foi atualizado e equalizado para **`python:3.12-slim`**, garantindo paridade absoluta entre desenvolvimento (Notebook), homologação (Local) e produção (Cloud Run).

### 4.2. Governança e Congelamento de Versões (*Version Pinning*)
* **O Problema:** Erros de carregamento no pré-processador analítico (`AttributeError: Can't get attribute '_RemainderColsList' on sklearn`) ocorreram devido ao comportamento de download padrão do gerenciador de pacotes.
* **A Solução:** Foi implementada uma governança estrita no arquivo `requirements.txt`. O Scikit-Learn foi cravado na versão exata do treinamento acadêmico (`scikit-learn==1.6.1`) e dependências do Google Cloud (como `db-dtypes`, `google-cloud-bigquery-storage` e `pandas-gbq`) foram rigidamente versionadas para impedir que futuras atualizações automáticas quebrem a esteira produtiva.

### 4.3. Testes Incrementais de Volumetria e Idempotência
* Para garantir a estabilidade do container diante do crescimento da carteira, a esteira foi testada de forma incremental:
  * **Mesa Piloto:** 100 clientes (Safra `2026-01`)
  * **Teste de Carga Inicial:** 500 clientes (Safra `2026-02`)
  * **Validação de Produção:** **10.000 clientes** processados de forma centralizada em uma única execução batch na nuvem, sem estouro de memória ou gargalos de I/O.
* Foi implementado o conceito de **Idempotência de Dados**: Garantiu-se que reexecuções de uma mesma safra não gerassem duplicações na tabela destino no BigQuery, através de operações de limpeza controlada antes da consolidação dos lotes analíticos.

---

## 📁 5. Estrutura do Repositório

```text
credit-risk-batch-pipeline-gcp/
├── .venv/                     # Ambiente virtual Python isolado localmente
├── simulador/
│   ├── data/
│   │   └── input/
│   │       └── default_of_credit_card_clients.csv # Base bruta do Kaggle com 30k clientes
│   └── gerar_safras.py        # Script interativo de carga incremental para o BQ
├── src/
│   ├── modelos/
│   │   ├── melhor_modelo_lstm.keras    # Rede Neural Temporal (Shadow)
│   │   ├── melhor_modelo_svm.pkl       # Classificador Oficial (Champion)
│   │   └── preprocess_scaler-onehot.pkl # Transformador analítico unificado
│   └── pipeline/
│       ├── Dockerfile         # Receita do container configurada em Python 3.12-slim
│       └── run_pipeline.py    # Coração do pipeline batch analítico
├── terraform/
│   ├── main.tf                # Provedores e definições base da GCP
│   ├── variables.tf           # Variáveis globais de infraestrutura
│   ├── bigquery.tf            # Criação estrita do Dataset e Tabelas analíticas
│   └── cloud_run.tf           # Definição física do Cloud Run Job Serverless
├── requirements.txt           # Dependências do ecossistema de produção cravadas
└── .gitignore                 # Proteção de arquivos locais e credenciais