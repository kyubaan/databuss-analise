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

def carregar_dados_embutidos():
    """Carrega dados de exemplo embutidos no código"""
    try:
        # Dados de exemplo simulados (substitua pelos seus dados reais)
        dados_exemplo = {
            'date_purchase': [
                '2023-05-15', '2023-05-16', '2023-05-17', '2023-05-18', '2023-05-19',
                '2023-06-10', '2023-06-11', '2023-06-12', '2023-06-13', '2023-06-14',
                '2023-07-05', '2023-07-06', '2023-07-07', '2023-07-08', '2023-07-09',
                '2023-08-12', '2023-08-13', '2023-08-14', '2023-08-15', '2023-08-16',
                '2023-09-20', '2023-09-21', '2023-09-22', '2023-09-23', '2023-09-24'
            ],
            'time_purchase': [
                '14:30:00', '09:15:00', '16:45:00', '11:20:00', '18:30:00',
                '08:45:00', '15:20:00', '10:30:00', '17:15:00', '13:40:00',
                '12:15:00', '19:30:00', '09:45:00', '14:20:00', '16:10:00',
                '10:45:00', '15:30:00', '08:20:00', '17:45:00', '12:30:00',
                '11:10:00', '16:50:00', '09:30:00', '14:45:00', '18:20:00'
            ],
            'gmv_success': [
                150.50, 89.90, 210.00, 75.30, 185.75,
                95.25, 120.00, 65.80, 145.90, 110.50,
                130.75, 195.25, 85.40, 155.60, 175.30,
                70.90, 125.45, 55.60, 165.80, 140.25,
                115.75, 180.90, 90.30, 160.45, 200.75
            ],
            'place_destination_departure': [
                'São Paulo - SP', 'Rio de Janeiro - RJ', 'Belo Horizonte - MG',
                'São Paulo - SP', 'Rio de Janeiro - RJ', 'Belo Horizonte - MG',
                'São Paulo - SP', 'Rio de Janeiro - RJ', 'Belo Horizonte - MG',
                'São Paulo - SP', 'Rio de Janeiro - RJ', 'Belo Horizonte - MG',
                'São Paulo - SP', 'Rio de Janeiro - RJ', 'Belo Horizonte - MG',
                'São Paulo - SP', 'Rio de Janeiro - RJ', 'Belo Horizonte - MG',
                'São Paulo - SP', 'Rio de Janeiro - RJ', 'Belo Horizonte - MG',
                'São Paulo - SP', 'Rio de Janeiro - RJ', 'Belo Horizonte - MG', 'São Paulo - SP'
            ],
            'place_origin_return': [
                '0', '1', '0', '1', '0', '1', '0', '1', '0', '1',
                '0', '1', '0', '1', '0', '1', '0', '1', '0', '1',
                '0', '1', '0', '1', '0'
            ],
            'fk_contact': [
                'user001', 'user002', 'user003', 'user004', 'user005',
                'user006', 'user007', 'user008', 'user009', 'user010',
                'user011', 'user012', 'user013', 'user014', 'user015',
                'user016', 'user017', 'user018', 'user019', 'user020',
                'user021', 'user022', 'user023', 'user024', 'user025'
            ]
        }
        
        df = pd.DataFrame(dados_exemplo)
        
        # PRÉ-PROCESSAMENTO
        # Converter data e hora
        df['data_hora'] = pd.to_datetime(
            df['date_purchase'] + ' ' + df['time_purchase'],
            errors='coerce'
        )
        
        # Remover linhas com datas inválidas
        df = df.dropna(subset=['data_hora'])
        
        # Extrair informações temporais
        df['mes_ano'] = df['data_hora'].dt.to_period('M')
        df['ano'] = df['data_hora'].dt.year
        df['mes'] = df['data_hora'].dt.month
        df['dia_semana'] = df['data_hora'].dt.day_name()
        df['hora'] = df['data_hora'].dt.hour
        
        # Processar retornos
        df['tem_retorno'] = df['place_origin_return'] != '0'
        
        st.success(f"✅ Dados de exemplo carregados: {len(df):,} registros")
        
        # Mostrar informações dos dados
        data_min = df['data_hora'].min()
        data_max = df['data_hora'].max()
        st.info(f"📅 Período: {data_min.date()} a {data_max.date()}")
        st.info(f"💰 Valor médio: R$ {df['gmv_success'].mean():.2f}")
        st.info(f"🗺️ Destinos únicos: {df['place_destination_departure'].nunique()}")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados embutidos: {str(e)}")
        return None

