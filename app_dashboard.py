import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(
    page_title="Inteligência de Dados | PCES", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CSS SEGURO (Apenas Textos e Alerta)
st.markdown("""
<style>
    .main-title {
        font-size: 38px;
        font-weight: 800;
        color: #1C3F60;
        margin-bottom: 0px;
        padding-bottom: 0px;
        font-family: 'Arial Black', sans-serif;
    }
    .sub-title {
        font-size: 16px;
        color: #888888;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    .alerta-vagas {
        background-color: #332b00; /* Tom escuro elegante para o alerta no dark mode */
        border-left: 5px solid #FFC107;
        padding: 15px;
        border-radius: 5px;
        color: #FFC107;
        font-size: 15px;
        margin-top: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 3. CABEÇALHO CUSTOMIZADO
st.markdown('<p class="main-title">DIRETORIA DE INTELIGÊNCIA E DADOS - PCES</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Painel Estratégico: Quadro de Oficiais Investigadores de Polícia (Ativos, Saídas e Projeções)</p>', unsafe_allow_html=True)


@st.cache_data
def carregar_dados():
    df_servidores = pd.read_csv("servidores.csv", low_memory=False)
    try:
        df_remuneracao = pd.read_csv("remuneracao06.csv", low_memory=False)
    except FileNotFoundError:
        df_remuneracao = pd.DataFrame() 
    return df_servidores, df_remuneracao

df_serv, df_rem = carregar_dados()

aba1, aba2, aba3 = st.tabs([
    "📍 Visão Geral & Reposição", 
    "📉 Fluxo de Saídas", 
    "⏱️ Perfil da Tropa"
])

# =============================================================
# ABA 1: ATIVOS E ABONO 
# =============================================================
with aba1:
    if not df_rem.empty:
        df_ativos = df_serv[df_serv['Situacao'] == 'ATIVO'].copy()
        
        df_rem['CodRubrica'] = df_rem['CodRubrica'].astype(str).str.strip()
        df_abono = df_rem[df_rem['CodRubrica'] == '220'].copy()
        
        df_abono['Recebe_Abono'] = 'Sim'
        df_abono_simples = df_abono[['NumFunc', 'Recebe_Abono']].drop_duplicates()
        
        df_painel = pd.merge(df_ativos, df_abono_simples, on='NumFunc', how='left')
        df_painel['Recebe_Abono'] = df_painel['Recebe_Abono'].fillna('Não')
        
        total_ativos = len(df_painel)
        com_abono = len(df_painel[df_painel['Recebe_Abono'] == 'Sim'])
        taxa = (com_abono / total_ativos) * 100 if total_ativos > 0 else 0
        
        # Métricas Nativas do Streamlit (Sem quebrar o layout)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Investigadores Ativos", f"{total_ativos:,}".replace(',','.'))
        col2.metric(f"Elegíveis para Aposentadoria", f"{com_abono}")
        col3.metric("Taxa de Renovação Imediata", f"{taxa:.1f}%")
        
        texto_alerta = f"<strong>Atenção Estratégica:</strong> Há {com_abono} servidores recebendo Abono Permanência. Estes profissionais já reúnem condições legais para aposentadoria voluntária, indicando uma potencial demanda de reposição de {taxa:.1f}% do quadro atual a curto prazo."
        st.markdown(f'<div class="alerta-vagas">{texto_alerta}</div>', unsafe_allow_html=True)
        
        st.write("#### Listagem do Efetivo")
        colunas_exibicao = ['NumFunc', 'Nome', 'Cargo', 'Recebe_Abono']
        colunas_exibicao = [c for c in colunas_exibicao if c in df_painel.columns]
        st.dataframe(df_painel[colunas_exibicao], use_container_width=True, hide_index=True)
    else:
        st.error("Base de dados de remuneração ausente.")

# =============================================================
# ABA 2: HISTÓRICO DE SAÍDAS
# =============================================================
with aba2:
    st.write("#### Curva Histórica de Vacâncias e Aposentadorias")
    
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
        fig2 = px.bar(dados_grafico, x='Ano', y='Quantidade', color='Situacao', 
                     barmode='stack',
                     color_discrete_map={'APOSENTADO': '#4C72B0', 'DESLIGADO': '#C44E52'})
                     
        fig2.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

# =============================================================
# ABA 3: PERFIL DE TEMPO DE CASA
# =============================================================
with aba3:
    st.write("#### Composição do Efetivo por Tempo de Corporação")
    
    df_ativos = df_serv[df_serv['Situacao'] == 'ATIVO'].copy()
    df_ativos['Exercicio'] = pd.to_datetime(df_ativos['Exercicio'], errors='coerce')
    df_ativos = df_ativos.dropna(subset=['Exercicio'])
    
    ref_date = pd.to_datetime('2026-06-01')
    df_ativos['Anos_Servico'] = (ref_date - df_ativos['Exercicio']).dt.days / 365.25
    
    bins = [-1, 5, 10, 15, 20, 25, 30, 100]
    labels = ['Até 5 anos', '6 a 10 anos', '11 a 15 anos', '16 a 20 anos', '21 a 25 anos', '26 a 30 anos', 'Mais de 30 anos']
    df_ativos['Faixa_Tempo'] = pd.cut(df_ativos['Anos_Servico'], bins=bins, labels=labels)
    
    df_tempo = df_ativos['Faixa_Tempo'].value_counts().reset_index()
    df_tempo.columns = ['Faixa de Tempo', 'Quantidade']
    
    ordem_map = {l: i for i, l in enumerate(labels)}
    df_tempo['Ordem'] = df_tempo['Faixa de Tempo'].map(ordem_map)
    df_tempo = df_tempo.sort_values('Ordem').drop(columns=['Ordem'])
    
    if not df_tempo.empty:
        fig3 = px.bar(df_tempo, x='Faixa de Tempo', y='Quantidade', 
                     text='Quantidade',
                     color_discrete_sequence=['#4C72B0'])
                     
        fig3.update_traces(textposition='outside', cliponaxis=False)
        fig3.update_layout(
            showlegend=False,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
