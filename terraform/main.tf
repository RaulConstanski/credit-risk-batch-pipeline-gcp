# 1. Configuração dos Provedores requeridos pelo Terraform
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0" # Usa a versão estável mais recente do provedor GCP
    }
  }
}

# 2. Configuração do Provedor Google Cloud
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}

# 3. Ativação das APIs necessárias no GCP automaticamente via Código
# Como o projeto é novo, precisamos ativar os serviços antes de criar os recursos
resource "google_project_service" "services" {
  for_each = toset([
    "bigquery.googleapis.com",       # Para o Banco de Dados
    "run.googleapis.com",            # Para o Cloud Run Jobs (Modelos)
    "storage.googleapis.com",        # Para os Buckets de arquivos
    "iam.googleapis.com",            # Para gerenciamento de permissões de segurança
    "cloudscheduler.googleapis.com" # Para o agendador mensal batch
  ])

  project            = var.gcp_project_id
  service            = each.key
  disable_on_destroy = false
}