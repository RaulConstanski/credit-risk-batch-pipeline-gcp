# 1. Criação de uma Conta de Serviço própria para o Pipeline (Melhor prática de segurança)
resource "google_service_account" "pipeline_sa" {
  account_id   = "credit-risk-pipeline-sa"
  display_name = "Pipeline Credit Risk Service Account"
  description  = "Conta de servico usada pelo Cloud Run Job para acessar BigQuery e Storage."
}

# 2. Atribuição de permissão no BigQuery (Data Editor + Job User para rodar queries)
resource "google_project_iam_member" "bq_editor" {
  project = var.gcp_project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

resource "google_project_iam_member" "bq_job_user" {
  project = var.gcp_project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# 3. Atribuição de permissão no Storage (Para ler arquivos se precisar no futuro)
resource "google_project_iam_member" "gcs_viewer" {
  project = var.gcp_project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# 4. Definição do Cloud Run Job (O Executor Batch do Container)
resource "google_cloud_run_v2_job" "pipeline_job" {
  name     = "credit-risk-batch-job"
  location = var.gcp_region

  template {
    template {
      service_account = google_service_account.pipeline_sa.email

      containers {
        # Aponta para a imagem que vamos buildar e subir no Artifact Registry
        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/credit-risk-pipeline-repo/pipeline-image:latest"

        # Injeção das Variáveis de Ambiente que o run_pipeline.py espera!
        env {
          name  = "GCP_PROJECT_ID"
          value = var.gcp_project_id
        }
        env {
          name  = "BQ_DATASET_NAME"
          value = var.bq_dataset_name
        }
        env {
          name  = "BQ_TABLE_INPUT"
          value = "tb_faturas_fechadas"
        }
        env {
          name  = "BQ_TABLE_OUTPUT"
          value = "tb_predicoes_inadimplencia"
        }
        env {
          name  = "MODELO_PRODUCAO"
          value = "SVM" # <-- O Switch de Produção está aqui! É possível mudar para o LSTM no futuro.
        }

        # Configuração de recursos básicos (O TensorFlow exige um pouquinho mais de RAM)
        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }
    }
  }

  # Garante que as APIs e o repositório Docker já existam antes do Job ser desenhado
  depends_on = [
    google_project_service.services,
    google_artifact_registry_repository.pipeline_repo
  ]
}