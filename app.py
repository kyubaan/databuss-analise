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
    .file-info {
        background-color: #e6f7ff;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #1890ff;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def carregar_csv_completo():
    """Carrega o arquivo CSV completo do repositório"""
    try:
        # Alterado para amostra_pequena.csv
        arquivo_csv = "amostra_pequena.csv"
        
        st.info(f"📁 Tentando carregar: {arquivo_csv}")
        
        # Verifica se o arquivo existe
        if not os.path.exists(arquivo_csv):
            st.warning(f"Arquivo '{arquivo_csv}' não encontrado no diretório.")
            
            # Lista arquivos disponíveis para debug
            st.write("📂 Arquivos no diretório:")
            for f in os.listdir('.'):
                if f.endswith('.csv'):
                    size = os.path.getsize(f) / (1024*1024)
                    st.write(f"- {f}: {size:.1f} MB")
            
            return None
        
        # Carrega o CSV completo
        st.info("⏳ Carregando arquivo CSV...")
        
        # Lê apenas as colunas essenciais para economizar memória
        colunas_essenciais = [
            'gmv_success', 'date_purchase', 'time_purchase',
            'place_destination_departure', 'place_origin_return', 'fk_contact'
        ]
        
        # Primeiro verifica quais colunas existem no arquivo
        colunas_existentes = pd.read_csv(arquivo_csv, nrows=0).columns.tolist()
        colunas_para_ler = [col for col in colunas_essenciais if col in colunas_existentes]
        
        st.write(f"📋 Colunas encontradas: {', '.join(colunas_para_ler)}")
        
        # Lê o arquivo completo com as colunas selecionadas
        df = pd.read_csv(arquivo_csv, usecols=colunas_para_ler)
        
        st.success(f"✅ Arquivo carregado com sucesso! {len(df):,} registros")
        
        # PRÉ-PROCESSAMENTO
        st.info("🔍 Processando dados...")
        
        # 1. Converter data e hora
        if 'date_purchase' in df.columns and 'time_purchase' in df.columns:
            df['data_hora'] = pd.to_datetime(
                df['date_purchase'] + ' ' + df['time_purchase'],
                errors='coerce'
            )
            
            # Remover linhas com datas inválidas
            linhas_antes = len(df)
            df = df.dropna(subset=['data_hora'])
            linhas_apos = len(df)
            
            if linhas_antes != linhas_apos:
                st.write(f"📅 Datas válidas: {linhas_apos:,} de {linhas_antes:,} registros")
            
            # Extrair informações temporais
            df['mes_ano'] = df['data_hora'].dt.to_period('M')
            df['ano'] = df['data_hora'].dt.year
            df['mes'] = df['data_hora'].dt.month
            df['dia_semana'] = df['data_hora'].dt.day_name()
            
            # Filtrar para período mais recente (últimos 12-15 meses)
            if len(df) > 0:
                data_mais_recente = df['data_hora'].max()
                data_inicio = data_mais_recente - pd.DateOffset(months=15)
                df = df[df['data_hora'] >= data_inicio]
                st.write(f"📅 Período analisado: {data_inicio.date()} a {data_mais_recente.date()}")
        
        # 2. Processar valores monetários
        if 'gmv_success' in df.columns:
            # Converter para numérico
            df['gmv_success'] = pd.to_numeric(df['gmv_success'], errors='coerce')
            df = df.dropna(subset=['gmv_success'])
            
            # Estatísticas básicas
            valor_medio = df['gmv_success'].mean()
            valor_max = df['gmv_success'].max()
            valor_min = df['gmv_success'].min()
            
            st.write(f"💰 Valores: Médio R$ {valor_medio:.2f} | Min R$ {valor_min:.2f} | Max R$ {valor_max:.2f}")
        
        # 3. Processar destinos
        if 'place_destination_departure' in df.columns:
            destinos_unicos = df['place_destination_departure'].nunique()
            st.write(f"🗺️ Destinos únicos: {destinos_unicos}")
        
        # 4. Processar retornos
        if 'place_origin_return' in df.columns:
            df['tem_retorno'] = df['place_origin_return'] != '0'
            if 'tem_retorno' in df.columns:
                perc_retorno = (df['tem_retorno'].sum() / len(df)) * 100
                st.write(f"🔄 Viagens com retorno: {perc_retorno:.1f}%")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar arquivo CSV: {str(e)}")
        return None

def gerar_grafico_media_mensal(df):
    """Gera gráfico de média mensal"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'mes_ano' in df.columns and 'gmv_success' in df.columns:
        media_mensal = df.groupby('mes_ano')['gmv_success'].mean()
        
        ax.plot(media_mensal.index.astype(str), media_mensal.values, 
                marker='o', color=click_bus_palette[0], linewidth=3, markersize=6)
        
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
    
    if 'place_destination_departure' in df.columns:
        top_destinos = df['place_destination_departure'].value_counts().head(10)
        
        ax.barh(range(len(top_destinos)), top_destinos.values, color=click_bus_palette[0], alpha=0.8)
        ax.set_yticks(range(len(top_destinos)))
        
        # Truncar nomes muito longos
        labels = [str(d)[:30] + '...' if len(str(d)) > 30 else str(d) for d in top_destinos.index]
        ax.set_yticklabels(labels, fontsize=10)
        
        for i, v in enumerate(top_destinos.values):
            ax.text(v + max(top_destinos.values) * 0.01, i, f'{v:,}', 
                    va='center', fontweight='bold', fontsize=9, color=click_bus_palette[4])
        
        ax.set_title("Top 10 Destinos Mais Comuns", fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel("Número de Viagens", fontsize=12)
        ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    return fig

def gerar_grafico_distribuicao(df):
    """Gera gráfico de distribuição de valores"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'gmv_success' in df.columns:
        # Usar percentis para visualização melhor
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
    
    if 'tem_retorno' in df.columns:
        contagem_retorno = df['tem_retorno'].value_counts()
        
        labels = ['Sem Retorno', 'Com Retorno']
        cores = [click_bus_palette[0], click_bus_palette[1]]
        
        wedges, texts, autotexts = ax.pie(contagem_retorno.values, labels=labels, colors=cores,
                                         autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12})
        
        for text in texts:
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title("Proporção de Viagens com Retorno", fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return fig

def gerar_grafico_sazonalidade(df):
    """Gera gráfico de sazonalidade"""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    if 'mes_ano' in df.columns:
        viagens_por_mes = df.groupby('mes_ano').size()
        
        ax.plot(viagens_por_mes.index.astype(str), viagens_por_mes.values,
               marker='o', color=click_bus_palette[0], linewidth=2, markersize=6)
        
        ax.set_title("Sazonalidade - Número de Viagens por Mês", fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel("Mês/Ano", fontsize=12)
        ax.set_ylabel("Número de Viagens", fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def mostrar_analise(df):
    """Mostra a análise dos dados"""
    st.success(f"✅ **Análise concluída!** {len(df):,} registros processados")
    
    # Métricas principais
    st.markdown("---")
    st.header("📊 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card">Total de Viagens<br><span style="font-size: 24px; font-weight: bold;">{len(df):,}</span></div>', unsafe_allow_html=True)
    with col2:
        valor_medio = df['gmv_success'].mean()
        st.markdown(f'<div class="metric-card">Valor Médio<br><span style="font-size: 24px; font-weight: bold;">R$ {valor_medio:.2f}</span></div>', unsafe_allow_html=True)
    with col3:
        destino = df['place_destination_departure'].mode()[0]
        st.markdown(f'<div class="metric-card">Destino Mais Popular<br><span style="font-size: 18px; font-weight: bold;">{destino[:20] + "..." if len(destino) > 20 else destino}</span></div>', unsafe_allow_html=True)
    with col4:
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
    
    # Análises extras
    st.markdown("---")
    st.header("📋 Análises Detalhadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Viagens por Mês")
        if 'mes_ano' in df.columns:
            viagens_por_mes = df['mes_ano'].value_counts().sort_index()
            st.dataframe(viagens_por_mes, use_container_width=True)
    
    with col2:
        st.subheader("💰 Estatísticas de Valores")
        if 'gmv_success' in df.columns:
            stats = df['gmv_success'].describe()
            st.dataframe(pd.DataFrame({
                'Estatística': stats.index,
                'Valor (R$)': stats.values.round(2)
            }), use_container_width=True, hide_index=True)
    
    # Amostra dos dados
    st.markdown("---")
    expander = st.expander("📋 Visualizar Amostra dos Dados (100 primeiras linhas)")
    with expander:
        st.dataframe(df.head(100), use_container_width=True)

def main():
    st.markdown('<h1 class="main-header">🚌 DataBus - Análise de Viagens ClickBus</h1>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="file-info">'
               f'🎯 <strong>MODO CSV COMPLETO</strong><br>'
               f'📊 Analisando arquivo: amostra_pequena.csv<br>'
               f'📈 Análise com amostra de dados - Sem necessidade de upload'
               f'</div>', unsafe_allow_html=True)
    
    # Adicionar spinner durante o carregamento
    with st.spinner('Carregando dados da amostra pequena...'):
        df = carregar_csv_completo()
    
    if df is not None:
        mostrar_analise(df)
    else:
        st.error("Não foi possível carregar os dados. Verifique se o arquivo 'amostra_pequena.csv' existe no diretório.")

# EXECUTAR A APLICAÇÃO
if __name__ == "__main__":
    main()
