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

def processar_amostra_csv(uploaded_file, tamanho_amostra=100000):
    """Processa apenas uma amostra do CSV grande"""
    try:
        # Primeiro: ler apenas as primeiras linhas para descobrir as colunas
        df_primeiras_linhas = pd.read_csv(uploaded_file, nrows=10)
        colunas_importantes = ['gmv_success', 'date_purchase', 'time_purchase', 
                              'place_destination_departure', 'place_origin_return', 'fk_contact']
        
        # Manter apenas colunas que existem no CSV
        colunas_para_ler = [col for col in colunas_importantes if col in df_primeiras_linhas.columns]
        
        # Voltar ao início do arquivo
        uploaded_file.seek(0)
        
        # Se o arquivo for muito grande, usar amostragem
        st.info("📊 Arquivo grande detectado. Processando amostra representativa...")
        
        # Estratégia: Ler amostra aleatória
        try:
            # Calcular número total de linhas de forma eficiente
            total_linhas = sum(1 for line in uploaded_file) - 1  # Subtrair header
            uploaded_file.seek(0)
            
            # Ler amostra aleatória
            skip_rows = np.random.choice(range(1, total_linhas+1), 
                                       size=min(tamanho_amostra, total_linhas), 
                                       replace=False)
            skip_rows = sorted(skip_rows)
            
            df = pd.read_csv(uploaded_file, skiprows=lambda x: x not in [0] + skip_rows.tolist())
            
        except:
            # Se falhar, ler apenas as primeiras N linhas
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, nrows=tamanho_amostra, usecols=colunas_para_ler)
        
        # Pré-processamento
        if 'date_purchase' in df.columns and 'time_purchase' in df.columns:
            df['data_hora'] = pd.to_datetime(
                df['date_purchase'] + ' ' + df['time_purchase'],
                errors='coerce'
            )
            df = df.dropna(subset=['data_hora'])
            
            # Filtrar para último ano
            data_inicio = pd.to_datetime("2023-04-01")
            data_fim = pd.to_datetime("2024-04-01")
            df = df[(df['data_hora'] >= data_inicio) & (df['data_hora'] <= data_fim)]
            
            df['mes_ano'] = df['data_hora'].dt.to_period('M')
        
        if 'place_origin_return' in df.columns:
            df['tem_retorno'] = df['place_origin_return'] != '0'
            
        return df, total_linhas
        
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        return None, 0

def main():
    st.title("🚌 DataBus - Análise de Viagens ClickBus")
    
    # Inicializar session state
    if 'dados_processados' not in st.session_state:
        st.session_state.dados_processados = None
        st.session_state.arquivo_hash = None
        st.session_state.processado = False

    # Seção de upload - sempre visível
    st.markdown("## 📋 Análise de Dados de Viagens")
    st.markdown("**💡 Para arquivos grandes (>200MB):** O sistema usa uma amostra representativa para análise.")
    
    uploaded_file = st.file_uploader("📤 Faça upload do arquivo CSV", type="csv")

    # Se já tem dados processados, mostrar botão de limpar
    if st.session_state.dados_processados is not None:
        if st.button("🗑️ Limpar Dados e Recarregar"):
            st.session_state.dados_processados = None
            st.session_state.arquivo_hash = None
            st.session_state.processado = False
            st.rerun()

    # Processar arquivo se for novo
    if uploaded_file is not None and not st.session_state.processado:
        file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
        
        # Verificar se é um novo arquivo
        if st.session_state.arquivo_hash != file_hash:
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
                    df, total_linhas = processar_amostra_csv(uploaded_file, tamanho_amostra)
                    
                    if df is not None:
                        st.session_state.dados_processados = df
                        st.session_state.arquivo_hash = file_hash
                        st.session_state.processado = True
                        st.session_state.total_linhas = total_linhas
                        st.rerun()

    # Mostrar resultados se já estiver processado
    if st.session_state.dados_processados is not None:
        df = st.session_state.dados_processados
        total_linhas = st.session_state.total_linhas
        
        st.success(f"✅ Amostra processada: {len(df):,} registros (de ~{total_linhas:,} total)")
        
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
        
        # Estatísticas
        with st.expander("📊 Estatísticas da Amostra"):
            st.write(f"- Total de registros na amostra: {len(df):,}")
            if 'data_hora' in df.columns:
                st.write(f"- Período coberto: {df['data_hora'].min().date()} a {df['data_hora'].max().date()}")
            if 'gmv_success' in df.columns:
                st.write(f"- Valor médio: R$ {df['gmv_success'].mean():.2f}")
                st.write(f"- Valor máximo: R$ {df['gmv_success'].max():.2f}")

    else:
        st.info("""
        ## 📋 Instruções:
        
        1. **Faça upload** do arquivo CSV com dados de viagens
        2. **Ajuste** o tamanho da amostra se necessário
        3. **Clique** em "Processar Análise"
        
        ⚠️ **Arquivos muito grandes** serão processados por amostragem
        """)

if __name__ == "__main__":
    main()
