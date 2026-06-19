# 1. Imagem base minimalista do Python oficial
FROM python:3.12-slim

# 2. Define variáveis de ambiente para garantir que o Python não trave em containers
# PYTHONDONTWRITEBYTECODE: Evita que o Python escreva arquivos .pyc no container
# PYTHONUNBUFFERED: Garante que os logs (print) saiam em tempo real no GCP Cloud Logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Define o diretório de trabalho interno do container
WORKDIR /app

# 4. Instala dependências do sistema operacional necessárias para o compilador do TensorFlow/C++
# Usamos o slim, então precisamos instalar o essencial e limpar o cache para manter a imagem leve
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 5. Copia o arquivo de requerimentos (que está na raiz do projeto) para dentro do container
# Como o requirements.txt está na raiz e o Dockerfile em src/pipeline, 
# o contexto do build será disparado da raiz do projeto.
COPY requirements.txt .

# 6. Atualiza o pip e instala as bibliotecas exatas do modelo (do TCC)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. Copia o código do pipeline e os modelos do TCC mantendo a estrutura original
COPY src/pipeline/ /app/src/pipeline/
COPY src/modelos/ /app/src/modelos/

# 8. Define a variável de ambiente do Python Path para que os imports relativos funcionem perfeitamente
ENV PYTHONPATH="/app"
# Variável de ambiente para ocultar logs de CUDA/GPU do TensorFlow (Oculta os logs 3 a 7)
ENV TF_CPP_MIN_LOG_LEVEL=2

# 9. Comando que o Cloud Run Jobs vai executar ao ser despertado
CMD ["python", "src/pipeline/run_pipeline.py"]