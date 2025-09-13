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
    .sample-info {
        background-color: #f6ffed;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #52c41a;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def processar_amostra_inteligente(uploaded_file):
    """Processa a amostra de forma inteligente para extrair máximo de insights"""
    try:
        # Ler o arquivo completo da amostra
        df = pd.read_csv(uploaded_file)
        
        st.success(f"✅ Amostra carregada: {len(df):,} registros")
        
        # Análise de qualidade dos dados
        st.info("🔍 Analisando qualidade dos dados...")
        
        # Verificar colunas disponíveis
        colunas_disponiveis = df.columns.tolist()
        st.write(f"📋 Colunas encontradas: {', '.join(colunas_disponiveis)}")
        
        # PRÉ-PROCESSAMENTO INTELIGENTE
        
        # 1. Converter data e hora (se as colunas existirem)
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
            df['hora'] = df['data_hora'].dt.hour
            
            # Encontrar período coberto
            data_min = df['data_hora'].min()
            data_max = df['data_hora'].max()
            st.write(f"📅 Período coberto: {data_min.date()} a {data_max.date()}")
        
        # 2. Processar valores monetários
        if 'gmv_success' in df.columns:
            # Converter para numérico e remover outliers extremos
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
            perc_retorno = (df['tem_retorno'].sum() / len(df)) * 100
            st.write(f"🔄 Viagens com retorno: {perc_retorno:.1f}%")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao processar amostra: {str(e)}")
        return None

def gerar_grafico_media_mensal(df):
    """Gera gráfico de média mensal"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'mes_ano' in df.columns and 'gmv_success' in df.columns:
        media_mensal = df.groupby('mes_ano')['gmv_success'].mean()
        
        if len(media_mensal) > 1:  # Só plotar se tiver mais de 1 mês
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
        else:
            ax.text(0.5, 0.5, 'Dados insuficientes para tendência temporal', 
                    ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'Dados insuficientes para o gráfico', 
                ha='center', va='center', transform=ax.transAxes)
    
    plt.tight_layout()
    return fig

def gerar_grafico_destinos(df):
    """Gera gráfico de top destinos"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    if 'place_destination_departure' in df.columns:
        top_destinos = df['place_destination_departure'].value_counts().head(10)
        
        if len(top_destinos) > 0:
            ax.barh(range(len(top_destinos)), top_destinos.values, color=click_bus_palette[0], alpha=0.8)
            ax.set_yticks(range(len(top_destinos)))
            
            # Truncar nomes muito longos
            labels = [str(d)[:25] + '...' if len(str(d)) > 25 else str(d) for d in top_destinos.index]
            ax.set_yticklabels(labels)
            
            for i, v in enumerate(top_destinos.values):
                ax.text(v + max(top_destinos.values) * 0.01, i, f'{v:,}', 
                        va='center', fontweight='bold', fontsize=10, color=click_bus_palette[4])
            
            ax.set_title("Top 10 Destinos Mais Comuns", fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel("Número de Viagens", fontsize=12)
            ax.grid(True, alpha=0.3, axis='x')
        else:
            ax.text(0.5, 0.5, 'Dados insuficientes para destinos', 
                    ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'Dados de destinos não disponíveis', 
                ha='center', va='center', transform=ax.transAxes)
    
    plt.tight_layout()
    return fig

def gerar_grafico_distribuicao(df):
    """Gera gráfico de distribuição de valores"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'gmv_success' in df.columns:
        # Usar percentis para evitar outliers extremos
        Q1 = df['gmv_success'].quantile(0.05)  # 5% para ser menos restritivo
        Q3 = df['gmv_success'].quantile(0.95)  # 95% para ser menos restritivo
        df_filtrado = df[(df['gmv_success'] >= Q1) & (df['gmv_success'] <= Q3)]
        
        if len(df_filtrado) > 0:
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
        else:
            ax.text(0.5, 0.5, 'Dados insuficientes após filtro', 
                    ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'Dados de valores não disponíveis', 
                ha='center', va='center', transform=ax.transAxes)
    
    plt.tight_layout()
    return fig

def gerar_grafico_retorno(df):
    """Gera gráfico de proporção de retorno"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    if 'tem_retorno' in df.columns:
        contagem_retorno = df['tem_retorno'].value_counts()
        
        if len(contagem_retorno) >= 2:
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
        else:
            ax.text(0.5, 0.5, 'Dados insuficientes para retorno', 
                    ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'Dados de retorno não disponíveis', 
                ha='center', va='center', transform=ax.transAxes)
    
    plt.tight_layout()
    return fig

def gerar_grafico_sazonalidade(df):
    """Gera gráfico de sazonalidade"""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    if 'mes_ano' in df.columns:
        viagens_por_mes = df.groupby('mes_ano').size()
        
        if len(viagens_por_mes) > 1:
            ax.plot(viagens_por_mes.index.astype(str), viagens_por_mes.values,
                   marker='o', color=click_bus_palette[0], linewidth=3, markersize=8)
            
            ax.set_title("Sazonalidade - Número de Viagens por Mês", fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel("Mês/Ano", fontsize=12)
            ax.set_ylabel("Número de Viagens", fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'Dados insuficientes para sazonalidade', 
                    ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'Dados temporais não disponíveis', 
                ha='center', va='center', transform=ax.transAxes)
    
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
        if 'gmv_success' in df.columns:
            valor_medio = df['gmv_success'].mean()
            st.markdown(f'<div class="metric-card">Valor Médio<br><span style="font-size: 24px; font-weight: bold;">R$ {valor_medio:.2f}</span></div>', unsafe_allow_html=True)
    with col3:
        if 'place_destination_departure' in df.columns:
            destino = df['place_destination_departure'].mode()
            destino_texto = destino[0] if not destino.empty else "N/A"
            st.markdown(f'<div class="metric-card">Destino Mais Popular<br><span style="font-size: 20px; font-weight: bold;">{destino_texto[:15] + "..." if len(destino_texto) > 15 else destino_texto}</span></div>', unsafe_allow_html=True)
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
    
    # Análises extras
    st.markdown("---")
    st.header("📋 Análises Detalhadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Distribuição por Mês")
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
    
    # Dados brutos
    st.markdown("---")
    expander = st.expander("📋 Visualizar Dados da Amostra (100 primeiras linhas)")
    with expander:
        st.dataframe(df.head(100), use_container_width=True)

def main():
    st.markdown('<h1 class="main-header">🚌 DataBus - Análise de Viagens ClickBus</h1>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="sample-info">'
               f'🎯 <strong>MODO AMOSTRA INTELIGENTE</strong><br>'
               f'📊 Otimizado para extrair máximo insights de amostras menores'
               f'</div>', unsafe_allow_html=True)
    
    # Upload do arquivo
    uploaded_file = st.file_uploader(
        "📤 Faça upload da amostra_pequena.csv", 
        type="csv", 
        key="csv_uploader_unique",
        help="Faça upload do arquivo de amostra para análise detalhada"
    )
    
    if uploaded_file is not None:
        # Informações do arquivo
        file_size = uploaded_file.size / (1024*1024)
        st.info(f"📁 **Arquivo:** {uploaded_file.name} | **Tamanho:** {file_size:.1f} MB")
        
        if st.button("🚀 ANALISAR AMOSTRA", type="primary", use_container_width=True):
            with st.spinner("⏳ Processando amostra de forma inteligente..."):
                df = processar_amostra_inteligente(uploaded_file)
            
            if df is not None:
                mostrar_analise(df)
    else:
        # Instruções
        st.markdown("""
        ## 📋 Como usar esta ferramenta:
        
        1. **📤 Faça upload** do arquivo `amostra_pequena.csv`
        2. **🚀 Clique** em "ANALISAR AMOSTRA"
        3. **📊 Explore** as métricas e gráficos gerados
        
        ### 🎯 Análise Inteligente:
        - **Processamento otimizado** para amostras menores
        - **Detecção automática** de colunas disponíveis
        - **Visualizações adaptativas** baseadas nos dados
        
        ### ⚠️ Dados esperados:
        - `gmv_success` - Valor da passagem
        - `date_purchase` - Data da compra
        - `time_purchase` - Hora da compra  
        - `place_destination_departure` - Destino
        - `place_origin_return` - Informações de retorno
        
        ### 💡 Dica:
        Mesmo com amostra reduzida, o sistema extrairá o máximo de insights possível!
        """)

if __name__ == "__main__":
    main()
