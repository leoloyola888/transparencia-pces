import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Transparência PCES", page_icon="🚓", layout="wide")

st.title("🚓 Portal de Transparência - Polícia Civil (ES)")
st.write("Dados abertos sobre o quadro de Oficiais Investigadores de Polícia (antigos agentes, investigadores e escrivães).")
st.markdown("---")

@st.cache_data
def carregar_dados():
    df_servidores = pd.read_csv("servidores.csv", low_memory=False)
    try:
        df_remuneracao = pd.read_csv("remuneracao06.csv", low_memory=False)
    except FileNotFoundError:
        df_remuneracao = pd.DataFrame() 
    return df_servidores, df_remuneracao

df_serv, df_rem = carregar_dados()

aba1, aba2 = st.tabs(["📊 Efetivo Ativo & Abono", "📉 Histórico de Saídas"])

# =============================================================
# ABA 1: ATIVOS E ABONO 
# =============================================================
with aba1:
    st.subheader("Raio-X do Efetivo Atual")
    
    if not df_rem.empty:
        # Filtra Ativos
        df_ativos = df_serv[df_serv['Situacao'] == 'ATIVO'].copy()
        
        # Filtra Rubrica 220
        df_rem['CodRubrica'] = df_rem['CodRubrica'].astype(str).str.strip()
        df_abono = df_rem[df_rem['CodRubrica'] == '220'].copy()
        
        # Pega os NumFunc únicos e cria a marcação
        df_abono['Recebe_Abono'] = 'Sim'
        df_abono_simples = df_abono[['NumFunc', 'Recebe_Abono']].drop_duplicates()
        
        # Cruza os dados
        df_painel = pd.merge(df_ativos, df_abono_simples, on='NumFunc', how='left')
        df_painel['Recebe_Abono'] = df_painel['Recebe_Abono'].fillna('Não')
        
        # Cálculos para os indicadores
        total_ativos = len(df_painel)
        com_abono = len(df_painel[df_painel['Recebe_Abono'] == 'Sim'])
        taxa = (com_abono / total_ativos) * 100 if total_ativos > 0 else 0
        
        mes_dados = df_rem['MesCompetencia'].iloc[0] if 'MesCompetencia' in df_rem.columns else "Mês Atual"
        
        # Exibe as métricas EM DESTAQUE NA TELA
        col1, col2 = st.columns(2)
        col1.metric("Total de Policiais Ativos", f"{total_ativos:,}".replace(',','.'))
        col2.metric(f"Com Abono Permanência ({mes_dados})", f"{com_abono} ({taxa:.1f}%)")
        
        # --- NOVO: TERMÔMETRO DE REPOSIÇÃO ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"🔥 **Termômetro de Reposição:** Atualmente, existem **{com_abono} servidores** com requisitos preenchidos para aposentadoria. Cada um desses servidores representa uma potencial **nova vaga** a ser reposta pelo Estado no curto/médio prazo.")
        
        # Barra de progresso visual do abono
        st.progress(com_abono / total_ativos if total_ativos > 0 else 0)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.write("##### Detalhamento do Efetivo")
        colunas_exibicao = ['NumFunc', 'Nome', 'Cargo', 'Recebe_Abono']
        colunas_exibicao = [c for c in colunas_exibicao if c in df_painel.columns]
        st.dataframe(df_painel[colunas_exibicao], use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Arquivo 'remuneracao06.csv' não encontrado.")

# =============================================================
# ABA 2: HISTÓRICO DE SAÍDAS
# =============================================================
with aba2:
    st.subheader("Evolução Temporal de Saídas")
    
    df_saidas = df_serv[df_serv['Situacao'].isin(['APOSENTADO', 'DESLIGADO'])].copy()
    
    df_saidas['Data_Saida'] = pd.to_datetime(df_saidas['Aposentadoria'], errors='coerce')
    mask_desligado = df_saidas['Situacao'] == 'DESLIGADO'
    if 'Vacancia' in df_saidas.columns:
        df_saidas.loc[mask_desligado, 'Data_Saida'] = pd.to_datetime(df_saidas.loc[mask_desligado, 'Vacancia'], errors='coerce')
    
    df_saidas = df_saidas.dropna(subset=['Data_Saida'])
    df_saidas['Ano'] = df_saidas['Data_Saida'].dt.year
    df_saidas = df_saidas[(df_saidas['Ano'] >= 2005) & (df_saidas['Ano'] <= 2026)]
    
    dados_grafico = df_saidas.groupby(['Ano', 'Situacao']).size().reset_index(name='Quantidade')
    
    if not dados_grafico.empty:
        fig = px.bar(dados_grafico, x='Ano', y='Quantidade', color='Situacao', 
                     title="Aposentadorias e Desligamentos por Ano",
                     barmode='stack',
                     color_discrete_map={'APOSENTADO': '#1f77b4', 'DESLIGADO': '#d62728'})
                     
        fig.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.write("##### Resumo por Ano")
        tabela_resumo = df_saidas.groupby('Ano').size().reset_index(name='Total de Saídas').sort_values('Ano', ascending=False)
        st.dataframe(tabela_resumo, use_container_width=True, hide_index=True)