def gerar_grafico_media_mensal(df):
    """Gera gráfico de média mensal"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'mes_ano' in df.columns and 'gmv_success' in df.columns:
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
    
    if 'place_destination_departure' in df.columns:
        top_destinos = df['place_destination_departure'].value_counts().head(10)
        
        ax.barh(range(len(top_destinos)), top_destinos.values, color=click_bus_palette[0], alpha=0.8)
        ax.set_yticks(range(len(top_destinos)))
        
        # Truncar nomes muito longos
        labels = [str(d)[:25] + '...' if len(str(d)) > 25 else str(d) for d in top_destinos.index]
        ax.set_yticklabels(labels)
        
        for i, v in enumerate(top_destinos.values):
            ax.text(v + max(top_destinos.values) * 0.01, i, f'{v}', 
                    va='center', fontweight='bold', fontsize=10, color=click_bus_palette[4])
        
        ax.set_title("Top Destinos Mais Comuns", fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel("Número de Viagens", fontsize=12)
        ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    return fig

def gerar_grafico_distribuicao(df):
    """Gera gráfico de distribuição de valores"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'gmv_success' in df.columns:
        ax.hist(df['gmv_success'], bins=15, alpha=0.7, 
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
    
    if 'mes_ano' in df.columns:
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
        st.markdown(f'<div class="metric-card">Destino Mais Popular<br><span style="font-size: 20px; font-weight: bold;">{destino[:15] + "..." if len(destino) > 15 else destino}</span></div>', unsafe_allow_html=True)
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
        st.subheader("📅 Distribuição por Mês")
        viagens_por_mes = df['mes_ano'].value_counts().sort_index()
        st.dataframe(viagens_por_mes, use_container_width=True)
    
    with col2:
        st.subheader("💰 Estatísticas de Valores")
        stats = df['gmv_success'].describe()
        st.dataframe(pd.DataFrame({
            'Estatística': stats.index,
            'Valor (R$)': stats.values.round(2)
        }), use_container_width=True, hide_index=True)
    
    # Dados brutos
    st.markdown("---")
    expander = st.expander("📋 Visualizar Dados Completos")
    with expander:
        st.dataframe(df, use_container_width=True)

def main():
    st.markdown('<h1 class="main-header">🚌 DataBus - Análise de Viagens ClickBus</h1>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="sample-info">'
               f'🎯 <strong>MODO DADOS EMBUTIDOS</strong><br>'
               f'📊 Análise com dados de exemplo integrados - Sem necessidade de upload'
               f'</div>', unsafe_allow_html=True)
    
    # Botão para carregar dados embutidos
    if st.button("🚀 CARREGAR E ANALISAR DADOS", type="primary", use_container_width=True):
        with st.spinner("⏳ Carregando dados de exemplo..."):
            df = carregar_dados_embutidos()
        
        if df is not None:
            mostrar_analise(df)
    else:
        # Instruções
        st.markdown("""
        ## 📋 Como usar esta ferramenta:
        
        1. **🚀 Clique** em "CARREGAR E ANALISAR DADOS"
        2. **📊 Explore** as métricas e gráficos gerados
        3. **📋 Analise** os dados de exemplo
        
        ### 🎯 Dados de Exemplo Incluídos:
        - **25 registros** de viagens simuladas
        - Período de **Maio a Setembro de 2023**
        - Valores entre **R$ 55,60 e R$ 210,00**
        - **3 destinos** principais (São Paulo, Rio de Janeiro, Belo Horizonte)
        - Dados de **retorno** incluídos
        
        ### 📊 Métricas Disponíveis:
        - Média de valores por mês
        - Top destinos mais comuns  
        - Distribuição de valores
        - Proporção de viagens com retorno
        - Sazonalidade temporal
        
        ### 💡 Para usar seus próprios dados:
        Substitua a função `carregar_dados_embutidos()` com seus dados reais
        """)

if __name__ == "__main__":
    main()
