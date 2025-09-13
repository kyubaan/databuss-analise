import pandas as pd
import os
from datetime import datetime


def converter_csv_para_parquet(caminho_csv, caminho_parquet=None):
    """
    Converte um arquivo CSV grande para formato Parquet
    """
    print(f"Iniciando conversão: {datetime.now()}")

    # Definir caminho de saída
    if caminho_parquet is None:
        caminho_parquet = caminho_csv.replace('.csv', '.parquet')

    # 1. Primeiro: verificar tamanho original
    tamanho_original = os.path.getsize(caminho_csv) / (1024 * 1024)  # MB
    print(f"Tamanho original do CSV: {tamanho_original:.2f} MB")

    # 2. Ler apenas as colunas necessárias para análise
    colunas_essenciais = [
        'gmv_success',
        'date_purchase',
        'time_purchase',
        'place_destination_departure',
        'place_origin_return',
        'fk_contact'
    ]

    try:
        # 3. Ler o CSV em partes (chunks) se for muito grande
        print("Lendo arquivo CSV...")
        df = pd.read_csv(caminho_csv, usecols=colunas_essenciais)

        # 4. Converter para Parquet
        print("Convertendo para Parquet...")
        df.to_parquet(
            caminho_parquet,
            compression='snappy',  # Boa relação entre compressão e velocidade
            engine='pyarrow'
        )

        # 5. Verificar tamanho final
        tamanho_final = os.path.getsize(caminho_parquet) / (1024 * 1024)  # MB
        reducao = ((tamanho_original - tamanho_final) / tamanho_original) * 100

        print(f"✅ Conversão concluída: {datetime.now()}")
        print(f"📊 Tamanho original: {tamanho_original:.2f} MB")
        print(f"📊 Tamanho Parquet: {tamanho_final:.2f} MB")
        print(f"📉 Redução: {reducao:.1f}%")

        return caminho_parquet

    except Exception as e:
        print(f"❌ Erro durante a conversão: {e}")
        return None


def verificar_dados_parquet(caminho_parquet):
    """
    Verifica se os dados foram convertidos corretamente
    """
    try:
        print("\n🔍 Verificando dados Parquet...")
        df = pd.read_parquet(caminho_parquet)

        print(f"📋 Total de linhas: {len(df):,}")
        print(f"📋 Total de colunas: {len(df.columns)}")
        print(f"📋 Colunas: {list(df.columns)}")
        print("\n📊 Primeiras linhas:")
        print(df.head())

        return True

    except Exception as e:
        print(f"❌ Erro ao verificar Parquet: {e}")
        return False


# Executar a conversão
if __name__ == "__main__":
    # Substitua pelo caminho do seu arquivo
    arquivo_csv = "df_t.csv"
    arquivo_parquet = "dados_viagens.parquet"

    if os.path.exists(arquivo_csv):
        # Converter
        parquet_path = converter_csv_para_parquet(arquivo_csv, arquivo_parquet)

        if parquet_path:
            # Verificar
            verificar_dados_parquet(parquet_path)
    else:
        print(f"❌ Arquivo {arquivo_csv} não encontrado!")
        print("💡 Dica: Coloque o arquivo CSV na mesma pasta deste script")
