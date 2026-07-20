import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÕES DA PÁGINA (Aba do navegador)
st.set_page_config(
    page_title="Inteligência de Dados | PCES", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. INJEÇÃO DE CSS (O segredo para tirar a "Cara de IA/Padrão")
st.markdown("""
<style>
    /* Cor de fundo principal mais profissional (cinza super claro quase branco) */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Título principal customizado */
    .main-title {
        font-size: 38px;
        font-weight: 800;
        color: #1C3F60; /* Azul Marinho Polícia */
        margin-bottom: 0px;
        padding-bottom: 0px;
        font-family: 'Arial Black', sans-serif;
    }
    
    .sub-title {
        font-size: 16px;
        color: #555555;
        margin-top: -10px;
        margin-bottom: 30px;
    }

    /* Estilo dos "Cards" de Métricas (Deixando eles com cara de Dashboard Profissional) */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E4E8;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 2px 4px 12px rgba(0,0,0,0.05);
        border-left: 6px solid #1C3F60; /* Faixa lateral azul */
    }
    
    [data-testid="stMetricValue"] {
        font-size: 38px !important;
        font-weight: 800 !important;
        color: #1C3F60 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 15px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        color: #7F8C8D !important;
    }

    /* Customização das Abas (Tabs) para parecerem botões nativos */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: #FFFFFF;
        border-radius: 8px 8px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        border: 1px solid #E0E4E8;
        border-bottom: none;
        color: #555555;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1C3F60;
        color: white !important;
        border-color: #1C3F60;
    }
    
    /* Ajuste da tabela para ficar mais clean */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Aviso de Vagas formatado */
    .alerta-vagas {
        background-color: #FFF3CD;
        border-left: 5px solid #FFC107;
        padding: 15px;
        border-radius: 5px;
        color: #856404;
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
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.metric("Total de Investigadores Ativos", f"{total_ativos:,}".replace(',','.'))
        with col2:
            st.metric(f"Elegíveis para Aposentadoria", f"{com_abono}")
        with col3:
            st.metric("Taxa de Renovação Imediata", f"{taxa:.1f}%")
        
        # Alerta customizado via HTML/CSS (sai a cara padrão do st.info)
        texto_alerta = f"<strong>Atenção Estratégica:</strong> Há {com_abono} servidores recebendo Abono Permanência. Estes profissionais já reúnem condições legais para aposentadoria voluntária, indicando uma potencial demanda de reposição de {taxa:.1f}% do quadro atual a curto prazo."
        st.markdown(f'<div class="alerta-vagas">{texto_alerta}</div>', unsafe_allow_html=True)
        
        st.markdown("#### Listagem do Efetivo")
        colunas_exibicao = ['NumFunc', 'Nome', 'Cargo', 'Recebe_Abono']
        colunas_exibicao = [c for c in colunas_exibicao if c in df_painel.columns]
        st.dataframe(df_painel[colunas_exibicao], use_container_width=True, hide_index=True)
    else:
        st.error("Base de dados de remuneração ausente.")

# =============================================================
# ABA 2: HISTÓRICO DE SAÍDAS
# =============================================================
with aba2:
    st.markdown("#### Curva Histórica de Vacâncias e Aposentadorias")
    
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
        # Plotly Customizado para visual corporativo
        fig2 = px.bar(dados_grafico, x='Ano', y='Quantidade', color='Situacao', 
                     barmode='stack',
                     color_discrete_map={'APOSENTADO': '#4C72B0', 'DESLIGADO': '#C44E52'}) # Cores sóbrias
                     
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", # Fundo transparente (tira a grade feia)
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickmode='linear', dtick=1, showgrid=False, linecolor='#555'),
            yaxis=dict(showgrid=True, gridcolor='#E0E4E8', title="Qtd. de Servidores"),
            legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), # Legenda em cima, clean
            margin=dict(l=0, r=0, t=30, b=0),
            font_family="Arial"
        )
        # Remove a barra flutuante chata do plotly
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

# =============================================================
# ABA 3: PERFIL DE TEMPO DE CASA
# =============================================================
with aba3:
    st.markdown("#### Composição do Efetivo por Tempo de Corporação")
    
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
                     color_discrete_sequence=['#1C3F60']) # Cor única institucional
                     
        fig3.update_traces(textposition='outside', textfont_size=14, textfont_color="#333", cliponaxis=False)
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, linecolor='#555', title=""),
            yaxis=dict(showgrid=True, gridcolor='#E0E4E8', title=""),
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0),
            font_family="Arial"
        )
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
