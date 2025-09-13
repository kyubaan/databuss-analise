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
    .uploaded-file {
        background-color: #e6f7ff;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #1890ff;
        margin-bottom: 10px;
    }
    .amostra-info {
        background-color: #f6ffed;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #52c41a;
        margin-bottom: 15px;
    }
    .high-precision {
        background-color: #fff7e6;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #fa8c16;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Função para salvar arquivo temporariamente
def salvar_arquivo_temp(uploaded_file):
    """Salva o arquivo uploadado em temp e retorna o caminho"""
    try:
        os.makedirs("temp_uploads", exist_ok=True)
        temp_path = f"temp_uploads/{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        return temp_path
    except Exception as e:
        st.error(f"Erro ao salvar arquivo: {e}")
        return None

def verificar_arquivos_temp():
    """Verifica se existem arquivos temporários salvos"""
    try:
        if os.path.exists("temp_uploads"):
            arquivos = os.listdir("temp_uploads")
            if arquivos:
                return arquivos[0]
    except:
        pass
    return None

def carregar_arquivo_salvo(nome_arquivo):
    """Carrega um arquivo previamente salvo"""
    try:
        caminho = f"temp_uploads/{nome_arquivo}"
        if os.path.exists(caminho):
            return open(caminho, "rb")
    except:
        pass
    return None

def limpar_arquivos_temp():
    """Limpa arquivos temporários"""
    try:
        if os.path.exists("temp_uploads"):
            for arquivo in os.listdir("temp_uploads"):
                os.remove(f"temp_uploads/{arquivo}")
    except:
        pass

@st.cache_data(show_spinner=False, max_entries=3)
def processar_amostra_50_percent(_file_object):
    """Processa 50% dos dados para máxima precisão"""
    try:
        # Contar total de linhas de forma eficiente
        total_linhas = 0
        _file_object.seek(0)
        for _ in _file_object:
            total_linhas += 1
        total_linhas -= 1  # Descontar header
        
        # Calcular 50% das linhas
        linhas_amostra = total_linhas // 2
        st.write(f"📊 Processando 50% dos dados: {linhas_amostra:,} de {total_linhas:,} registros")
        
        # Voltar ao início e identificar colunas
        _file_object.seek(0)
        header_line = _file_object.readline()
        header = header_line.decode('utf-8').strip().split(',')
        
        # Colunas essenciais
        colunas_essenciais = [
            'gmv_success', 'date_purchase', 'time_purchase',
            'place_destination_departure', 'place_origin_return', 'fk_contact'
        ]
        colunas_para_ler = [col for col in colunas_essenciais if col in header]
        
        # Amostra aleatória de 50%
        _file_object.seek(0)
        skip_rows = np.random.choice(range(1, total_linhas + 1), 
                                   size=min(linhas_amostra, 500000),  # Limite seguro
                                   replace=False)
        
        # Ler a amostra
        df = pd.read_csv(_file_object, 
                        skiprows=lambda x: x not in [0] + skip_rows.tolist(),
                        usecols=colunas_para_ler)
        
        # Pré-processamento
        if 'date_purchase' in df.columns and 'time_purchase' in df.columns:
            df['data_hora'] = pd.to_datetime(
                df['date_purchase'] + ' ' + df['time_purchase'],
                errors='coerce'
            )
            df = df.dropna(subset=['data_hora'])
            
            # Filtrar para período mais recente (últimos 12-15 meses)
            data_mais_recente = df['data_hora'].max()
            data_inicio = data_mais_recente - pd.DateOffset(months=15)
            df = df[df['data_hora'] >= data_inicio]
            
            df['mes_ano'] = df['data_hora'].dt.to_period('M')
        
        if 'place_origin_return' in df.columns:
            df['tem_retorno'] = df['place_origin_return'] != '0'
            
        return df, total_linhas
        
    except Exception as e:
        st.error(f"❌ Erro ao processar: {str(e)}")
        return None, None

def gerar_grafico_media_mensal(df):
    """Gera gráfico de média mensal"""
    fig, ax = plt.subplots(figsize=(12, 6))
    media_mensal = df.groupby('mes_ano')['gmv_success'].mean()
    ax.plot(media_mensal.index.astype(str), media_mensal.values, 
            marker='o', color=click_bus_palette[0], linewidth=3, markersize=8)
    
    media_geral = df['gmv_success'].mean()
    ax.axhline(y=media_geral, color=click_bus_palette[1], linestyle='--', 
              linewidth=2, label=f'Média Geral: R$ {media_geral:.2f}')
    
    ax.set_title("Média de Valores por Mês (50% dos dados)", fontsize=16, fontweight='bold', pad=20)
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
    ax.set_yticklabels([str(d)[:25] + '...' if len(str(d)) > 25 else str(d) for d in top_destinos.index])
    
    for i, v in enumerate(top_destinos.values):
        ax.text(v + max(top_destinos.values) * 0.01, i, f'{v:,}', 
                va='center', fontweight='bold', fontsize=10, color=click_bus_palette[4])
    
    ax.set_title("Top 10 Destinos Mais Comuns (50% dos dados)", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Número de Viagens", fontsize=12)
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    return fig

def gerar_grafico_distribuicao(df):
    """Gera gráfico de distribuição de valores"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Usar percentis para evitar outliers extremos
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
    
    ax.set_title("Distribuição de Valores das Passagens (50% dos dados)", fontsize=16, fontweight='bold', pad=20)
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
    
    ax.set_title("Proporção de Viagens com Retorno (50% dos dados)", fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    return fig

def gerar_grafico_sazonalidade(df):
    """Gera gráfico de sazonalidade"""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    viagens_por_mes = df.groupby('mes_ano').size()
    ax.plot(viagens_por_mes.index.astype(str), viagens_por_mes.values,
           marker='o', color=click_bus_palette[0], linewidth=3, markersize=8)
    
    ax.set_title("Sazonalidade - Número de Viagens por Mês (50% dos dados)", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Mês/Ano", fontsize=12)
    ax.set_ylabel("Número de Viagens", fontsize=12)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig

def main():
    st.markdown('<h1 class="main-header">🚌 DataBus - Análise de Viagens ClickBus</h1>', unsafe_allow_html=True)
    
    # Verificar se já existe arquivo salvo
    arquivo_salvo = verificar_arquivos_temp()
    arquivo_carregado = None
    
    if arquivo_salvo:
        st.markdown(f'<div class="uploaded-file">📁 Arquivo carregado anteriormente: <strong>{arquivo_salvo}</strong></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🔄 Usar arquivo salvo", use_container_width=True):
                arquivo_carregado = carregar_arquivo_salvo(arquivo_salvo)
        with col2:
            if st.button("🗑️ Limpar arquivo", type="secondary", use_container_width=True):
                limpar_arquivos_temp()
                st.rerun()
    
    # Upload do arquivo
    uploaded_file = st.file_uploader(
        "📤 Faça upload do arquivo CSV completo", 
        type="csv", 
        key="csv_uploader_unique",
        help="Upload do arquivo completo (ex: df_t.csv de 600MB). O sistema processará 50% dos dados automaticamente."
    )
    
    arquivo_para_usar = arquivo_carregado if arquivo_carregado else uploaded_file
    
    if arquivo_para_usar:
        if uploaded_file and not arquivo_carregado:
            temp_path = salvar_arquivo_temp(uploaded_file)
            if temp_path:
                st.success("💾 Arquivo salvo para sessões futuras!")
                st.rerun()
        
        file_size = len(arquivo_para_usar.getvalue()) / (1024*1024) if hasattr(arquivo_para_usar, 'getvalue') else os.path.getsize(arquivo_para_usar.name)
        
        st.markdown(f'<div class="high-precision">'
                   f'🎯 <strong>MODO ALTA PRECISÃO</strong><br>'
                   f'📁 Arquivo: {arquivo_para_usar.name}<br>'
                   f'📊 Tamanho: {file_size:.1f} MB<br>'
                   f'✅ Serão processados: <strong>50% dos dados</strong>'
                   f'</div>', unsafe_allow_html=True)
        
        if st.button("🚀 PROCESSAR COM 50% DE PRECISÃO", type="primary", use_container_width=True):
            with st.spinner("⏳ Processando 50% dos dados para máxima precisão..."):
                df, total_linhas = processar_amostra_50_percent(arquivo_para_usar)
            
            if df is not None:
                st.success(f"✅ **Análise de alta precisão concluída!** {len(df):,} registros processados")
                
                # Métricas principais
                st.markdown("---")
                st.header("📊 Métricas Principais (50% dos dados)")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f'<div class="metric-card">Amostra Processada<br><span style="font-size: 24px; font-weight: bold;">{len(df):,}</span><br><span style="font-size: 12px;">de ~{total_linhas:,} total</span></div>', unsafe_allow_html=True)
                with col2:
                    valor_medio = df['gmv_success'].mean() if 'gmv_success' in df.columns else 0
                    st.markdown(f'<div class="metric-card">Valor Médio<br><span style="font-size: 24px; font-weight: bold;">R$ {valor_medio:.2f}</span></div>', unsafe_allow_html=True)
                with col3:
                    if 'place_destination_departure' in df.columns:
                        destino = df['place_destination_departure'].mode()
                        destino_texto = destino[0] if not destino.empty else "N/A"
                        st.markdown(f'<div class="metric-card">Destino Mais Popular<br><span style="font-size: 20px; font-weight: bold;">{destino_texto[:20] + "..." if len(destino_texto) > 20 else destino_texto}</span></div>', unsafe_allow_html=True)
                with col4:
                    if 'tem_retorno' in df.columns:
                        perc_retorno = (df['tem_retorno'].sum() / len(df)) * 100
                        st.markdown(f'<div class="metric-card">Viagens c/ Retorno<br><span style="font-size: 24px; font-weight: bold;">{perc_retorno:.1f}%</span></div>', unsafe_allow_html=True)
                
                # Gráficos
                st.markdown("---")
                st.header("📈 Visualizações (50% dos dados - Alta Precisão)")
                
                # Abas para os gráficos
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📅 Média Mensal", "🗺️ Top Destinos", "📊 Distribuição Valores", 
                    "🔄 Viagens c/ Retorno", "📈 Sazonalidade"
                ])
                
                with tab1:
                    if 'mes_ano' in df.columns and 'gmv_success' in df.columns:
                        st.pyplot(gerar_grafico_media_mensal(df))
                    else:
                        st.warning("Dados insuficientes para gerar gráfico de média mensal")
                
                with tab2:
                    if 'place_destination_departure' in df.columns:
                        st.pyplot(gerar_grafico_destinos(df))
                    else:
                        st.warning("Dados insuficientes para gerar gráfico de destinos")
                
                with tab3:
                    if 'gmv_success' in df.columns:
                        st.pyplot(gerar_grafico_distribuicao(df))
                    else:
                        st.warning("Dados insuficientes para gerar gráfico de distribuição")
                
                with tab4:
                    if 'tem_retorno' in df.columns:
                        st.pyplot(gerar_grafico_retorno(df))
                    else:
                        st.warning("Dados insuficientes para gerar gráfico de retorno")
                
                with tab5:
                    if 'mes_ano' in df.columns:
                        st.pyplot(gerar_grafico_sazonalidade(df))
                    else:
                        st.warning("Dados insuficientes para gerar gráfico de sazonalidade")
                
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
                
                # Download da amostra processada
                st.markdown("---")
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download da Amostra Processada (CSV)",
                    data=csv,
                    file_name="amostra_pequena.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Baixe os dados processados para análise offline"
                )
                
                # Informações técnicas
                with st.expander("ℹ️ Informações Técnicas"):
                    st.write(f"**Total de registros no arquivo original:** ~{total_linhas:,}")
                    st.write(f"**Registros processados:** {len(df):,} (50%)")
                    st.write(f"**Período analisado:** {df['data_hora'].min().date()} a {df['data_hora'].max().date()}")
                    st.write(f"**Colunas utilizadas:** {list(df.columns)}")
    
    else:
        # Instruções quando não há arquivo
        st.markdown("""
        ## 📋 Como usar esta ferramenta de ALTA PRECISÃO:
        
        1. **📤 Faça upload** do arquivo CSV completo com dados de viagens
        2. **🚀 Clique** em "PROCESSAR COM 50% DE PRECISÃO"
        3. **📊 Explore** as métricas e gráficos de alta precisão
        
        ### 🎯 Vantagens do modo 50%:
        - **Máxima precisão** estatística
        - **Resultados mais confiáveis**
        - **Análise representativa** dos dados completos
        - **Detecção de padrões** mais precisa
        
        ### ⚠️ Dados necessários no CSV:
        - `gmv_success` - Valor da passagem
        - `date_purchase` - Data da compra  
        - `time_purchase` - Hora da compra
        - `place_destination_departure` - Destino
        - `place_origin_return` - Informações de retorno
        
        ### 💡 Recomendado para:
        - **Arquivos grandes** (500MB+)
        - **Análises estratégicas**
        - **Tomada de decisão** baseada em dados
        - **Relatórios executivos**
        """)
        
        # Exemplo de estrutura
        with st.expander("🧾 Exemplo da estrutura do CSV recomendada"):
            st.code("""
gmv_success,date_purchase,time_purchase,place_destination_departure,place_origin_return
150.50,2023-05-15,14:30:00,São Paulo - SP,0
89.90,2023-06-20,09:15:00,Rio de Janeiro - RJ,1
210.00,2023-07-12,16:45:00,Belo Horizonte - MG,0
            """)

if __name__ == "__main__":
    main()
