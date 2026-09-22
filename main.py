import streamlit as st
import json
import os
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Minecraft Server Telemetry", layout="wide")
st.title("⛏️ Estatísticas do Servidor")

# Caminhos definidos
SERVER_DIR = "../" 
STATS_DIR = os.path.join(SERVER_DIR, "world/players/stats")
USERCACHE = os.path.join(SERVER_DIR, "usercache.json")

@st.cache_data(ttl=60)
def carregar_dados_locais():
    # 1. Carrega o cache de nomes (UUID -> Nickname)
    nomes = {}
    if os.path.exists(USERCACHE):
        with open(USERCACHE, "r") as f:
            try:
                cache = json.load(f)
                nomes = {jogador["uuid"]: jogador["name"] for jogador in cache}
            except json.JSONDecodeError:
                pass

    # 2. Processa as estatísticas
    registros = []
    if not os.path.exists(STATS_DIR):
        return pd.DataFrame() # Retorna DataFrame vazio se a pasta não existir

    for arquivo in os.listdir(STATS_DIR):
        if arquivo.endswith(".json"):
            uuid = arquivo.replace(".json", "")
            nome_jogador = nomes.get(uuid, f"Desconhecido_{uuid[:8]}")
            caminho_arquivo = os.path.join(STATS_DIR, arquivo)
            
            with open(caminho_arquivo, "r") as f:
                try:
                    dados = json.load(f)
                except json.JSONDecodeError:
                    continue
            
            stats_nativas = dados.get("stats", {})
            
            # Navega pelas categorias e métricas do Minecraft
            for categoria_bruta, metricas in stats_nativas.items():
                categoria_limpa = categoria_bruta.replace("minecraft:", "")
                
                for metrica_bruta, valor in metricas.items():
                    metrica_limpa = metrica_bruta.replace("minecraft:", "")
                    
                    # Converte ticks para horas
                    if "time" in metrica_limpa or "minute" in metrica_limpa:
                         valor = round(valor / 72000, 2)
                    
                    # Converte centímetros para metros
                    elif "one_cm" in metrica_limpa:
                         metrica_limpa = metrica_limpa.replace("one_cm", "meters")
                         valor = round(valor / 100, 2)

                    registros.append({
                        "Jogador": nome_jogador,
                        "Categoria": categoria_limpa,
                        "Métrica": metrica_limpa,
                        "Valor": valor
                    })
                    
    return pd.DataFrame(registros)

df = carregar_dados_locais()

if df.empty:
    st.warning(f"Nenhum dado encontrado. Verifique se o diretório existe: {os.path.abspath(STATS_DIR)}")
else:
    # ---- BARRA LATERAL (Filtros) ----
    st.sidebar.header("Filtros do Ranking")
    
    lista_categorias = df["Categoria"].unique()
    categoria_selecionada = st.sidebar.selectbox("Selecione a Categoria", lista_categorias)
    
    # Filtra as métricas com base na categoria escolhida
    df_categoria = df[df["Categoria"] == categoria_selecionada]
    lista_metricas = df_categoria["Métrica"].unique()
    metrica_selecionada = st.sidebar.selectbox("Selecione a Métrica", lista_metricas)

    # ---- PROCESSAMENTO DO RANKING ----
    df_ranking = df_categoria[df_categoria["Métrica"] == metrica_selecionada]
    df_ranking = df_ranking.sort_values(by="Valor", ascending=False).reset_index(drop=True)
    df_exibicao = df_ranking[["Jogador", "Valor"]]

    # ---- INTERFACE PRINCIPAL ----
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader(f"🏆 Ranking: {metrica_selecionada}")
        st.dataframe(
            df_exibicao,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Jogador": st.column_config.TextColumn("Jogador"),
                "Valor": st.column_config.NumberColumn("Pontuação / Valor", format="%.2f")
            }
        )
        
    with col2:
        st.subheader("Gráfico Comparativo")
        st.bar_chart(df_exibicao.set_index("Jogador"))

    if st.button("Atualizar Dados Agora"):
        st.cache_data.clear()
        st.rerun()