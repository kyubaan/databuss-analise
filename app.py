import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import numpy as np
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="DataBus - Análise de Viagens", 
    page_icon="🚌", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração de estilo
click_bus_palette = ["#6A0DAD", "#FFD700", "#9B30FF", "#FFDF00", "#4B0082", "#DAA520"]
sns.set_palette(click_bus_palette)
plt.style.use('default')

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #6A0DAD;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #6A0DAD;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #F0F2F6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6A0DAD;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    """Carrega os dados do arquivo CSV no repositório"""
    try:
        # Tenta carregar o arquivo do diretório (que está no GitHub)
        df = pd.read_csv("dados.csv")
        
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
            df['mes'] = df['data_hora'].dt.month
            df['dia_semana'] = df['data_hora'].dt.day_name()
        
        if 'place_origin_return' in df.columns:
            df['tem_retorno'] = df['place_origin_return'] != '0'
            
        return df
        
    except FileNotFoundError:
        st.warning("Arquivo 'dados.csv' não encontrado no diretório.")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao processar: {str(e)}")
        return None

@st.cache_data
def processar_amostra_csv(uploaded_file, tamanho_amostra=50000):
    """Processa uma amostra do CSV grande (para fallback)"""
    try:
        # Ler apenas as colunas essenciais
        colunas_essenciais = [
            'gmv_success', 'date_purchase', 'time_purchase',
            'place_destination_departure', 'place_origin_return', 'fk_contact'
        ]
        
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
            
            # Filtrar para último ano
            data_inicio = pd.to_datetime("2023-04-01")
            data_fim = pd.to_datetime("2024-04-01")
            df = df[(df['data_hora'] >= data_inicio) & (df['data_hora'] <= data_fim)]
            
            df['mes_ano'] = df['data_hora'].dt.to_period('M')
            df['mes'] = df['data_hora'].dt.month
            df['dia_semana'] = df['data_hora'].dt.day_name()
        
        if 'place_origin_return' in df.columns:
            df['tem_retorno'] = df['place_origin_return'] != '0'
            
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao processar: {str(e)}")
        return None

