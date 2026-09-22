import streamlit as st
import json
import os
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# Configuração inicial da página
st.set_page_config(page_title="Minecraft Server Telemetry", layout="wide", initial_sidebar_state="expanded")

# Atualiza a página a cada 5000 milissegundos (5 segundos) automaticamente
st_autorefresh(interval=5000, key="data_refresh")

# Caminhos definidos (ajuste conforme necessário)
SERVER_DIR = "../" 
STATS_DIR = os.path.join(SERVER_DIR, "world/players/stats")
USERCACHE = os.path.join(SERVER_DIR, "usercache.json")


# Adicione esta função logo após as importações iniciais
def carregar_traducoes():
    caminho = "traducoes.json"
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"categorias": {}, "metricas": {}}

# Carrega os dicionários diretamente do arquivo
traducoes = carregar_traducoes()
TRADUCOES_CATEGORIA = traducoes.get("categorias", {})
TRADUCOES_METRICA = traducoes.get("metricas", {})

# A função de formatação permanece a mesma
def formatar_nome_metrica(metrica):
    """Traduz a métrica ou limpa os underscores caso não esteja no dicionário."""
    if metrica in TRADUCOES_METRICA:
        return TRADUCOES_METRICA[metrica]
    return metrica.replace("_", " ").title()

@st.cache_data(ttl=4) # Cache de 4 segundos, logo antes do refresh da página
def carregar_dados():
    nomes = {}
    if os.path.exists(USERCACHE):
        with open(USERCACHE, "r") as f:
            try:
                cache = json.load(f)
                nomes = {jogador["uuid"]: jogador["name"] for jogador in cache}
            except json.JSONDecodeError:
                pass

    registros = []
    if not os.path.exists(STATS_DIR):
        return pd.DataFrame() 

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
            
            for categoria_bruta, metricas in stats_nativas.items():
                categoria_limpa = categoria_bruta.replace("minecraft:", "")
                cat_traduzida = TRADUCOES_CATEGORIA.get(categoria_limpa, categoria_limpa.title())
                
                for metrica_bruta, valor in metricas.items():
                    metrica_limpa = metrica_bruta.replace("minecraft:", "")
                    
                    if "time" in metrica_limpa or "minute" in metrica_limpa:
                         valor = round(valor / 72000, 2)
                    elif "one_cm" in metrica_limpa:
                         metrica_limpa = metrica_limpa.replace("one_cm", "meters")
                         valor = round(valor / 100, 2)

                    registros.append({
                        "Jogador": nome_jogador,
                        "Categoria": cat_traduzida,
                        "Métrica_ID": metrica_limpa,
                        "Métrica": formatar_nome_metrica(metrica_limpa),
                        "Valor": valor
                    })
                    
    return pd.DataFrame(registros)

df = carregar_dados()

if df.empty:
    st.error("Nenhum dado encontrado. Verifique o mapeamento da pasta de estatísticas.")
    st.stop()

# ---- BARRA LATERAL ----
st.sidebar.title("🎮 Painel de Controle")
st.sidebar.markdown("---")

lista_jogadores = ["Visão Geral do Servidor"] + sorted(df["Jogador"].unique().tolist())
jogador_selecionado = st.sidebar.radio("Selecione a Visão:", lista_jogadores)

# ---- ÁREA PRINCIPAL ----
st.title("⛏️ Telemetria do Servidor")

if jogador_selecionado == "Visão Geral do Servidor":
    st.markdown("### Estatísticas Globais")
    
    # Abas temáticas globais
    aba1, aba2, aba3 = st.tabs(["🏆 Top Blocos Quebrados", "⚔️ Animais/Mobs Mais Eliminados", "⏱️ Tempo Jogado"])
    
    with aba1:
        st.subheader("Blocos mais destruídos em todo o servidor")
        df_mined = df[df["Categoria"] == "Blocos Minerados"]
        if not df_mined.empty:
            top_blocos = df_mined.groupby("Métrica")["Valor"].sum().sort_values(ascending=False).head(15)
            st.bar_chart(top_blocos)
        else:
            st.info("Nenhum bloco minerado registado ainda.")

    with aba2:
        st.subheader("As criaturas mais caçadas")
        df_killed = df[df["Categoria"] == "Criaturas Eliminadas"]
        if not df_killed.empty:
            top_mobs = df_killed.groupby("Métrica")["Valor"].sum().sort_values(ascending=False).head(15)
            st.bar_chart(top_mobs)
        else:
            st.info("Nenhuma eliminação registada ainda.")
            
    with aba3:
        st.subheader("Ranking de Tempo de Jogo (Horas)")
        df_tempo = df[df["Métrica_ID"] == "play_time"]
        if not df_tempo.empty:
            top_tempo = df_tempo.groupby("Jogador")["Valor"].sum().sort_values(ascending=False)
            st.bar_chart(top_tempo)

