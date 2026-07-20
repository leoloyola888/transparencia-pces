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

# Adicionamos a terceira aba
aba1, aba2, aba3 = st.tabs([
    "📊 Efetivo Ativo & Abono", 
    "📉 Histórico de Saídas", 
    "⏱️ Tempo de Casa (Perfil)"
])

# =============================================================
# ABA 1: ATIVOS E ABONO 
# =============================================================
with aba1:
    st.subheader("Raio-X do Efetivo Atual")
    
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
        
        mes_dados = df_rem['MesCompetencia'].iloc[0] if 'MesCompetencia' in df_rem.columns else "Mês Atual"
        
        col1, col2 = st.columns(2)
        col1.metric("Total de Policiais Ativos", f"{total_ativos:,}".replace(',','.'))
        col2.metric(f"Com Abono Permanência ({mes_dados})", f"{com_abono} ({taxa:.1f}%)")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"🔥 **Termômetro de Reposição:** Atualmente, existem **{com_abono} servidores** com requisitos preenchidos para aposentadoria. Cada um desses servidores representa uma potencial **nova vaga** a ser reposta pelo Estado no curto/médio prazo.")
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
        fig2 = px.bar(dados_grafico, x='Ano', y='Quantidade', color='Situacao', 
                     title="Aposentadorias e Desligamentos por Ano",
                     barmode='stack',
                     color_discrete_map={'APOSENTADO': '#1f77b4', 'DESLIGADO': '#d62728'})
                     
        fig2.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        
        st.write("##### Resumo por Ano")
        tabela_resumo = df_saidas.groupby('Ano').size().reset_index(name='Total de Saídas').sort_values('Ano', ascending=False)
        st.dataframe(tabela_resumo, use_container_width=True, hide_index=True)

# =============================================================
# ABA 3: PERFIL DE TEMPO DE CASA
# =============================================================
with aba3:
    st.subheader("Perfil de Tempo de Corporação (Apenas Ativos)")
    st.write("Distribuição do efetivo em atividade com base na data de posse (ingresso na corporação).")
    
    df_ativos = df_serv[df_serv['Situacao'] == 'ATIVO'].copy()
    df_ativos['Exercicio'] = pd.to_datetime(df_ativos['Exercicio'], errors='coerce')
    df_ativos = df_ativos.dropna(subset=['Exercicio'])
    
    # Referência: Junho de 2026 (mês da folha de pagamento)
    ref_date = pd.to_datetime('2026-06-01')
    df_ativos['Anos_Servico'] = (ref_date - df_ativos['Exercicio']).dt.days / 365.25
    
    # Criar faixas de tempo
    bins = [-1, 5, 10, 15, 20, 25, 30, 100]
    labels = ['Até 5 anos', '6 a 10 anos', '11 a 15 anos', '16 a 20 anos', '21 a 25 anos', '26 a 30 anos', 'Mais de 30 anos']
    df_ativos['Faixa_Tempo'] = pd.cut(df_ativos['Anos_Servico'], bins=bins, labels=labels)
    
    # Agrupar e contar
    df_tempo = df_ativos['Faixa_Tempo'].value_counts().reset_index()
    df_tempo.columns = ['Faixa de Tempo', 'Quantidade']
    
    # Ordenar corretamente pelas faixas
    ordem_map = {l: i for i, l in enumerate(labels)}
    df_tempo['Ordem'] = df_tempo['Faixa de Tempo'].map(ordem_map)
    df_tempo = df_tempo.sort_values('Ordem').drop(columns=['Ordem'])
    
    if not df_tempo.empty:
        # Criar o gráfico
        fig3 = px.bar(df_tempo, x='Faixa de Tempo', y='Quantidade', 
                     text='Quantidade',
                     color='Faixa de Tempo',
                     title="Quantos anos de polícia tem o efetivo atual?",
                     color_discrete_sequence=px.colors.qualitative.Prism)
                     
        fig3.update_traces(textposition='outside')
        fig3.update_layout(
            showlegend=False,
            xaxis_title="Tempo de Serviço (Data de Posse)",
            yaxis_title="Número de Policiais",
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
        
        st.write("##### Tabela Detalhada")
        df_tempo['% do Efetivo'] = (df_tempo['Quantidade'] / df_tempo['Quantidade'].sum() * 100).round(1).astype(str) + '%'
        st.dataframe(df_tempo, use_container_width=True, hide_index=True)
