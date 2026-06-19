import os
import sys
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import joblib
from google.cloud import bigquery


# 1. Carregamento das Variáveis de Ambiente
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "credit-risk-pipeline-498702")
DATASET_NAME = os.getenv("BQ_DATASET_NAME", "credit_risk_analytics")
TABLE_INPUT = os.getenv("BQ_TABLE_INPUT", "tb_faturas_fechadas")
TABLE_OUTPUT = os.getenv("BQ_TABLE_OUTPUT", "tb_predicoes_inadimplencia")
MODELO_PRODUCAO = os.getenv("MODELO_PRODUCAO", "SVM") 
SAFRA_ALVO = os.getenv("SAFRA_ALVO", "2026-01") 

print(f"🎬 Iniciando Pipeline Batch de Risco de Crédito")
print(f"📌 Projeto: {PROJECT_ID} | Safra de Processamento: {SAFRA_ALVO}")
print(f"⚙️  Modelo definido como Decisor Oficial: {MODELO_PRODUCAO}\n")

# Auxiliar: Função customizada de Reshape para a sua LSTM do TCC
def reshape_para_lstm_array(X_array):
    """
    Transforma a matriz plana de 29 colunas do ColumnTransformer 
    no formato 3D exigido pela rede LSTM: (Amostras, 6 Meses, 14 Features)
    """
    estaticas_indices = [0, 1] + list(range(20, 29)) # LIMIT_BAL, AGE + 9 Dummies do OneHot

    ordem_meses = [5, 4, 3, 2, 1, 0] # Ordem cronológica dos 6 meses de histórico

    pay_idxs = [2, 3, 4, 5, 6, 7]        # PAY_1 até PAY_6
    bill_idxs = [8, 9, 10, 11, 12, 13]    # BILL_AMT1 até BILL_AMT6
    pamt_idxs = [14, 15, 16, 17, 18, 19]  # PAY_AMT1 até PAY_AMT6

    sequencia_3d = []

    for m in ordem_meses:
        temporais_do_mes = [pay_idxs[m], bill_idxs[m], pamt_idxs[m]]
        indices_fatia = temporais_do_mes + estaticas_indices
        fatia = X_array[:, indices_fatia]
        sequencia_3d.append(fatia)

    return np.stack(sequencia_3d, axis=1)

# 2. Inicialização do Cliente BigQuery
client = bigquery.Client(project=PROJECT_ID)

# 3. Download dos Dados Brutos da Safra Alvo
query = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_NAME}.{TABLE_INPUT}`
    WHERE safra = '{SAFRA_ALVO}'
"""
print("🔍 Buscando dados brutos no BigQuery...")
df_bruto = client.query(query).to_dataframe()

if df_bruto.empty:
    print(f"⚠️  Atenção: Nenhuns dados foram encontrados para a safra {SAFRA_ALVO}. Encerrando pipeline.")
    sys.exit(0)

print(f"📊 {len(df_bruto)} clientes encontrados para processamento.")

# 4. Separação de Metadados e Ordenação Estrita das Features
df_metadados = df_bruto[['id_cliente', 'safra']].copy()

# A ordem precisa casar 100% com a ordem das colunas que gerou o seu venv/ColumnTransformer
features_ordem_treino = [
    'LIMIT_BAL', 'SEX', 'EDUCATION', 'MARRIAGE', 'AGE',
    'PAY_1', 'PAY_2', 'PAY_3', 'PAY_4', 'PAY_5', 'PAY_6',
    'BILL_AMT1', 'BILL_AMT2', 'BILL_AMT3', 'BILL_AMT4', 'BILL_AMT5', 'BILL_AMT6',
    'PAY_AMT1', 'PAY_AMT2', 'PAY_AMT3', 'PAY_AMT4', 'PAY_AMT5', 'PAY_AMT6'
]
df_features = df_bruto[features_ordem_treino].copy()

# 5. Carregamento dos Artefatos de Inteligência Artificial
CAMINHO_MODELOS = "src/modelos" if os.path.exists("src/modelos") else "/app/src/modelos"

print("🧠 Carregando artefatos de Machine Learning...")
preprocessador = joblib.load(f"{CAMINHO_MODELOS}/preprocess_scaler-onehot.pkl")
modelo_svm = joblib.load(f"{CAMINHO_MODELOS}/melhor_modelo_svm.pkl")

modelo_lstm = None
try:
    from tensorflow.keras.models import load_model
    modelo_lstm = load_model(f"{CAMINHO_MODELOS}/melhor_modelo_lstm.keras")
    print("✅ LSTM (Modelo Shadow) carregado com sucesso.")
except Exception as e:
    print(f"⚠️  Aviso ao carregar o LSTM: {e}. O pipeline seguirá apenas com o SVM.")

# 6. Pré-processamento dos Dados (Gera a matriz plana de 29 colunas)
print("🧪 Aplicando transformações matemáticas nos dados brutos (Scale & Encode)...")
X_transformado = preprocessador.transform(df_features)

# 7. Escoragem dos Modelos (Predição de Probabilidades)
print("🔮 Gerando scores de risco de inadimplência...")

# Modelo 1: SVM (Consome a matriz 2D diretamente)
prob_svm = modelo_svm.predict_proba(X_transformado)[:, 1]

# Modelo 2: LSTM (Consome a estrutura 3D gerada pela sua função do TCC)
if modelo_lstm is not None:
    print("🔄 Redimensionando dados para a estrutura temporal da LSTM...")
    X_3d = reshape_para_lstm_array(X_transformado)
    prob_lstm = modelo_lstm.predict(X_3d, verbose=0).flatten()
else:
    prob_lstm = [None] * len(df_bruto)

# 8. Aplicação da Regra de Política de Crédito (Switch de Modelos)
if MODELO_PRODUCAO == "SVM":
    score_final = prob_svm
else:
    score_final = prob_lstm if modelo_lstm is not None else prob_svm

flag_decisao = [1 if s >= 0.5 else 0 for s in score_final]

# 9. Estruturação do DataFrame de Saída
df_saida = pd.DataFrame({
    'id_cliente': df_metadados['id_cliente'],
    'safra': df_metadados['safra'],
    'prob_inadimplencia_svm': prob_svm,
    'prob_inadimplencia_lstm': prob_lstm,
    'score_final_decisao': score_final,
    'modelo_decisor': MODELO_PRODUCAO,
    'flag_inadimplente_previsto': flag_decisao,
    'data_processamento': datetime.now(timezone.utc)
})

# 10. Escrita dos Resultados na Tabela Histórica do BigQuery
print(f"💾 Gravando os resultados na tabela destino: '{TABLE_OUTPUT}'...")
full_table_ref_output = f"{PROJECT_ID}.{DATASET_NAME}.{TABLE_OUTPUT}"

job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
job = client.load_table_from_dataframe(df_saida, full_table_ref_output, job_config=job_config)
job.result()

print(f"🎉 Fim do processo! {len(df_saida)} scores de crédito gerados e salvos com sucesso na nuvem.")