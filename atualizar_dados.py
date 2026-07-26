import pandas as pd

# 1. COLE OS LINKS DIRETOS DE DOWNLOAD AQUI
url_servidores = "https://dados.es.gov.br/dataset/4c3ef6d6-6a55-4c54-958b-87678d2b4d4e/resource/c26013df-354d-4467-9272-37e7bf570ccf/download/vinculosservidores.csv"
url_remuneracao = "https://dados.es.gov.br/dataset/4c3ef6d6-6a55-4c54-958b-87678d2b4d4e/resource/d558b77d-3e20-4b4a-815a-b8d0fc7b5222/download/remuneracoes-06_2026.csv"

print("🔄 Baixando a base completa de Servidores do ES...")
# Baixa e lê tudo na memória do seu PC (que é muito maior que a da nuvem)
df_serv = pd.read_csv(url_servidores, sep=';', encoding='latin-1', low_memory=False)

print("🎯 Filtrando apenas os Investigadores (CodCargo 2781)...")
# Limpa sujeiras do código e filtra
df_serv['CodCargo'] = df_serv['CodCargo'].astype(str).str.strip().str.replace('.0', '', regex=False)
df_pces = df_serv[df_serv['CodCargo'] == '2781']

# Salva a planilha filtrada na sua pasta
df_pces.to_csv("servidores_pces.csv", index=False)
print(f"✅ Arquivo de servidores salvo! Encontrados {len(df_pces)} investigadores.")

print("🔄 Baixando a base completa de Remuneração do ES...")
df_rem = pd.read_csv(url_remuneracao, sep=';', encoding='latin-1', low_memory=False)

print("🎯 Cruzando as remunerações com as matrículas da PCES...")
# Pega apenas o salário de quem está na lista de investigadores
matriculas = df_pces['NumFunc'].unique()
df_rem_pces = df_rem[df_rem['NumFunc'].isin(matriculas)]

# Salva a planilha de remuneração filtrada na sua pasta
df_rem_pces.to_csv("remuneracao_pces.csv", index=False)
print(f"✅ Arquivo de remuneração salvo! Total de registros: {len(df_rem_pces)}.")
print("🚀 Processo concluído! Os arquivos estão prontos para o Streamlit.")