else:
    # ---- PÁGINA ESPECÍFICA DO JOGADOR ----
    st.markdown(f"### Perfil do Jogador: **{jogador_selecionado}**")
    df_jogador = df[df["Jogador"] == jogador_selecionado]
    
    # Extrair métricas principais para exibição numérica
    def obter_valor_jogador(metrica_id):
        try:
            return df_jogador[df_jogador["Métrica_ID"] == metrica_id]["Valor"].values[0]
        except IndexError:
            return 0

    tempo_jogado = obter_valor_jogador("play_time")
    mortes = obter_valor_jogador("deaths")
    mobs_mortos = obter_valor_jogador("mob_kills")
    distancia = obter_valor_jogador("walk_meters") # já limpo pelo replace one_cm

    # Cartões de Métricas (apenas números visuais)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Tempo Jogado", value=f"{tempo_jogado:.2f} h")
    col2.metric(label="Total de Mortes", value=int(mortes))
    col3.metric(label="Mobs Eliminados", value=int(mobs_mortos))
    col4.metric(label="Distância Andada", value=f"{distancia/1000:.2f} km")
    
    st.markdown("---")
    
    # Abas temáticas do jogador
    aba_jog1, aba_jog2 = st.tabs(["Atividade e Mineração", "Combate e Criação"])
    
    with aba_jog1:
        col_grafico1, col_grafico2 = st.columns(2)
        with col_grafico1:
            st.markdown("**Top 10 Blocos Minerados**")
            df_mined_jog = df_jogador[df_jogador["Categoria"] == "Blocos Minerados"]
            if not df_mined_jog.empty:
                top_blocos_jog = df_mined_jog.sort_values(by="Valor", ascending=False).head(10)
                st.bar_chart(top_blocos_jog.set_index("Métrica")["Valor"])
                
        with col_grafico2:
            st.markdown("**Ações Frequentes (Geral)**")
            df_geral_jog = df_jogador[df_jogador["Categoria"] == "Estatísticas Gerais"]
            # Exclui métricas grandes como tempo e distância para não estragar a escala do gráfico
            df_geral_jog = df_geral_jog[~df_geral_jog["Métrica_ID"].isin(["play_time", "walk_meters", "crouch_meters", "sprint_meters"])]
            if not df_geral_jog.empty:
                top_geral = df_geral_jog.sort_values(by="Valor", ascending=False).head(10)
                st.bar_chart(top_geral.set_index("Métrica")["Valor"])

    with aba_jog2:
        col_grafico3, col_grafico4 = st.columns(2)
        with col_grafico3:
            st.markdown("**Top 10 Criaturas Eliminadas**")
            df_kill_jog = df_jogador[df_jogador["Categoria"] == "Criaturas Eliminadas"]
            if not df_kill_jog.empty:
                top_kill_jog = df_kill_jog.sort_values(by="Valor", ascending=False).head(10)
                st.bar_chart(top_kill_jog.set_index("Métrica")["Valor"])
                
        with col_grafico4:
            st.markdown("**Top 10 Itens Criados (Crafted)**")
            df_craft_jog = df_jogador[df_jogador["Categoria"] == "Itens Criados"]
            if not df_craft_jog.empty:
                top_craft_jog = df_craft_jog.sort_values(by="Valor", ascending=False).head(10)
                st.bar_chart(top_craft_jog.set_index("Métrica")["Valor"])