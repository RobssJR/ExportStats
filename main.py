import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Minecraft Server Telemetry", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=5000, key="data_refresh")

SERVER_DIR = "../" 
STATS_DIR = os.path.join(SERVER_DIR, "world/players/stats")
USERCACHE = os.path.join(SERVER_DIR, "usercache.json")

def carregar_traducoes():
    caminho = "traducoes.json"
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"categorias": {}, "metricas": {}}

traducoes = carregar_traducoes()
TRADUCOES_CATEGORIA = traducoes.get("categorias", {})
TRADUCOES_METRICA = traducoes.get("metricas", {})

def formatar_nome_metrica(metrica):
    if metrica in TRADUCOES_METRICA:
        return TRADUCOES_METRICA[metrica]
    return metrica.replace("_", " ").title()

@st.cache_data(ttl=4)
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

# --- FUNÇÃO DE GRÁFICO DE PIZZA LIMPO ---
def exibir_grafico_pizza(serie_dados):
    if serie_dados.empty:
        st.info("Nenhum dado registado ainda.")
        return
        
    # Limita aos top 7 para não encavalar o texto no gráfico
    top_dados = serie_dados.head(7).reset_index()
    top_dados.columns = ['Métrica', 'Valor']
    
    # Cria a pizza com um buraco no meio (Donut) para um visual mais moderno
    fig = px.pie(top_dados, values='Valor', names='Métrica', hole=0.4)
    
    # Define que o texto fica dentro das fatias e oculta a legenda lateral
    fig.update_traces(textposition='inside', textinfo='percent+label', showlegend=False)
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
    
    st.plotly_chart(fig, use_container_width=True)


df = carregar_dados()

if df.empty:
    st.error("Nenhum dado encontrado. Verifique o mapeamento da pasta de estatísticas.")
    st.stop()

st.sidebar.title("🎮 Painel de Controlo")
st.sidebar.markdown("---")

lista_jogadores = ["Visão Geral do Servidor"] + sorted(df["Jogador"].unique().tolist())
jogador_selecionado = st.sidebar.radio("Selecione a Visão:", lista_jogadores)

st.title("⛏️ Telemetria do Servidor")

if jogador_selecionado == "Visão Geral do Servidor":
    st.markdown("### Estatísticas Globais")
    
    aba1, aba2, aba3 = st.tabs(["🏆 Top Blocos Quebrados", "⚔️ Animais/Mobs Mais Eliminados", "⏱️ Tempo Jogado"])
    
    with aba1:
        st.subheader("Blocos mais destruídos em todo o servidor")
        df_mined = df[df["Categoria"] == "Blocos Minerados"]
        if not df_mined.empty:
            top_blocos = df_mined.groupby("Métrica")["Valor"].sum().sort_values(ascending=False)
            exibir_grafico_pizza(top_blocos)

    with aba2:
        st.subheader("As criaturas mais caçadas")
        df_killed = df[df["Categoria"] == "Criaturas Eliminadas"]
        if not df_killed.empty:
            top_mobs = df_killed.groupby("Métrica")["Valor"].sum().sort_values(ascending=False)
            exibir_grafico_pizza(top_mobs)
            
    with aba3:
        st.subheader("Ranking de Tempo de Jogo (Horas)")
        df_tempo = df[df["Métrica_ID"] == "play_time"]
        if not df_tempo.empty:
            top_tempo = df_tempo.groupby("Jogador")["Valor"].sum().sort_values(ascending=False)
            exibir_grafico_pizza(top_tempo)

else:
    # ---- PÁGINA ESPECÍFICA DO JOGADOR ----
    st.markdown(f"### 👤 Perfil do Jogador: **{jogador_selecionado}**")
    df_jogador = df[df["Jogador"] == jogador_selecionado]
    
    def obter_valor_jogador(metrica_id):
        try:
            return df_jogador[df_jogador["Métrica_ID"] == metrica_id]["Valor"].values[0]
        except IndexError:
            return 0

    # Cartões de Métricas Principais
    tempo_jogado = obter_valor_jogador("play_time")
    mortes = obter_valor_jogador("deaths")
    mobs_mortos = obter_valor_jogador("mob_kills")
    distancia = obter_valor_jogador("walk_meters")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Tempo Jogado", value=f"{tempo_jogado:.2f} h")
    col2.metric(label="Total de Mortes", value=int(mortes))
    col3.metric(label="Mobs Eliminados", value=int(mobs_mortos))
    col4.metric(label="Distância Andada", value=f"{distancia/1000:.2f} km")
    
    st.markdown("---")
    st.subheader("📊 Estatísticas Detalhadas")
    
    # Levanta todas as categorias existentes para este jogador específico
    categorias_jogador = df_jogador["Categoria"].unique().tolist()
    
    # Força "Estatísticas Gerais" a ser sempre a primeira aba, se existir
    if "Estatísticas Gerais" in categorias_jogador:
        categorias_jogador.remove("Estatísticas Gerais")
        categorias_jogador.insert(0, "Estatísticas Gerais")

    # Mapeamento de ícones para as abas
    icones_cat = {
        "Estatísticas Gerais": "⚙️",
        "Blocos Minerados": "⛏️",
        "Criaturas Eliminadas": "⚔️",
        "Itens Criados": "🛠️",
        "Itens Apanhados": "🎒",
        "Itens Caídos": "🗑️"
    }
    
    # Gera os títulos das abas com ícones dinamicamente
    titulos_abas = [f"{icones_cat.get(cat, '📁')} {cat}" for cat in categorias_jogador]
    abas = st.tabs(titulos_abas)

    # Preenche cada aba com todas as métricas correspondentes
    for i, cat in enumerate(categorias_jogador):
        with abas[i]:
            df_cat = df_jogador[df_jogador["Categoria"] == cat]
            
            # Divide a aba em duas colunas (Gráfico à esquerda, Tabela completa à direita)
            col_grafico, col_tabela = st.columns([1, 1.2])
            
            with col_grafico:
                st.markdown(f"**Top Destaques**")
                df_grafico = df_cat
                
                # Na aba geral, remove as métricas de tempo/distância para não esmagar o gráfico de pizza
                if cat == "Estatísticas Gerais":
                    df_grafico = df_cat[~df_cat["Métrica_ID"].isin(["play_time", "walk_meters", "crouch_meters", "sprint_meters", "time_since_death", "time_since_rest"])]
                
                if not df_grafico.empty:
                    top_grafico = df_grafico.groupby("Métrica")["Valor"].sum().sort_values(ascending=False)
                    exibir_grafico_pizza(top_grafico)
                else:
                    st.info("Gráfico não disponível para estes dados.")

            with col_tabela:
                st.markdown(f"**Lista Completa**")
                # Prepara o DataFrame com 100% dos dados ordenados do maior para o menor
                df_tabela = df_cat[["Métrica", "Valor"]].sort_values(by="Valor", ascending=False).reset_index(drop=True)
                
                # Renderiza a tabela com altura fixa para criar uma barra de rolagem interna limpa
                st.dataframe(
                    df_tabela,
                    use_container_width=True,
                    hide_index=True,
                    height=350,
                    column_config={
                        "Métrica": st.column_config.TextColumn("Métrica / Item"),
                        "Valor": st.column_config.NumberColumn("Quantidade", format="%g")
                    }
                )