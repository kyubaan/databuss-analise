import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings
import streamlit as st
from datetime import datetime
import os

warnings.filterwarnings('ignore')

# Configuração do estilo dos gráficos com cores amarelo e roxo da Click Bus
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
    def __init__(self, arquivo_parquet):
        self.df = self.carregar_dados(arquivo_parquet)
        if self.df is not None:
            self.preprocessar_dados()

    def carregar_dados(self, arquivo_parquet):
        # Carrega os dados do arquivo Parquet
        try:
            df = pd.read_parquet(arquivo_parquet)
            st.success("Dados carregados com sucesso do arquivo Parquet!")
            st.info(f"Total de registros: {len(df):,}")
            return df
        except FileNotFoundError:
            st.error(f"Erro: Arquivo {arquivo_parquet} não encontrado.")
            st.info("💡 Dica: Execute primeiro o script de conversão para Parquet")
            return None
        except Exception as e:
            st.error(f"Erro ao carregar arquivo Parquet: {e}")
            # Tentar carregar CSV como fallback
            try:
                csv_path = arquivo_parquet.replace('.parquet', '.csv')
                if os.path.exists(csv_path):
                    st.info("Tentando carregar CSV como alternativa...")
                    df = pd.read_csv(csv_path)
                    st.success("Dados carregados do CSV como alternativa!")
                    return df
            except:
                pass
            return None

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

    def calcular_metricas(self):
        # Calcula as metricas principais
        if self.df is None:
            return None

        metricas = {
            'total_viagens': len(self.df),
            'media_valores': self.df['gmv_success'].mean() if 'gmv_success' in self.df.columns else 0,
        }

        # Destino mais comum
        if 'place_destination_departure' in self.df.columns:
            metricas['destino_mais_comum'] = (
                self.df['place_destination_departure'].mode()[0] 
                if not self.df['place_destination_departure'].mode().empty else 'N/A'
            )
        else:
            metricas['destino_mais_comum'] = 'N/A'

        # Calcular frequencia média de compra em meses
        if 'fk_contact' in self.df.columns and 'data_hora' in self.df.columns:
            freq_compras = self.calcular_frequencia_compras()
            metricas['frequencia_media_compra'] = freq_compras
        else:
            metricas['frequencia_media_compra'] = None

        return metricas

    def calcular_frequencia_compras(self):
        # Calcula a frequencia média de compra por cliente em meses
        compras_por_cliente = self.df.groupby('fk_contact')['data_hora'].agg(['min', 'max', 'count'])
        compras_por_cliente = compras_por_cliente[compras_por_cliente['count'] > 1]

        if len(compras_por_cliente) == 0:
            return 0

        compras_por_cliente['dias_entre_compras'] = (
                (compras_por_cliente['max'] - compras_por_cliente['min']).dt.days
                / (compras_por_cliente['count'] - 1)
        )

        media_dias = compras_por_cliente['dias_entre_compras'].mean()
        return round(media_dias / 30, 1)  # Converter para meses

    # Gráficos com estilo Click Bus (amarelo e roxo)
    def gerar_grafico_media_mensal(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        
        if 'mes_ano' in self.df.columns and 'gmv_success' in self.df.columns:
            media_mensal = self.df.groupby('mes_ano')['gmv_success'].mean()
            ax.plot(media_mensal.index.astype(str), media_mensal.values,
                    marker='o', linewidth=2, markersize=6, color=click_bus_palette[0])
            
            media_geral = self.df['gmv_success'].mean()
            ax.axhline(y=media_geral, color=click_bus_palette[1], linestyle='--', alpha=0.7,
                       label=f'Média Geral: R$ {media_geral:.2f}')
        else:
            ax.text(0.5, 0.5, 'Dados insuficientes para o gráfico', 
                    ha='center', va='center', transform=ax.transAxes)
        
        ax.set_title('Média de Valores por Mês', fontweight='bold', fontsize=14, pad=20, color=click_bus_palette[4])
        ax.set_xlabel('Mês/Ano', fontsize=10, color=click_bus_palette[4])
        ax.set_ylabel('Valor Médio (R$)', fontsize=10, color=click_bus_palette[4])
        ax.tick_params(axis='x', rotation=45, colors=click_bus_palette[4])
        ax.tick_params(axis='y', colors=click_bus_palette[4])
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#F5F5F5')
        ax.legend(facecolor='white', edgecolor='none')
        plt.tight_layout()
        return fig

    def gerar_grafico_destinos(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        
        if 'place_destination_departure' in self.df.columns:
            top_destinos = self.df['place_destination_departure'].value_counts().head(10)
            ax.barh(range(len(top_destinos)), top_destinos.values, color=click_bus_palette[0])
            ax.set_yticks(range(len(top_destinos)))
            ax.set_yticklabels(top_destinos.index, color=click_bus_palette[4])
            
            for i, v in enumerate(top_destinos.values):
                ax.text(v + max(top_destinos.values) * 0.01, i, str(v), va='center',
                        fontweight='bold', color=click_bus_palette[4])
        else:
            ax.text(0.5, 0.5, 'Dados de destinos não disponíveis', 
                    ha='center', va='center', transform=ax.transAxes)
        
        ax.set_title('Top 10 Destinos Mais Comuns', fontweight='bold', fontsize=14, pad=20, color=click_bus_palette[4])
        ax.set_xlabel('Número de Viagens', fontsize=10, color=click_bus_palette[4])
        ax.tick_params(axis='x', colors=click_bus_palette[4])
        ax.set_facecolor('#F5F5F5')
        plt.tight_layout()
        return fig

    def gerar_grafico_distribuicao_valores(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        
        if 'gmv_success' in self.df.columns:
            ax.hist(self.df['gmv_success'], bins=30, alpha=0.7, edgecolor='white',
                    color=click_bus_palette[0])
            
            media = self.df['gmv_success'].mean()
            mediana = self.df['gmv_success'].median()
            ax.axvline(media, color=click_bus_palette[1], linestyle='--', label=f'Média: R$ {media:.2f}')
            ax.axvline(mediana, color=click_bus_palette[2], linestyle='--', label=f'Mediana: R$ {mediana:.2f}')
        else:
            ax.text(0.5, 0.5, 'Dados de valores não disponíveis', 
                    ha='center', va='center', transform=ax.transAxes)
        
        ax.set_title('Distribuição de Valores das Passagens', fontweight='bold',
                     fontsize=14, pad=20, color=click_bus_palette[4])
        ax.set_xlabel('Valor (R$)', fontsize=10, color=click_bus_palette[4])
        ax.set_ylabel('Frequência', fontsize=10, color=click_bus_palette[4])
        ax.tick_params(axis='x', colors=click_bus_palette[4])
        ax.tick_params(axis='y', colors=click_bus_palette[4])
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#F5F5F5')
        ax.legend(facecolor='white', edgecolor='none')
        plt.tight_layout()
        return fig

    def gerar_grafico_retorno(self):
        fig, ax = plt.subplots(figsize=(8, 8))
        fig.patch.set_facecolor('white')
        
        if 'tem_retorno' in self.df.columns:
            contagem_retorno = self.df['tem_retorno'].value_counts()
            labels = ['Sem Retorno', 'Com Retorno']
            cores = [click_bus_palette[0], click_bus_palette[1]]
            wedges, texts, autotexts = ax.pie(contagem_retorno.values, labels=labels, colors=cores,
                                              autopct='%1.1f%%', startangle=90)

            for text in texts:
                text.set_color(click_bus_palette[4])
                text.set_fontweight('bold')
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        else:
            ax.text(0.5, 0.5, 'Dados de retorno não disponíveis', 
                    ha='center', va='center', transform=ax.transAxes)
        
        ax.set_title('Proporção de Viagens com Retorno', fontweight='bold',
                     fontsize=14, pad=20, color=click_bus_palette[4])
        plt.tight_layout()
        return fig

    def gerar_grafico_sazonalidade(self):
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('white')
        
        if 'mes_ano' in self.df.columns:
            viagens_por_mes = self.df.groupby('mes_ano').size()
            ax.plot(viagens_por_mes.index.astype(str), viagens_por_mes.values,
                    marker='o', linewidth=2, color=click_bus_palette[0])
        else:
            ax.text(0.5, 0.5, 'Dados de temporalidade não disponíveis', 
                    ha='center', va='center', transform=ax.transAxes)
        
        ax.set_title('Sazonalidade - Número de Viagens por Mês', fontweight='bold',
                     fontsize=14, pad=20, color=click_bus_palette[4])
        ax.set_xlabel('Mês/Ano', fontsize=10, color=click_bus_palette[4])
        ax.set_ylabel('Número de Viagens', fontsize=10, color=click_bus_palette[4])
        ax.tick_params(axis='x', rotation=45, colors=click_bus_palette[4])
        ax.tick_params(axis='y', colors=click_bus_palette[4])
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#F5F5F5')
        plt.tight_layout()
        return fig

# Interface principal do Streamlit
# Interface principal do Streamlit
def main():
    # Cabeçalho com logo (simulado)
    st.markdown(
        """
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
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<h1 class="main-header">🚌 DataBus - Análise de Viagens ClickBus</h1>', unsafe_allow_html=True)
    
    # Verificar se o arquivo Parquet existe, se não, converter do CSV
    arquivo_parquet = "dados_viagens.parquet"
    arquivo_csv = "df_t.csv"  # Nome do seu arquivo CSV
    
    if not os.path.exists(arquivo_parquet):
        if os.path.exists(arquivo_csv):
            st.warning("Arquivo Parquet não encontrado. Convertendo CSV...")
            
            # Converter CSV para Parquet automaticamente
            try:
                with st.spinner("Convertendo CSV para Parquet (isso pode demorar alguns minutos)..."):
                    # Ler o CSV
                    df = pd.read_csv(arquivo_csv)
                    
                    # Converter para Parquet
                    df.to_parquet(arquivo_parquet, engine='pyarrow', compression='snappy')
                    
                    st.success("✅ Conversão concluída! Recarregando...")
                    st.experimental_rerun()  # Recarregar a página
                    
            except Exception as e:
                st.error(f"❌ Erro na conversão: {e}")
                st.info("💡 Certifique-se de que o pyarrow está instalado: `pip install pyarrow`")
        else:
            st.warning("Nenhum arquivo de dados encontrado!")
            st.info("""
            **Para usar o sistema:**
            1. Certifique-se de que o arquivo `df_t.csv` está na mesma pasta
            2. Ou faça upload de um arquivo CSV abaixo
            """)
            
            # Opção de upload de CSV
            uploaded_file = st.file_uploader("Faça upload de um arquivo CSV", type="csv")
            if uploaded_file is not None:
                try:
                    with st.spinner("Processando arquivo CSV..."):
                        # Salvar o arquivo uploadado
                        with open("temp_uploaded.csv", "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Converter para Parquet
                        df = pd.read_csv("temp_uploaded.csv")
                        df.to_parquet(arquivo_parquet, engine='pyarrow', compression='snappy')
                        
                        st.success("✅ Arquivo convertido com sucesso! Recarregando...")
                        st.experimental_rerun()
                        
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {e}")
    
    # Se o Parquet existe ou foi convertido, carregar os dados
    if os.path.exists(arquivo_parquet):
        analise = AnaliseDadosViagens(arquivo_parquet)
        
        if analise.df is not None:
          
            # Exibir métricas
            metricas = analise.calcular_metricas()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f'<div class="metric-card">Total de Viagens: <b>{metricas["total_viagens"]:,}</b></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-card">Média de Valores: <b>R$ {metricas["media_valores"]:.2f}</b></div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'<div class="metric-card">Destino Mais Comum: <b>{metricas["destino_mais_comum"]}</b></div>', unsafe_allow_html=True)
            
            with col3:
                if metricas['frequencia_media_compra']:
                    st.markdown(f'<div class="metric-card">Frequência Média: <b>{metricas["frequencia_media_compra"]} meses</b></div>', unsafe_allow_html=True)
            
            # Seleção de gráficos
            st.subheader("📊 Visualizações")
            
            opcoes_graficos = {
                "Média de Valores por Mês": analise.gerar_grafico_media_mensal,
                "Top 10 Destinos": analise.gerar_grafico_destinos,
                "Distribuição de Valores": analise.gerar_grafico_distribuicao_valores,
                "Viagens com Retorno": analise.gerar_grafico_retorno,
                "Sazonalidade": analise.gerar_grafico_sazonalidade
            }
            
            grafico_selecionado = st.selectbox("Selecione o gráfico:", list(opcoes_graficos.keys()))
            
            if st.button("Gerar Gráfico"):
                with st.spinner("Gerando gráfico..."):
                    fig = opcoes_graficos[grafico_selecionado]()
                    st.pyplot(fig)
            
            # Mostrar informações do dataset
            with st.expander("📋 Informações do Dataset"):
                st.write(f"**Total de linhas:** {len(analise.df):,}")
                st.write(f"**Total de colunas:** {len(analise.df.columns)}")
                st.write("**Colunas disponíveis:**", list(analise.df.columns))
            
            # Mostrar dados
            if st.checkbox("Mostrar amostra dos dados"):
                st.subheader("Amostra dos Dados (100 primeiras linhas)")
                st.dataframe(analise.df.head(100))
    else:
        st.warning("Arquivo Parquet não encontrado!")
        st.info("""
        **Para usar o sistema:**
        1. Execute primeiro o script `parquet_conversao.py` para converter seu CSV
        2. Certifique-se de que o arquivo `dados_viagens.parquet` está na mesma pasta
        3. Recarregue esta página
        """)
        
        # Opção de upload de CSV alternativo
        uploaded_file = st.file_uploader("Ou faça upload de um arquivo CSV", type="csv")
        if uploaded_file is not None:
            # Salvar temporariamente e converter
            with st.spinner("Processando arquivo CSV..."):
                temp_csv = "temp_uploaded.csv"
                with open(temp_csv, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Converter para Parquet
                try:
                    import parquet_conversao
                    parquet_conversao.converter_csv_para_parquet(temp_csv, "dados_viagens.parquet")
                    st.success("Arquivo convertido com sucesso! Recarregue a página.")
                except:
                    st.error("Erro ao converter arquivo. Verifique o formato.")

if __name__ == "__main__":
    main()
