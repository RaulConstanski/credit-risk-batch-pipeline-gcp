# 1. Criação do Dataset de Crédito no BigQuery
resource "google_bigquery_dataset" "credit_dataset" {
  dataset_id                  = var.bq_dataset_name
  friendly_name               = "Credit Risk Analytics"
  description                 = "Dataset para armazenamento de faturas mensais e predições de risco de crédito do TCC."
  location                    = var.gcp_region
  default_table_expiration_ms = null # As tabelas são permanentes
}

# 2. Tabela de Ingestão: Dados brutos das faturas do Kaggle (Sem o Target)
resource "google_bigquery_table" "tb_faturas_fechadas" {
  dataset_id          = google_bigquery_dataset.credit_dataset.dataset_id
  table_id            = "tb_faturas_fechadas"
  deletion_protection = false

  schema = <<EOF
[
  { "name": "id_cliente", "type": "INTEGER", "mode": "REQUIRED", "description": "Coluna 'ID' original do dataset" },
  { "name": "safra", "type": "STRING", "mode": "REQUIRED", "description": "Mês de referência da rodada (AAAA-MM)" },
  { "name": "LIMIT_BAL", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor do crédito concedido (em dólares NT)" },
  { "name": "SEX", "type": "INTEGER", "mode": "NULLABLE", "description": "Gênero (1 = masculino; 2 = feminino)" },
  { "name": "EDUCATION", "type": "INTEGER", "mode": "NULLABLE", "description": "Escolaridade (1 = pós-graduação; 2 = universidade; 3 = ensino médio; 4 = outros)" },
  { "name": "MARRIAGE", "type": "INTEGER", "mode": "NULLABLE", "description": "Estado civil (1 = casado; 2 = solteiro; 3 = outros)" },
  { "name": "AGE", "type": "INTEGER", "mode": "NULLABLE", "description": "Idade (em anos)" },
  { "name": "PAY_1", "type": "INTEGER", "mode": "NULLABLE", "description": "Status de pagamento em m-0" },
  { "name": "PAY_2", "type": "INTEGER", "mode": "NULLABLE", "description": "Status de pagamento em m-1" },
  { "name": "PAY_3", "type": "INTEGER", "mode": "NULLABLE", "description": "Status de pagamento em m-2" },
  { "name": "PAY_4", "type": "INTEGER", "mode": "NULLABLE", "description": "Status de pagamento em m-3" },
  { "name": "PAY_5", "type": "INTEGER", "mode": "NULLABLE", "description": "Status de pagamento em m-4" },
  { "name": "PAY_6", "type": "INTEGER", "mode": "NULLABLE", "description": "Status de pagamento em m-5" },
  { "name": "BILL_AMT1", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor da fatura em m-0" },
  { "name": "BILL_AMT2", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor da fatura em m-1" },
  { "name": "BILL_AMT3", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor da fatura em m-2" },
  { "name": "BILL_AMT4", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor da fatura em m-3" },
  { "name": "BILL_AMT5", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor da fatura em m-4" },
  { "name": "BILL_AMT6", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor da fatura em m-5" },
  { "name": "PAY_AMT1", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor pago em m-0" },
  { "name": "PAY_AMT2", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor pago em m-1" },
  { "name": "PAY_AMT3", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor pago em m-2" },
  { "name": "PAY_AMT4", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor pago em m-3" },
  { "name": "PAY_AMT5", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor pago em m-4" },
  { "name": "PAY_AMT6", "type": "FLOAT", "mode": "NULLABLE", "description": "Valor pago em m-5" }
]
EOF
}

# 3. Tabela Histórica Destino: Onde o script vai salvar o resultado dos modelos
resource "google_bigquery_table" "tb_predicoes_inadimplencia" {
  dataset_id          = google_bigquery_dataset.credit_dataset.dataset_id
  table_id            = "tb_predicoes_inadimplencia"
  deletion_protection = false

  schema = <<EOF
[
  { "name": "id_cliente", "type": "INTEGER", "mode": "REQUIRED" },
  { "name": "safra", "type": "STRING", "mode": "REQUIRED" },
  { "name": "prob_inadimplencia_svm", "type": "FLOAT", "mode": "NULLABLE", "description": "Probabilidade calculada pelo SVM" },
  { "name": "prob_inadimplencia_lstm", "type": "FLOAT", "mode": "NULLABLE", "description": "Probabilidade calculada pelo LSTM (Modo Shadow)" },
  { "name": "score_final_decisao", "type": "FLOAT", "mode": "NULLABLE", "description": "Score oficial usado pela mesa de crédito" },
  { "name": "modelo_decisor", "type": "STRING", "mode": "NULLABLE", "description": "Modelo que carimbou a decisão oficial (SVM/LSTM)" },
  { "name": "flag_inadimplente_previsto", "type": "INTEGER", "mode": "NULLABLE", "description": "Corte binário: 1 para Alto Risco, 0 para Baixo Risco" },
  { "name": "data_processamento", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Data/Hora em que a previsão foi gerada" }
]
EOF
}