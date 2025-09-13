import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import numpy as np
from datetime import datetime
import os
import tempfile

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
    .uploaded-file {
        background-color: #e6f7ff;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #1890ff;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Função para salvar arquivo temporariamente
def salvar_arquivo_temp(uploaded_file):
    """Salva o arquivo uploadado em temp e retorna o caminho"""
    try:
        # Criar diretório temp se não existir
        os.makedirs("temp_uploads", exist_ok=True)
        
        # Gerar nome único para o arquivo
        temp_path = f"temp_uploads/{uploaded_file.name}"
        
        # Salvar arquivo
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        return temp_path
    except Exception as e:
        st.error(f"Erro ao salvar arquivo: {e}")
        return None

# Função para verificar arquivos temp existentes
def verificar_arquivos_temp():
    """Verifica se existem arquivos temporários salvos"""
    try:
        if os.path.exists("temp_uploads"):
            arquivos = os.listdir("temp_uploads")
            if arquivos:
                return arquivos[0]  # Retorna o primeiro arquivo encontrado
    except:
        pass
    return None

# Função para carregar arquivo salvo
def carregar_arquivo_salvo(nome_arquivo):
    """Carrega um arquivo previamente salvo"""
    try:
        caminho = f"temp_uploads/{nome_arquivo}"
        if os.path.exists(caminho):
            return open(caminho, "rb")
    except:
        pass
    return None

# Função para limpar arquivos temp
def limpar_arquivos_temp():
    """Limpa arquivos temporários"""
    try:
        if os.path.exists("temp_uploads"):
            for arquivo in os.listdir("temp_uploads"):
                os.remove(f"temp_uploads/{arquivo}")
    except:
        pass

@st.cache_data
def processar_amostra_csv(_file_object, tamanho_amostra=50000):
    """Processa uma amostra do CSV grande"""
    try:
        # Ler apenas as colunas essenciais
        colunas_essenciais = [
            'gmv_success', 'date_purchase', 'time_purchase',
            'place_destination_departure', 'place_origin_return', 'fk_contact'
        ]
        
        # Verificar quais colunas existem no arquivo
        _file_object.seek(0)
        primeira_linha = pd.read_csv(_file_object, nrows=0)
        _file_object.seek(0)
        
        colunas_para_ler = [col for col in colunas_essenciais if col in primeira_linha.columns]
        
        # Ler amostra
        df = pd.read_csv(_file_object, usecols=colunas_para_ler, nrows=tamanho_amostra)
        
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

# ... (AS FUNÇÕES DE GRÁFICOS PERMANECEM IGUAIS) ...

def main():
    st.markdown('<h1 class="main-header">🚌 DataBus - Análise de Viagens ClickBus</h1>', unsafe_allow_html=True)
    
    # Verificar se já existe arquivo salvo
    arquivo_salvo = verificar_arquivos_temp()
    arquivo_carregado = None
    
    # Se já existe arquivo salvo, mostrar opção para usar
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
    
    # Upload do arquivo (sempre disponível)
    uploaded_file = st.file_uploader(
        "📤 Ou faça upload de um novo arquivo CSV", 
        type="csv", 
        key="csv_uploader_unique"
    )
    
    # Determinar qual arquivo usar
    arquivo_para_usar = arquivo_carregado if arquivo_carregado else uploaded_file
    
    if arquivo_para_usar:
        # Se é um novo upload, salvar temporariamente
        if uploaded_file and not arquivo_carregado:
            temp_path = salvar_arquivo_temp(uploaded_file)
            if temp_path:
                st.success("💾 Arquivo salvo para sessões futuras!")
                st.rerun()
        
        # Informações do arquivo
        file_size = len(arquivo_para_usar.getvalue()) / (1024*1024) if hasattr(arquivo_para_usar, 'getvalue') else os.path.getsize(arquivo_para_usar.name)
        st.info(f"📁 **Arquivo:** {arquivo_para_usar.name} | **Tamanho:** {file_size:.1f} MB")
        
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
                df = processar_amostra_csv(arquivo_para_usar, tamanho_amostra)
            
            if df is not None:
                st.success(f"✅ **Amostra processada com sucesso!** {len(df):,} registros")
                
                # ... (O RESTO DO CÓDIGO DE MÉTRICAS E GRÁFICOS PERMANECE IGUAL) ...
                
    else:
        # Instruções quando não há arquivo
        st.markdown("""
        ## 📋 Como usar esta ferramenta:
        
        1. **📤 Faça upload** de um arquivo CSV com dados de viagens
        2. **🎚️ Ajuste** o tamanho da amostra conforme necessário
        3. **🚀 Clique** em "Processar Análise"
        4. **📊 Explore** as métricas e gráficos gerados
        
        ### 💡 Vantagens:
        - **Arquivo salvo** entre refreshes de página
        - **Não precisa** reupload a cada atualização
        - **Dados preservados** durante sua sessão
        
        ### ⚠️ Dados necessários no CSV:
        - `gmv_success` - Valor da passagem
        - `date_purchase` - Data da compra  
        - `time_purchase` - Hora da compra
        - `place_destination_departure` - Destino
        - `place_origin_return` - Informações de retorno
        """)

if __name__ == "__main__":
    main()
