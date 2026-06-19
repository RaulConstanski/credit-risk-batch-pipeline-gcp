import os
import pandas as pd
from google.cloud import bigquery

# Configurações do ambiente do GCP (Apontando para o seu projeto atual)
PROJECT_ID = "credit-risk-pipeline-498702"
DATASET_ID = "credit_risk_analytics"
TABLE_ID = "tb_faturas_fechadas"
FULL_TABLE_REF = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

CSV_PATH = "simulador/data/input/default_of_credit_card_clients.csv"

def carregar_e_preparar_base():
    if not os.path.exists(CSV_PATH):
        print(f"Erro: O arquivo {CSV_PATH} não foi encontrado!")
        print("Por favor, salve o CSV do Kaggle nessa pasta antes de rodar.")
        return None

    print("Carregando base completa do Kaggle...")
    df = pd.read_csv(CSV_PATH)
    
    # Adequando o DataFrame ao Schema estrito do BigQuery
    # 1. Renomeia o ID
    df = df.rename(columns={'ID': 'id_cliente'})
    
    # 2. Remove a coluna Target (Produção não conhece o futuro)
    if 'default payment next month' in df.columns:
        df = df.drop(columns=['default payment next month'])
        
    return df

def enviar_para_bigquery(df_safra, nome_safra):
    print(f"Conectando ao BigQuery para injetar a safra {nome_safra} ({len(df_safra)} clientes)...")
    client = bigquery.Client(project=PROJECT_ID)
    
    # Configuração do Job de Carga para garantir compatibilidade
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND" # APPEND garante que acumula os dados sem apagar os meses anteriores
    )
    
    job = client.load_table_from_dataframe(df_safra, FULL_TABLE_REF, job_config=job_config)
    job.result() # Aguarda a conclusão do upload
    
    print(f"Sucesso! {len(df_safra)} registros inseridos na tabela '{TABLE_ID}' para a safra {nome_safra}.\n")

def main():
    df_completo = carregar_e_preparar_base()
    if df_completo is None:
        return
# Incluindo safra lote a lote para testar modelos.
    print("\n--- MENU DO SIMULADOR DE SAFRAS DE CRÉDITO ---")
    print("1 - Injetar Safra 1 (100 clientes)   -> Ref: 2026-01")
    print("2 - Injetar Safra 2 (500 clientes)   -> Ref: 2026-02")
    print("3 - Injetar Safra 3 (1000 clientes)  -> Ref: 2026-03")
    print("4 - Injetar Safra 4 (2000 clientes)  -> Ref: 2026-04")
    print("5 - Injetar Safra 5 (5000 clientes)  -> Ref: 2026-05")
    print("6 - Injetar Safra 6 (10000 clientes) -> Ref: 2026-06")
    print("0 - Sair")
    
    opcao = input("\nEscolha qual safra deseja enviar para a nuvem: ")
    
    if opcao == '1':
        # Safra 1: Pega os primeiros 100 registros (linhas 0 a 100)
        df_safra = df_completo.iloc[0:100].copy()
        df_safra['safra'] = '2026-01'
        enviar_para_bigquery(df_safra, '2026-01')
        
    elif opcao == '2':
        # Safra 2: Próximos 500 registros (linhas 100 a 600)
        df_safra = df_completo.iloc[100:600].copy()
        df_safra['safra'] = '2026-02'
        enviar_para_bigquery(df_safra, '2026-02')
        
    elif opcao == '3':
        # Safra 3: Próximos 1000 registros (linhas 600 a 1600)
        df_safra = df_completo.iloc[600:1600].copy()
        df_safra['safra'] = '2026-03'
        enviar_para_bigquery(df_safra, '2026-03')
        
    elif opcao == '4':
        # Safra 4: Próximos 2000 registros (linhas 1600 a 3600)
        df_safra = df_completo.iloc[1600:3600].copy()
        df_safra['safra'] = '2026-04'
        enviar_para_bigquery(df_safra, '2026-04')
    
    elif opcao == '5':
        # Safra 5: Próximos 5000 registros (linhas 3600 a 8600)
        df_safra = df_completo.iloc[3600:8600].copy()
        df_safra['safra'] = '2026-05'
        enviar_para_bigquery(df_safra, '2026-05')

    elif opcao == '6':
        # Safra 6: Próximos 10000 registros (linhas 8600 a 18600)
        df_safra = df_completo.iloc[8600:18600].copy()
        df_safra['safra'] = '2026-06'
        enviar_para_bigquery(df_safra, '2026-06')

    elif opcao == '0':
        print("Saindo do simulador.")
    else:
        print("Opção inválida!")

if __name__ == "__main__":
    main()