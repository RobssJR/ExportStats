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
    st.markdown(f"### 👤 Perfil do Jogador: **{jogador_selecionado}**")
    df_jogador = df[df["Jogador"] == jogador_selecionado]
    
    # ---- BARRA LATERAL (Filtros de Inventário) ----
    st.sidebar.markdown("### 🔍 Filtros de Busca")
    termo_busca = st.sidebar.text_input("Buscar item/bloco...", "").lower()
    
    # ---- CSS CUSTOMIZADO (Estilo Minecraft GUI com Emojis) ----
    st.markdown("""
        <style>
        .mc-container {
            background-color: #1e1e1e;
            padding: 15px;
            border: 2px solid #3a3a3a;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .mc-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(48px, 1fr));
            gap: 4px;
        }
        .mc-slot {
            width: 48px;
            height: 48px;
            background-color: #8b8b8b;
            border: 2px solid;
            border-color: #373737 #fff #fff #373737;
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 24px; /* Tamanho do Emoji */
            user-select: none;
        }
        .mc-slot:hover {
            background-color: #a8a8a8;
            cursor: crosshair;
        }
        .mc-badge {
            position: absolute;
            bottom: 0;
            right: 2px;
            color: white;
            font-size: 12px;
            font-weight: bold;
            font-family: monospace;
            text-shadow: 2px 2px 0 #3f3f3f, -1px -1px 0 #3f3f3f, 1px -1px 0 #3f3f3f, -1px 1px 0 #3f3f3f, 1px 1px 0 #3f3f3f;
        }
        .mc-tooltip {
            visibility: hidden;
            background-color: #110211;
            color: #55FF55;
            text-align: center;
            padding: 5px 10px;
            border: 2px solid #2a042a;
            border-radius: 3px;
            position: absolute;
            z-index: 100;
            bottom: 110%;
            left: 50%;
            transform: translateX(-50%);
            white-space: nowrap;
            font-family: monospace;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
        }
        .mc-slot:hover .mc-tooltip {
            visibility: visible;
        }
        .categoria-titulo {
            color: #FFAA00;
            font-family: monospace;
            margin-bottom: 10px;
            margin-top: 5px;
            text-shadow: 1px 1px 0 #3f3f3f;
        }
        </style>
    """, unsafe_allow_html=True)

    # ---- SISTEMA DE EMOJIS ----
    def classificar_emoji(item_id, categoria):
        item = str(item_id).lower()
        
        # Mobs e Entidades
        if "zombie" in item: return "🧟"
        if "skeleton" in item: return "💀"
        if "spider" in item: return "🕷️"
        if "creeper" in item: return "💥"
        if "pig" in item or "hoglin" in item: return "🐷"
        if "cow" in item: return "🐄"
        if "sheep" in item: return "🐑"
        if "chicken" in item: return "🐔"
        if "villager" in item: return "🧔"
        if "dragon" in item: return "🐉"
        
        # Ferramentas e Armas
        if "sword" in item: return "🗡️"
        if "pickaxe" in item: return "⛏️"
        if "axe" in item: return "🪓"
        if "hoe" in item: return "⛏️"
        if "shovel" in item: return "🪏"
        if "bow" in item: return "🏹"
        if "shield" in item: return "🛡️"
        if "helmet" in item or "chestplate" in item or "leggings" in item or "boots" in item: return "👕"
        
        # Blocos Naturais e Minérios
        if "wood" in item or "log" in item or "planks" in item: return "🪵"
        if "stone" in item or "cobblestone" in item or "andesite" in item or "diorite" in item: return "🪨"
        if "dirt" in item or "grass" in item or "sand" in item: return "🟫"
        if "leaves" in item or "sapling" in item: return "🌿"
        if "diamond" in item or "emerald" in item or "lapis" in item: return "💎"
        if "gold" in item or "iron" in item or "copper" in item: return "🪙"
        if "coal" in item: return "⬛"
        
        # Itens Diversos
        if "apple" in item or "bread" in item or "beef" in item or "porkchop" in item: return "🥩"
        if "potion" in item or "bottle" in item: return "🧪"
        if "bucket" in item: return "🪣"
        if "boat" in item: return "🛶"
        if "bed" in item: return "🛏️"
        if "door" in item: return "🚪"
        
        # Fallbacks (Ícones padrão baseados na categoria)
        if categoria == "Blocos Minerados": return "📦"
        if categoria == "Itens Criados": return "🛠️"
        if categoria == "Criaturas Eliminadas": return "🩸"
        return "❓"

    def renderizar_grade_inventario(df_dados, titulo):
        if termo_busca:
            df_dados = df_dados[df_dados["Métrica"].str.lower().str.contains(termo_busca) | df_dados["Métrica_ID"].str.lower().str.contains(termo_busca)]
            
        if df_dados.empty:
            return

        html = f'<div class="mc-container"><h4 class="categoria-titulo">{titulo}</h4><div class="mc-grid">'
        
        for _, row in df_dados.iterrows():
            id_item = row["Métrica_ID"]
            nome_limpo = row["Métrica"]
            categoria = row["Categoria"]
            valor = int(row["Valor"]) if row["Valor"].is_integer() else f"{row['Valor']:.1f}"
            
            # Obtém o emoji através da função
            icone_emoji = classificar_emoji(id_item, categoria)
            
            html += f"""
            <div class="mc-slot">
                {icone_emoji}
                <div class="mc-badge">{valor}</div>
                <span class="mc-tooltip">{nome_limpo}<br><span style="color:#AAAAAA">{valor}x</span></span>
            </div>
            """
            
        html += '</div></div>'
        st.markdown(html, unsafe_allow_html=True)

    st.subheader("🎒 Inventário de Estatísticas")
    
    df_mined = df_jogador[df_jogador["Categoria"] == "Blocos Minerados"].sort_values(by="Valor", ascending=False)
    renderizar_grade_inventario(df_mined, "🧊 Blocos Minerados (Natural & Building Blocks)")
    
    df_crafted = df_jogador[df_jogador["Categoria"] == "Itens Criados"].sort_values(by="Valor", ascending=False)
    renderizar_grade_inventario(df_crafted, "🛠️ Itens Criados (Functional Blocks & Items)")
    
    df_killed = df_jogador[df_jogador["Categoria"] == "Criaturas Eliminadas"].sort_values(by="Valor", ascending=False)
    renderizar_grade_inventario(df_killed, "⚔️ Criaturas Eliminadas")