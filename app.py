import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import numpy as np
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="DataBus - Análise de Viagens", page_icon="🚌", layout="wide")

# Configuração de estilo
click_bus_palette = ["#6A0DAD", "#FFD700", "#9B30FF", "#FFDF00", "#4B0082", "#DAA520"]
sns.set_palette(click_bus_palette)
plt.style.use('default')

def processar_amostra_csv(uploaded_file, tamanho_amostra=50000):
    """Processa uma amostra do CSV grande"""
    try:
        st.info("📊 Processando amostra representativa...")
        
        # Ler apenas as colunas essenciais
        colunas_essenciais = ['gmv_success', 'date_purchase', 'time_purchase',
                             'place_destination_departure', 'place_origin_return']
        
        # Verificar quais colunas existem no arquivo
        uploaded_file.seek(0)
        primeira_linha = pd.read_csv(uploaded_file, nrows=0)
        uploaded_file.seek(0)
        
        colunas_para_ler = [col for col in colunas_essenciais if col in primeira_linha.columns]
        
        # Ler amostra
        df = pd.read_csv(uploaded_file, usecols=colunas_para_ler, nrows=tamanho_amostra)
        
        # Pré-processamento
        if 'date_purchase' in df.columns and 'time_purchase' in df.columns:
            df['data_hora'] = pd.to_datetime(
                df['date_purchase'] + ' ' + df['time_purchase'],
                errors='coerce'
            )
            df = df.dropna(subset=['data_hora'])
            df['mes_ano'] = df['data_hora'].dt.to_period('M')
        
        if 'place_origin_return' in df.columns:
            df['tem_retorno'] = df['place_origin_return'] != '0'
            
        st.success(f"✅ Amostra processada: {len(df):,} registros")
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao processar: {str(e)}")
        return None

def main():
    st.title("🚌 DataBus - Análise de Viagens ClickBus")
    
    st.markdown("""
    ## 📋 Análise de Dados de Viagens
    
    **💡 Para arquivos grandes:** O sistema usa uma amostra representativa para análise.
    """)
    
    # ⬇️⬇️⬇️ LINHA CORRIGIDA - ADICIONE key ÚNICA ⬇️⬇️⬇️
    uploaded_file = st.file_uploader("📤 Faça upload do arquivo CSV", type="csv", key="csv_uploader_unique")
    
    if uploaded_file is not None:
        # Mostrar informações do arquivo
        file_size = uploaded_file.size / (1024*1024)
        st.info(f"📁 Arquivo: {uploaded_file.name} | Tamanho: {file_size:.1f} MB")
        
        # Controle de tamanho da amostra
        tamanho_amostra = st.slider(
            "Tamanho da amostra:",
            min_value=10000,
            max_value=100000,
            value=50000,
            help="Número de registros para análise",
            key="slider_amostra_unique"  # ⬅️ Key única para o slider também
        )
        
        # ⬇️⬇️⬇️ Key única para o botão ⬇️⬇️⬇️
        if st.button("🚀 Processar Análise", type="primary", key="processar_btn_unique"):
            with st.spinner(f"Processando {tamanho_amostra:,} registros..."):
                df = processar_amostra_csv(uploaded_file, tamanho_amostra)
            
            if df is not None:
                # Métricas
                st.header("📊 Métricas Principais")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Amostra de Viagens", f"{len(df):,}")
                with col2:
                    valor_medio = df['gmv_success'].mean() if 'gmv_success' in df.columns else 0
                    st.metric("Valor Médio", f"R$ {valor_medio:.2f}")
                with col3:
                    if 'place_destination_departure' in df.columns:
                        destino = df['place_destination_departure'].mode()
                        destino = destino[0] if not destino.empty else "N/A"
                        st.metric("Destino Mais Popular", destino)
                
                # Gráficos
                st.header("📈 Visualizações")
                
                if 'mes_ano' in df.columns and 'gmv_success' in df.columns:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    media_mensal = df.groupby('mes_ano')['gmv_success'].mean()
                    ax.plot(media_mensal.index.astype(str), media_mensal.values, 
                            marker='o', color=click_bus_palette[0], linewidth=2)
                    ax.set_title("Média de Valores por Mês")
                    ax.set_xlabel("Mês/Ano")
                    ax.set_ylabel("Valor Médio (R$)")
                    ax.tick_params(axis='x', rotation=45)
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                
                if 'place_destination_departure' in df.columns:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    top_destinos = df['place_destination_departure'].value_counts().head(10)
                    ax.barh(range(len(top_destinos)), top_destinos.values, color=click_bus_palette[0])
                    ax.set_yticks(range(len(top_destinos)))
                    ax.set_yticklabels(top_destinos.index)
                    ax.set_xlabel("Número de Viagens")
                    ax.set_title("Top 10 Destinos")
                    st.pyplot(fig)
                
                # Dados
                if st.checkbox("Mostrar amostra dos dados", key="checkbox_dados_unique"):
                    st.dataframe(df.head(20))
    else:
        st.info("""
        ## 📋 Como usar:
        
        1. **Prepare seu CSV** com dados de viagens
        2. **Faça upload** do arquivo
        3. **Ajuste** o tamanho da amostra se necessário
        4. **Clique** em "Processar Análise"
        
        ⚠️ **Dados necessários:** 
        - gmv_success (valor)
        - date_purchase e time_purchase (data/hora)
        - place_destination_departure (destino)
        - place_origin_return (retorno)
        """)

if __name__ == "__main__":
    main()
