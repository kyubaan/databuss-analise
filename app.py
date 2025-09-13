import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import numpy as np
from datetime import datetime
import hashlib

# Configuração da página
st.set_page_config(page_title="DataBus - Análise de Viagens", page_icon="🚌", layout="wide")

# Configuração de estilo
click_bus_palette = ["#6A0DAD", "#FFD700", "#9B30FF", "#FFDF00", "#4B0082", "#DAA520"]
sns.set_palette(click_bus_palette)
plt.style.use('default')

def main():
    st.title("🚌 DataBus - Análise de Viagens ClickBus")
    
    # Inicializar session state de forma mais robusta
    if 'dados_processados' not in st.session_state:
        st.session_state.dados_processados = None
        st.session_state.arquivo_nome = None
        st.session_state.processado = False

    st.markdown("## 📋 Análise de Dados de Viagens")
    st.markdown("**💡 Para arquivos grandes (>200MB):** O sistema usa uma amostra representativa para análise.")

    # Sempre mostrar o uploader, mas esconder se já tiver dados
    if st.session_state.dados_processados is None:
        uploaded_file = st.file_uploader("📤 Faça upload do arquivo CSV", type="csv")
        
        if uploaded_file is not None:
            file_size = uploaded_file.size / (1024*1024)
            st.info(f"📁 Arquivo: {uploaded_file.name} | Tamanho: {file_size:.1f} MB")
            
            tamanho_amostra = st.slider(
                "Tamanho da amostra (registros):",
                min_value=10000,
                max_value=200000,
                value=50000
            )
            
            if st.button("🚀 Processar Análise", type="primary"):
                with st.spinner(f"Processando amostra de {tamanho_amostra:,} registros..."):
                    try:
                        # Processamento simplificado
                        df = pd.read_csv(uploaded_file, nrows=tamanho_amostra)
                        
                        # Pré-processamento básico
                        if 'date_purchase' in df.columns and 'time_purchase' in df.columns:
                            df['data_hora'] = pd.to_datetime(
                                df['date_purchase'] + ' ' + df['time_purchase'],
                                errors='coerce'
                            )
                            df = df.dropna(subset=['data_hora'])
                            df['mes_ano'] = df['data_hora'].dt.to_period('M')
                        
                        # Salvar no session state
                        st.session_state.dados_processados = df
                        st.session_state.arquivo_nome = uploaded_file.name
                        st.session_state.processado = True
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao processar: {str(e)}")
    else:
        # Já tem dados processados - mostrar resultados
        df = st.session_state.dados_processados
        
        # Botão para recarregar
        if st.button("🔄 Carregar Novo Arquivo"):
            st.session_state.dados_processados = None
            st.session_state.arquivo_nome = None
            st.session_state.processado = False
            st.rerun()
        
        st.success(f"✅ Dados carregados: {len(df):,} registros do arquivo {st.session_state.arquivo_nome}")
        
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
                destino_mais_comum = df['place_destination_departure'].mode()
                destino = destino_mais_comum[0] if not destino_mais_comum.empty else "N/A"
                st.metric("Destino Mais Popular", destino)
        
        # Gráficos
        st.header("📈 Visualizações")
        
        tab1, tab2 = st.tabs(["Média Mensal", "Top Destinos"])
        
        with tab1:
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
        
        with tab2:
            if 'place_destination_departure' in df.columns:
                fig, ax = plt.subplots(figsize=(10, 6))
                top_destinos = df['place_destination_departure'].value_counts().head(10)
                ax.barh(range(len(top_destinos)), top_destinos.values, color=click_bus_palette[0])
                ax.set_yticks(range(len(top_destinos)))
                ax.set_yticklabels(top_destinos.index)
                ax.set_xlabel("Número de Viagens")
                ax.set_title("Top 10 Destinos")
                st.pyplot(fig)

if __name__ == "__main__":
    main()
