# 1. Repositório no Artifact Registry para armazenar a imagem Docker do Pipeline
resource "google_artifact_registry_repository" "pipeline_repo" {
  location      = var.gcp_region
  repository_id = "credit-risk-pipeline-repo"
  description   = "Repositorio Docker para as imagens do pipeline de Machine Learning (SVM e LSTM)"
  format        = "DOCKER"

  # Garante que as APIs do main.tf sejam ativadas ANTES de tentar criar o repositório
  depends_on = [google_project_service.services]
}

# 2. Bucket do Cloud Storage para Zona de Landing (Upload dos arquivos CSV brutos)
resource "google_storage_bucket" "landing_bucket" {
  name                        = "${var.gcp_project_id}-landing-zone"
  location                    = var.gcp_region
  force_destroy               = true # Permite apagar o bucket com arquivos dentro se deletarmos o projeto
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  # Evita problemas de concorrência com a ativação de APIs
  depends_on = [google_project_service.services]
}