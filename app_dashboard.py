import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(
    page_title="Inteligência de Dados | PCES", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CSS SEGURO
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
        background-color: #332b00; 
        border-left: 5px solid #FFC107;
        padding: 15px;
        border-radius: 5px;
        color: #FFC107;
        font-size: 15px;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .stProgress > div > div > div > div {
        background-color: #1C3F60;
    }
</style>
""", unsafe_allow_html=True)

# 3. CABEÇALHO CUSTOMIZADO COM LOGO
col_logo, col_texto = st.columns([1, 8])

with col_logo:
    # Lê a imagem transparente da sua pasta
    st.image("logo.png", width=90) 

with col_texto:
    st.markdown('<p class="main-title">DIRETORIA DE INTELIGÊNCIA E DADOS - PCES</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Painel Estratégico da Comissão de Aprovados (Investigador)</p>', unsafe_allow_html=True)

# 4. MOTOR DA API - DETETIVE DO MÊS ATUAL
def pegar_id_mais_recente(nome_do_pacote):
    url_catalogo = f"https://transparencia.es.gov.br/api/3/action/package_show?id={nome_do_pacote}"
    resposta = requests.get(url_catalogo).json()
    arquivos = resposta['result']['resources']
    ultimo_arquivo = arquivos[-1] 
    return ultimo_arquivo['id']

@st.cache_data(ttl=86400) # Robô atualiza os dados a cada 24 horas
def carregar_dados():
    # =====================================================================
    # ⚠️ ATENÇÃO: COLOQUE AS CHAVES DO GOVERNO AQUI NAS DUAS LINHAS ABAIXO
    # =====================================================================
    id_servidores = "c26013df-354d-4467-9272-37e7bf570ccf"
    nome_pacote_remuneracao = "portal-da-transparencia-pessoal"
    # =====================================================================

    try:
        # Descobre o ID do mês mais recente da remuneração automaticamente
        id_remuneracao_atual = pegar_id_mais_recente(nome_pacote_remuneracao)
        
        base_url = "https://transparencia.es.gov.br/api/3/action/datastore_search"
        
        # Faz o download dos Servidores via API
        url_serv = f"{base_url}?resource_id={id_servidores}&limit=100000"
        resp_serv = requests.get(url_serv).json()
        df_servidores = pd.DataFrame(resp_serv['result']['records'])
        
        # Faz o download da Remuneração via API
        url_rem = f"{base_url}?resource_id={id_remuneracao_atual}&limit=100000"
        resp_rem = requests.get(url_rem).json()
        df_remuneracao = pd.DataFrame(resp_rem['result']['records'])
        
        # Filtro automático exclusivo para o cargo de vocês
        if 'Cargo' in df_servidores.columns:
            df_servidores = df_servidores[df_servidores['Cargo'] == 'OFICIAL INVESTIGADOR DE POLICIA']
            
        return df_servidores, df_remuneracao
        
    except Exception as e:
        # Modo de Segurança: avisa se o site do governo estiver fora do ar
        st.error(f"⚠️ Erro ao conectar com o banco de dados do Governo. Verifique os códigos inseridos ou se o Portal está fora do ar. Detalhe técnico: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_serv, df_rem = carregar_dados()

# 5. ESTRUTURA DAS ABAS
aba1, aba2, aba3 = st.tabs([
    "📍 Visão Geral & Déficit", 
    "📉 Fluxo de Saídas", 
    "⏱️ Perfil da Tropa"
])

# =============================================================
# ABA 1: VISÃO GERAL E DÉFICIT
# =============================================================
with aba1:
    if not df_rem.empty:
        df_ativos = df_serv[df_serv['Situacao'] == 'ATIVO'].copy()
        df_afastados = df_serv[df_serv['Situacao'] == 'AFASTADO PARA APOSENTADORIA'].copy()
        
        df_rem['CodRubrica'] = df_rem['CodRubrica'].astype(str).str.strip()
        df_abono = df_rem[df_rem['CodRubrica'] == '220'].copy()
        
        df_abono['Recebe_Abono'] = 'Sim'
        df_abono_simples = df_abono[['NumFunc', 'Recebe_Abono']].drop_duplicates()
        
        df_painel = pd.merge(df_ativos, df_abono_simples, on='NumFunc', how='left')
        df_painel['Recebe_Abono'] = df_painel['Recebe_Abono'].fillna('Não')
        
        # --- CÁLCULOS ESTRATÉGICOS ---
        cargos_lei = 2740
        total_ativos = len(df_painel)
        total_afastados = len(df_afastados)
        total_ocupantes = total_ativos + total_afastados
        
        cargos_vagos = cargos_lei - total_ocupantes
        com_abono = len(df_painel[df_painel['Recebe_Abono'] == 'Sim'])
        
        taxa_ocupacao = (total_ocupantes / cargos_lei) * 100
        
        vagas_estrategicas = cargos_vagos + com_abono + total_afastados
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Cargos em Lei (Teto)", f"{cargos_lei:,}".replace(',','.'))
        col2.metric("Investigadores Ativos", f"{total_ativos:,}".replace(',','.'))
        col3.metric("Cargos Vagos (Déficit)", f"{cargos_vagos:,}".replace(',','.'))
        col4.metric(f"Vagas Iminentes", f"{com_abono + total_afastados}")
        
        st.write(f"**Ocupação do Quadro Legal ({taxa_ocupacao:.1f}% ocupado)**")
        st.progress(total_ocupantes / cargos_lei)
        
        texto_alerta = f"<strong>Mapa de Reposição:</strong> A corporação opera com um déficit real de {cargos_vagos:,} investigadores. Somando-se a isso os {total_afastados} servidores já afastados aguardando publicação de aposentadoria e os {com_abono} profissionais que recebem abono permanência, o volume estratégico de vacâncias chega a <strong>{vagas_estrategicas:,} vagas</strong>.".replace(',', '.')
        st.markdown(f'<div class="alerta-vagas">{texto_alerta}</div>', unsafe_allow_html=True)
        
        st.write("#### Listagem do Efetivo Ativo")
        colunas_exibicao = ['NumFunc', 'Nome', 'Cargo', 'Recebe_Abono']
        colunas_exibicao = [c for c in colunas_exibicao if c in df_painel.columns]
        st.dataframe(df_painel[colunas_exibicao], use_container_width=True, hide_index=True)
    else:
        st.warning("⏱️ Conectando à base de remuneração ou aguardando inserção dos IDs...")

# =============================================================
# ABA 2: HISTÓRICO DE SAÍDAS
# =============================================================
with aba2:
    st.write("#### Curva Histórica de Vacâncias e Aposentadorias")
    
    if not df_serv.empty:
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
    
    if not df_serv.empty:
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