def gerar_grafico_media_mensal(df):
    """Gera gráfico de média mensal"""
    fig, ax = plt.subplots(figsize=(12, 6))
    media_mensal = df.groupby('mes_ano')['gmv_success'].mean()
    ax.plot(media_mensal.index.astype(str), media_mensal.values, 
            marker='o', color=click_bus_palette[0], linewidth=3, markersize=8)
    
    media_geral = df['gmv_success'].mean()
    ax.axhline(y=media_geral, color=click_bus_palette[1], linestyle='--', 
              linewidth=2, label=f'Média Geral: R$ {media_geral:.2f}')
    
    ax.set_title("Média de Valores por Mês", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Mês/Ano", fontsize=12)
    ax.set_ylabel("Valor Médio (R$)", fontsize=12)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    return fig

def gerar_grafico_destinos(df):
    """Gera gráfico de top destinos"""
    fig, ax = plt.subplots(figsize=(12, 8))
    top_destinos = df['place_destination_departure'].value_counts().head(10)
    
    ax.barh(range(len(top_destinos)), top_destinos.values, color=click_bus_palette[0], alpha=0.8)
    ax.set_yticks(range(len(top_destinos)))
    ax.set_yticklabels([str(d)[:20] + '...' if len(str(d)) > 20 else str(d) for d in top_destinos.index])
    
    for i, v in enumerate(top_destinos.values):
        ax.text(v + max(top_destinos.values) * 0.01, i, f'{v:,}', 
                va='center', fontweight='bold', fontsize=10, color=click_bus_palette[4])
    
    ax.set_title("Top 10 Destinos Mais Comuns", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Número de Viagens", fontsize=12)
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    return fig

def gerar_grafico_distribuicao(df):
    """Gera gráfico de distribuição de valores"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Filtrar valores extremos para melhor visualização
    Q1 = df['gmv_success'].quantile(0.01)
    Q3 = df['gmv_success'].quantile(0.99)
    df_filtrado = df[(df['gmv_success'] >= Q1) & (df['gmv_success'] <= Q3)]
    
    ax.hist(df_filtrado['gmv_success'], bins=30, alpha=0.7, 
           color=click_bus_palette[0], edgecolor='white')
    
    media = df['gmv_success'].mean()
    mediana = df['gmv_success'].median()
    ax.axvline(media, color=click_bus_palette[1], linestyle='--', linewidth=2,
              label=f'Média: R$ {media:.2f}')
    ax.axvline(mediana, color=click_bus_palette[2], linestyle='--', linewidth=2,
              label=f'Mediana: R$ {mediana:.2f}')
    
    ax.set_title("Distribuição de Valores das Passagens", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Valor (R$)", fontsize=12)
    ax.set_ylabel("Frequência", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    return fig

def gerar_grafico_retorno(df):
    """Gera gráfico de proporção de retorno"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    contagem_retorno = df['tem_retorno'].value_counts()
    labels = ['Sem Retorno', 'Com Retorno']
    cores = [click_bus_palette[0], click_bus_palette[1]]
    
    wedges, texts, autotexts = ax.pie(contagem_retorno.values, labels=labels, colors=cores,
                                     autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12})
    
    for text in texts:
        text.set_fontweight('bold')
        text.set_fontsize(12)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(12)
    
    ax.set_title("Proporção de Viagens com Retorno", fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    return fig

def gerar_grafico_sazonalidade(df):
    """Gera gráfico de sazonalidade"""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    viagens_por_mes = df.groupby('mes_ano').size()
    ax.plot(viagens_por_mes.index.astype(str), viagens_por_mes.values,
           marker='o', color=click_bus_palette[0], linewidth=3, markersize=8)
    
    ax.set_title("Sazonalidade - Número de Viagens por Mês", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Mês/Ano", fontsize=12)
    ax.set_ylabel("Número de Viagens", fontsize=12)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig

def mostrar_analise(df):
    """Mostra a análise dos dados"""
    st.success(f"✅ **Dados carregados com sucesso!** {len(df):,} registros")
    
    # Métricas principais
    st.markdown("---")
    st.header("📊 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card">Total de Viagens<br><span style="font-size: 24px; font-weight: bold;">{len(df):,}</span></div>', unsafe_allow_html=True)
    with col2:
        valor_medio = df['gmv_success'].mean() if 'gmv_success' in df.columns else 0
        st.markdown(f'<div class="metric-card">Valor Médio<br><span style="font-size: 24px; font-weight: bold;">R$ {valor_medio:.2f}</span></div>', unsafe_allow_html=True)
    with col3:
        if 'place_destination_departure' in df.columns:
            destino = df['place_destination_departure'].mode()
            destino_texto = destino[0] if not destino.empty else "N/A"
            if len(destino_texto) > 15:
                destino_texto = destino_texto[:15] + "..."
            st.markdown(f'<div class="metric-card">Destino Mais Popular<br><span style="font-size: 20px; font-weight: bold;">{destino_texto}</span></div>', unsafe_allow_html=True)
    with col4:
        if 'tem_retorno' in df.columns:
            perc_retorno = (df['tem_retorno'].sum() / len(df)) * 100
            st.markdown(f'<div class="metric-card">Viagens c/ Retorno<br><span style="font-size: 24px; font-weight: bold;">{perc_retorno:.1f}%</span></div>', unsafe_allow_html=True)
    
    # Gráficos
    st.markdown("---")
    st.header("📈 Visualizações")
    
    # Abas para os gráficos
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📅 Média Mensal", "🗺️ Top Destinos", "📊 Distribuição Valores", 
        "🔄 Viagens c/ Retorno", "📈 Sazonalidade"
    ])
    
    with tab1:
        st.pyplot(gerar_grafico_media_mensal(df))
    
    with tab2:
        st.pyplot(gerar_grafico_destinos(df))
    
    with tab3:
        st.pyplot(gerar_grafico_distribuicao(df))
    
    with tab4:
        st.pyplot(gerar_grafico_retorno(df))
    
    with tab5:
        st.pyplot(gerar_grafico_sazonalidade(df))
    
    # Dados brutos
    st.markdown("---")
    expander = st.expander("📋 Visualizar Dados da Amostra (100 primeiras linhas)")
    with expander:
        st.dataframe(df.head(100), use_container_width=True)
    
    # Download da amostra processada
    st.markdown("---")
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download da Amostra Processada (CSV)",
        data=csv,
        file_name="amostra_processada.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_btn_unique"
    )

def main():
    st.markdown('<h1 class="main-header">🚌 DataBus - Análise de Viagens ClickBus</h1>', unsafe_allow_html=True)
    
    # Tenta carregar os dados do arquivo no repositório primeiro
    df = carregar_dados()
    
    if df is not None:
        mostrar_analise(df)
    else:
        # Fallback: se não encontrar o arquivo, permite upload
        st.info("""
        ### 📁 Arquivo 'dados.csv' não encontrado
        Para usar o app sem necessidade de upload, adicione um arquivo chamado **dados.csv** na raiz do seu repositório do GitHub.
        
        Como alternativa, você pode fazer upload de um arquivo para análise:
        """)
        
        # Upload do arquivo (fallback)
        uploaded_file = st.file_uploader(
            "📤 Faça upload do arquivo CSV com dados de viagens", 
            type="csv", 
            key="csv_uploader_unique"
        )
        
        if uploaded_file is not None:
            # Informações do arquivo
            file_size = uploaded_file.size / (1024*1024)
            st.info(f"📁 **Arquivo:** {uploaded_file.name} | **Tamanho:** {file_size:.1f} MB")
            
            # Controles
            col1, col2 = st.columns([2, 1])
            with col1:
                tamanho_amostra = st.slider(
                    "**Tamanho da amostra para análise:**",
                    min_value=10000,
                    max_value=150000,
                    value=50000,
                    help="Número de registros que serão processados",
                    key="slider_amostra_unique"
                )
            with col2:
                st.write("")
                st.write("")
                processar = st.button(
                    "🚀 **Processar Análise**", 
                    type="primary", 
                    use_container_width=True,
                    key="processar_btn_unique"
                )
            
            if processar:
                with st.spinner(f"⏳ Processando {tamanho_amostra:,} registros..."):
                    df_uploaded = processar_amostra_csv(uploaded_file, tamanho_amostra)
                
                if df_uploaded is not None:
                    mostrar_analise(df_uploaded)
    
    # Instruções quando não há dados
    if df is None and 'uploaded_file' not in locals():
        st
