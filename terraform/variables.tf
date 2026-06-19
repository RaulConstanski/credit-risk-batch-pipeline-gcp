variable "gcp_project_id" {
  type        = string
  description = "O ID do projeto que você acabou de criar no GCP"
  default     = "credit-risk-pipeline-498702" # <-- SUBSTITUA pelo ID real que você criou
}

variable "gcp_region" {
  type        = string
  description = "Região padrão para os recursos do GCP"
  default     = "us-central1" # Região com excelente custo-benefício e disponibilidade no GCP
}

variable "gcp_zone" {
  type        = string
  description = "Zona padrão para os recursos"
  default     = "us-central1-a"
}

variable "bq_dataset_name" {
  type        = string
  description = "Nome do dataset no BigQuery onde as tabelas serão criadas"
  default     = "credit_risk_analytics" # Nome do dataset para o TCC
  
}