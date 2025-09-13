import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings
import streamlit as st
from datetime import datetime
import os

warnings.filterwarnings('ignore')

# Configuração do estilo dos gráficos
plt.style.use('default')
click_bus_palette = ["#6A0DAD", "#FFD700", "#9B30FF", "#FFDF00", "#4B0082", "#DAA520"]
sns.set_palette(click_bus_palette)

# Configuração da página do Streamlit
st.set_page_config(
    page_title="DataBus - Análise de Viagens",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

class AnaliseDadosViagens:
    def __init__(self, df):  # MODIFICADO: agora recebe DataFrame diretamente
        self.df = df
        self.preprocessar_dados()
    
    def preprocessar_dados(self):
        # Realiza pre-processamento dos dados
        st.info("Pré-processando dados...")
        
        # Converter data e hora (se as colunas existirem)
        if 'date_purchase' in self.df.columns and 'time_purchase' in self.df.columns:
            self.df['data_hora'] = pd.to_datetime(
                self.df['date_purchase'] + ' ' + self.df['time_purchase'],
                errors='coerce'
            )
            
            # Remover linhas com datas inválidas
            self.df = self.df.dropna(subset=['data_hora'])
            
            # Filtro de Dados - último ano
            data_inicio = pd.to_datetime("2023-04-01")
            data_fim = pd.to_datetime("2024-04-01")
            self.df = self.df[(self.df['data_hora'] >= data_inicio) & (self.df['data_hora'] <= data_fim)]
            
            # Extrair mes e ano
            self.df['mes_ano'] = self.df['data_hora'].dt.to_period('M')
        
        # Tratar valores de retorno (se a coluna existir)
        if 'place_origin_return' in self.df.columns:
            self.df['tem_retorno'] = self.df['place_origin_return'] != '0'
        
        st.success("Pré-processamento concluído!")
    
    # ... (mantenha o resto dos métodos como gerar_grafico_media_mensal, etc.) ...

# Interface principal do Streamlit
def main():
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
        margin-bottom: 1rem;
        border-left: 4px solid #6A0DAD;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🚌 DataBus - Análise de Viagens ClickBus</h1>', unsafe_allow_html=True)
    
    # DEBUG: Verificar arquivos na pasta
    st.sidebar.write("📁 Arquivos na pasta:")
    for arquivo in os.listdir("."):
        if any(arquivo.endswith(ext) for ext in ['.csv', '.parquet', '.py']):
            tamanho = os.path.getsize(arquivo) / (1024*1024)
            st.sidebar.write(f"- {arquivo}: {tamanho:.2f} MB")
    
    # Opção 1: Usar Parquet se existir
    if os.path.exists("dados_viagens.parquet"):
        try:
            df = pd.read_parquet("dados_viagens.parquet")
            st.success(f"✅ Dados carregados do Parquet: {len(df):,} registros")
            analise = AnaliseDadosViagens(df)
            
        except Exception as e:
            st.error(f"Erro ao carregar Parquet: {e}")
            return
    
    # Opção 2: Usar CSV se existir
    elif os.path.exists("df_t.csv"):
        try:
            df = pd.read_csv("df_t.csv")
            st.success(f"✅ Dados carregados do CSV: {len(df):,} registros")
            analise = AnaliseDadosViagens(df)
            
        except Exception as e:
            st.error(f"Erro ao carregar CSV: {e}")
            return
    
    # Opção 3: Upload
    else:
        uploaded_file = st.file_uploader("Faça upload do CSV", type="csv")
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.success("✅ Dados carregados do upload!")
                analise = AnaliseDadosViagens(df)
            except Exception as e:
                st.error(f"Erro ao carregar CSV: {e}")
                return
        else:
            st.warning("⚠️ Nenhum arquivo de dados encontrado!")
            return
    
    # ... (resto do seu código com os gráficos) ...

if __name__ == "__main__":
    main()
