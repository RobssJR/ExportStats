import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import json
import os
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIGURAÇÃO INICIAL E CSS RESPONSIVO
# ==========================================
st.set_page_config(page_title="Minecraft Server Telemetry", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=5000, key="data_refresh")

st.markdown("""
    <style>
    [data-testid="stMetricLabel"] {
        font-size: 15px !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.7rem !important;
    }
    .stCodeBlock {
        width: 100% !important;
    }
    @media (max-width: 768px) {
        [data-testid="stMetricValue"] {
            font-size: 1.3rem !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 13px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

SERVER_DIR = "../" 
STATS_DIR = os.path.join(SERVER_DIR, "world/players/stats")
USERCACHE = os.path.join(SERVER_DIR, "usercache.json")

# ==========================================
# LISTAS DE RASTREIO E DICIONÁRIOS
# ==========================================
HOSTILE_MOBS = [
    "zombie", "skeleton", "creeper", "spider", "cave_spider", "enderman", 
    "witch", "slime", "magma_cube", "silverfish", "zombie_villager", 
    "phantom", "drowned", "husk", "stray", "vindicator", "evoker", 
    "pillager", "ravager", "guardian", "elder_guardian", "shulker", 
    "endermite", "blaze", "ghast", "wither_skeleton", "hoglin", "zoglin", 
    "piglin_brute", "warden", "wither", "ender_dragon"
]

PASSIVE_MOBS = [
    "pig", "cow", "sheep", "chicken", "horse", "donkey", "mule", 
    "llama", "trader_llama", "cat", "ocelot", "wolf", "fox", "panda", 
    "polar_bear", "rabbit", "turtle", "parrot", "bee", "strider", 
    "axolotl", "goat", "frog", "tadpole", "allay", "camel", "sniffer", 
    "villager", "wandering_trader", "iron_golem", "snow_golem", "bat", "squid", "glow_squid", "dolphin"
]

FOOD_ITEMS = [
    "apple", "golden_apple", "enchanted_golden_apple", "melon_slice", 
    "sweet_berries", "glow_berries", "chorus_fruit", "carrot", 
    "golden_carrot", "potato", "baked_potato", "poisonous_potato", 
    "beetroot", "dried_kelp", "beef", "cooked_beef", "porkchop", 
    "cooked_porkchop", "mutton", "cooked_mutton", "chicken", 
    "cooked_chicken", "rabbit", "cooked_rabbit", "cod", "cooked_cod", 
    "salmon", "cooked_salmon", "tropical_fish", "pufferfish", 
    "bread", "cookie", "cake", "pumpkin_pie", "mushroom_stew", 
    "beetroot_soup", "rabbit_stew", "suspicious_stew", "honey_bottle", 
    "potion"
]

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
        
    nomes_dist = {
        "climb_one_cm": "Distance Climbed",
        "crouch_one_cm": "Distance Crouched",
        "fall_one_cm": "Distance Fallen",
        "fly_one_cm": "Distance Flown",
        "sprint_one_cm": "Distance Sprinted",
        "swim_one_cm": "Distance Swum",
        "walk_one_cm": "Distance Walked",
        "walk_on_water_one_cm": "Distance Walked on Water",
        "walk_under_water_one_cm": "Distance Walked under Water",
        "boat_one_cm": "Distance by Boat",
        "aviate_one_cm": "Distance by Elytra",
        "horse_one_cm": "Distance by Horse",
        "minecart_one_cm": "Distance by Minecart",
        "pig_one_cm": "Distance by Pig",
        "strider_one_cm": "Distance by Strider"
    }
    
    if metrica in nomes_dist:
        return f"{nomes_dist[metrica]} (km)"
    elif metrica == "jump":
        return "Jumps"
    elif "one_cm" in metrica:
        return metrica.replace("_one_cm", "").replace("_", " ").title() + " Distance (km)"
    elif "time" in metrica:
        return metrica.replace("_", " ").title() + " (h)"
        
    return metrica.replace("_", " ").title()

def classificar_emoji(item_id, categoria):
    item = str(item_id).lower()
    
    if categoria == "Comida":
        if "apple" in item: return "🍎"
        if "melon" in item: return "🍉"
        if "carrot" in item: return "🥕"
        if "potato" in item: return "🥔"
        if "bread" in item: return "🍞"
        if "cookie" in item: return "🍪"
        if "cake" in item: return "🎂"
        if "pie" in item: return "🥧"
        if "fish" in item or "salmon" in item or "cod" in item: return "🐟"
        if "beef" in item or "porkchop" in item or "mutton" in item or "chicken" in item or "rabbit" in item: return "🥩"
        if "stew" in item or "soup" in item: return "🥣"
        if "berries" in item: return "🫐"
        if "kelp" in item: return "🌿"
        if "honey" in item or "potion" in item: return "🍯"
        return "🍎"

    if "jump" in item: return "🦘"
    if "time" in item: return "⏱️"
    if "boat" in item: return "🛶"
    if "horse" in item: return "🐎"
    if "aviate" in item or "elytra" in item or "fly" in item: return "🚀"
    if "swim" in item or "water" in item: return "🏊"
    if "climb" in item: return "🧗"
    if "fall" in item: return "📉"
    if "walk" in item or "sprint" in item or "crouch" in item or "sneak" in item or "one_cm" in item: return "👟"

    if "deaths" in item: return "☠️"
    if "mob_kills" in item: return "⚔️"
    if "player_kills" in item: return "🤺"
    if "zombie" in item: return "🧟"
    if "skeleton" in item or "wither" in item: return "💀"
    if "spider" in item: return "🕷️"
    if "creeper" in item: return "💥"
    if "pig" in item or "hoglin" in item: return "🐷"
    if "cow" in item: return "🐄"
    if "sheep" in item: return "🐑"
    if "chicken" in item: return "🐔"
    if "villager" in item or "pillager" in item or "evoker" in item: return "🧔"
    if "dragon" in item: return "🐉"
    if "blaze" in item or "ghast" in item or "magma" in item: return "🔥"
    if "slime" in item: return "🟩"
    if "enderman" in item or "endermite" in item: return "👁️"
    if "guardian" in item: return "🐡"
    
    if "sword" in item: return "🗡️"
    if "pickaxe" in item: return "⛏️"
    if "axe" in item: return "🪓"
    if "hoe" in item: return "⛏️"
    if "shovel" in item: return "🪏"
    if "bow" in item: return "🏹"
    if "shield" in item: return "🛡️"
    if "helmet" in item or "chestplate" in item or "leggings" in item or "boots" in item: return "👕"
    if "wood" in item or "log" in item or "planks" in item: return "🪵"
    if "stone" in item or "cobblestone" in item or "andesite" in item or "diorite" in item: return "🪨"
    if "dirt" in item or "grass" in item or "sand" in item: return "🟫"
    if "leaves" in item or "sapling" in item: return "🌿"
    if "diamond" in item or "emerald" in item or "lapis" in item: return "💎"
    if "gold" in item or "iron" in item or "copper" in item: return "🪙"
    if "coal" in item: return "⬛"
    
    if categoria == "Criaturas Hostis": return "👾"
    if categoria == "Criaturas Eliminadas": return "🩸"
    if categoria == "Estatísticas Gerais": return "📊"
    if categoria == "Blocos Minerados": return "📦"
    if categoria == "Itens Criados": return "🛠️"
    return "📦"

@st.cache_data(ttl=4)
def carregar_dados():
    nomes = {}
    if os.path.exists(USERCACHE):
        with open(USERCACHE, "r") as f:
            try:
                cache = json.load(f)
                nomes = {jogador["uuid"]: jogador["name"] for jogador in cache}
            except json.JSONDecodeError: pass

    registros = []
    if not os.path.exists(STATS_DIR): return pd.DataFrame() 

    for arquivo in os.listdir(STATS_DIR):
        if arquivo.endswith(".json"):
            uuid = arquivo.replace(".json", "")
            nome_jogador = nomes.get(uuid, f"Desconhecido_{uuid[:8]}")
            caminho_arquivo = os.path.join(STATS_DIR, arquivo)
            
            with open(caminho_arquivo, "r") as f:
                try: dados = json.load(f)
                except json.JSONDecodeError: continue
            
            stats_nativas = dados.get("stats", {})
            for categoria_bruta, metricas in stats_nativas.items():
                categoria_limpa = categoria_bruta.replace("minecraft:", "")
                cat_traduzida = TRADUCOES_CATEGORIA.get(categoria_limpa, categoria_limpa.title())
                
                for metrica_bruta, valor in metricas.items():
                    metrica_limpa = metrica_bruta.replace("minecraft:", "")
                    
                    if metrica_limpa == "jump":
                        pass
                    elif "time" in metrica_limpa or "minute" in metrica_limpa:
                         valor = round(valor / 72000, 2)
                    elif "one_cm" in metrica_limpa:
                         valor = round(valor / 100000, 2)

                    registros.append({
                        "Jogador": nome_jogador,
                        "Categoria": cat_traduzida,
                        "Categoria_Original": categoria_limpa,
                        "Métrica_ID": metrica_limpa,
                        "Métrica": formatar_nome_metrica(metrica_limpa),
                        "Valor": valor
                    })
    return pd.DataFrame(registros)

df = carregar_dados()
if df.empty:
    st.error("Nenhum dado encontrado. Verifique a pasta de estatísticas.")
    st.stop()

# ==========================================
# BARRA LATERAL
# ==========================================
st.sidebar.title("🎮 Painel de Controlo")

lista_jogadores = ["Visão Geral do Servidor"] + sorted(df["Jogador"].unique().tolist())
jogador_selecionado = st.sidebar.selectbox("👤 Selecionar Visão", lista_jogadores)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗂️ Filtros")

opcoes_menu = {
    "📄 General": "Estatísticas Gerais",
    "🧭 Items": "Agrupamento_Itens",
    "🟫 Blocks": "Blocos Minerados",
    "🐷 Mobs (Passivos)": "Criaturas Eliminadas_Passivas", 
    "🧟 Hostile Mobs": "Criaturas Hostis",
    "🍎 Food & Drinks": "Comida"
}

categoria_selecionada_visual = st.sidebar.selectbox("Menu", list(opcoes_menu.keys()))
ocultar_zerados = st.sidebar.checkbox("Ocultar itens não encontrados", value=True)

# Novo filtro de ordenação
ordem_selecionada = st.sidebar.selectbox(
    "Ordenar por:",
    ["Maior Quantidade", "Menor Quantidade", "Alfabético (A-Z)"]
)

termo_busca = st.sidebar.text_input("Pesquisar na categoria...", "").lower()

def aplicar_ordenacao(df_ordenar, coluna_valor="Valor"):
    if df_ordenar.empty: return df_ordenar
    if ordem_selecionada == "Maior Quantidade":
        return df_ordenar.sort_values(by=coluna_valor, ascending=False)
    elif ordem_selecionada == "Menor Quantidade":
        return df_ordenar.sort_values(by=coluna_valor, ascending=True)
    else:
        return df_ordenar.sort_values(by="Métrica", ascending=True)

# ==========================================
# MOTORES DE RENDERIZAÇÃO
# ==========================================
def exibir_kpis_detalhados(df_dados):
    kpi_kills = df_dados[df_dados["Métrica_ID"] == "mob_kills"]["Valor"].sum()
    kpi_deaths = df_dados[df_dados["Métrica_ID"] == "deaths"]["Valor"].sum()
    kpi_player_kills = df_dados[df_dados["Métrica_ID"] == "player_kills"]["Valor"].sum()
    kd_ratio = round(kpi_kills / kpi_deaths, 2) if kpi_deaths > 0 else float(kpi_kills)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("⚔️ Mobs", int(kpi_kills))
    with col2: st.metric("☠️ Mortes", int(kpi_deaths))
    with col3: st.metric("📊 K/D", kd_ratio)
    with col4: st.metric("🤺 PvP", int(kpi_player_kills))
    st.divider()

def renderizar_grafico_horizontal(df_grafico, coluna_valor, titulo):
    if df_grafico.empty: return
    df_top = df_grafico.sort_values(coluna_valor, ascending=False).head(15)
    df_top = df_top.sort_values(coluna_valor, ascending=True)
    
    if df_top[coluna_valor].sum() == 0: return 
    
    altura_dinamica = max(300, len(df_top) * 45)
    
    fig = px.bar(df_top, x=coluna_valor, y="Métrica", orientation='h', text=coluna_valor, title=titulo)
    fig.update_layout(
        yaxis_title=None, xaxis_title=None, margin=dict(l=0, r=0, t=50, b=10), 
        height=altura_dinamica, font=dict(size=14), title_font=dict(size=20, color='#FFAA00')
    )
    fig.update_traces(textposition='outside', textfont_size=14, marker_color='#55FF55')
    st.plotly_chart(fig, use_container_width=True)

def renderizar_grafico_comparativo_jogadores(df_origem, metrica_filtro_id, titulo):
    df_comp = df_origem[df_origem["Métrica_ID"] == metrica_filtro_id]
    if df_comp.empty: return
    
    df_soma = df_comp.groupby("Jogador", as_index=False)["Valor"].sum()
    df_soma = df_soma.sort_values("Valor", ascending=True)
    
    if df_soma["Valor"].sum() == 0: return
    
    fig = px.bar(df_soma, x="Valor", y="Jogador", orientation='h', text="Valor", title=f"🏆 Comparativo entre Jogadores: {titulo}")
    fig.update_layout(
        yaxis_title=None, xaxis_title=None, margin=dict(l=0, r=0, t=50, b=10), 
        height=300, font=dict(size=14), title_font=dict(size=18, color='#FFAA00')
    )
    fig.update_traces(textposition='outside', textfont_size=14, marker_color='#FFAAFF')
    st.plotly_chart(fig, use_container_width=True)

def renderizar_grade_nativa(df_dados, titulo, aplicar_filtro_zeros=True, mostrar_grafico=True):
    if aplicar_filtro_zeros and ocultar_zerados:
        df_dados = df_dados[df_dados["Valor"] > 0]
    if termo_busca:
        df_dados = df_dados[df_dados["Métrica"].str.lower().str.contains(termo_busca) | df_dados["Métrica_ID"].str.lower().str.contains(termo_busca)]
    
    df_dados = aplicar_ordenacao(df_dados, coluna_valor="Valor")

    if df_dados.empty:
        st.info("Nenhum dado para mostrar.")
        return

    if mostrar_grafico:
        renderizar_grafico_horizontal(df_dados, "Valor", f"Top 15 {titulo.replace('Registadas', '')}")
        
    st.markdown(f"#### {titulo}")
    
    colunas_por_linha = 4
    itens = df_dados.to_dict('records')
    for i in range(0, len(itens), colunas_por_linha):
        cols = st.columns(colunas_por_linha)
        pedaco = itens[i:i + colunas_por_linha]
        for j, item in enumerate(pedaco):
            with cols[j]:
                icone = classificar_emoji(item["Métrica_ID"], item.get("Categoria", ""))
                val = item["Valor"]
                valor = val if isinstance(val, float) else (int(val) if isinstance(val, int) or val.is_integer() else val)
                
                if isinstance(valor, float):
                    valor_str = f"{valor:.2f}"
                else:
                    valor_str = str(valor)

                if val > 0:
                    st.metric(label=f"{icone} {item['Métrica']}", value=valor_str)
                else:
                    estilo = f"<div style='opacity: 0.3; filter: grayscale(100%); margin-bottom: 1rem;'><p style='font-size: 15px; margin-bottom: -5px; font-weight: 600;'>{icone} {item['Métrica']}</p><h2 style='font-size: 1.7rem; margin-top: 0; font-weight: normal;'>0</h2></div>"
                    st.markdown(estilo, unsafe_allow_html=True)
    st.divider()

# ==========================================
# CONJUNTO DE DADOS (VISÃO GERAL VS JOGADOR)
# ==========================================
if jogador_selecionado == "Visão Geral do Servidor":
    st.title("🌐 Visão Geral do Servidor")
    st.markdown("### 🗺️ Mapa ao Vivo")
    components.iframe("http://lucas-server:25566/#world:1006:60:-697:88:0:0:0:1:flat", height=450, scrolling=True)
    st.divider()
    
    exibir_kpis_detalhados(df)
    
    # Exclui métricas acumuladas/pontuais (como time_since_death) na Visão Geral do Servidor
    metricas_excluir_global = ["time_since_death", "time_since_rest"]
    df_sem_acumulados = df[~df["Métrica_ID"].isin(metricas_excluir_global)]
    
    df_ativo = df_sem_acumulados.groupby(["Categoria_Original", "Categoria", "Métrica_ID", "Métrica"], as_index=False)["Valor"].sum()
    eh_visao_geral = True
else:
    st.title(f"👤 {jogador_selecionado}")
    df_ativo = df[df["Jogador"] == jogador_selecionado]
    eh_visao_geral = False

# ==========================================
# PROCESSAMENTO POR MENU
# ==========================================
st.subheader(f"{categoria_selecionada_visual.split(' ')[0]} {categoria_selecionada_visual.split(' ', 1)[1]}")

# 1. Itens Consolidados
if categoria_selecionada_visual == "🧭 Items":
    df_itens_raw = df_ativo[~df_ativo["Categoria_Original"].isin(["custom", "killed", "killed_by"])]
    dados_agrupados = {}
    for _, row in df_itens_raw.iterrows():
        m_id = row["Métrica_ID"]
        cat = row["Categoria_Original"]
        val = row["Valor"]
        if m_id not in dados_agrupados:
            dados_agrupados[m_id] = {"Métrica_ID": m_id, "Métrica": row["Métrica"], "Criado": 0, "Usado": 0, "Minerado": 0, "Quebrado": 0, "Apanhado": 0, "Caído": 0}
        
        if cat == "crafted": dados_agrupados[m_id]["Criado"] = val
        elif cat == "used": dados_agrupados[m_id]["Usado"] = val
        elif cat == "mined": dados_agrupados[m_id]["Minerado"] = val
        elif cat == "broken": dados_agrupados[m_id]["Quebrado"] = val
        elif cat == "picked_up": dados_agrupados[m_id]["Apanhado"] = val
        elif cat == "dropped": dados_agrupados[m_id]["Caído"] = val

    df_categoria = pd.DataFrame(list(dados_agrupados.values()))
    if not df_categoria.empty:
        df_categoria['Total_Interacoes'] = df_categoria['Criado'] + df_categoria['Usado'] + df_categoria['Minerado'] + df_categoria['Quebrado'] + df_categoria['Apanhado'] + df_categoria['Caído']
        
    if ocultar_zerados: df_categoria = df_categoria[df_categoria['Total_Interacoes'] > 0]
    
    df_categoria = aplicar_ordenacao(df_categoria, coluna_valor="Total_Interacoes")
    
    renderizar_grafico_horizontal(df_categoria, "Total_Interacoes", "Top 15 Itens Mais Interagidos")
    st.markdown("#### 📦 Registo Completo de Itens")
    
    colunas_por_linha = 3
    itens = df_categoria.to_dict('records')
    for i in range(0, len(itens), colunas_por_linha):
        cols = st.columns(colunas_por_linha)
        pedaco = itens[i:i + colunas_por_linha]
        for j, item in enumerate(pedaco):
            with cols[j]:
                icone = classificar_emoji(item["Métrica_ID"], "Itens")
                st.markdown(f"**{icone} {item['Métrica']}**")
                st.caption(f"`minecraft:{item['Métrica_ID']}`")
                st.code(
                    f"Times Crafted: {int(item['Criado'])}\n"
                    f"Times Used:    {int(item['Usado'])}\n"
                    f"Times Broken:  {int(item['Minerado'] + item['Quebrado'])}\n"
                    f"Picked Up:     {int(item['Apanhado'])}\n"
                    f"Dropped:       {int(item['Caído'])}", language="text"
                )

# 2. Mobs Hostis e Passivos (Pokédex Completa)
elif categoria_selecionada_visual in ["🧟 Hostile Mobs", "🐷 Mobs (Passivos)"]:
    if not eh_visao_geral:
        exibir_kpis_detalhados(df_ativo)
        
    df_mobs_raw = df_ativo[df_ativo["Categoria_Original"].isin(["killed", "killed_by"])]
    
    if categoria_selecionada_visual == "🧟 Hostile Mobs":
        lista_alvo = HOSTILE_MOBS
    else:
        lista_alvo = PASSIVE_MOBS
        
    dados_mobs = {}
    for mob in lista_alvo:
        dados_mobs[mob] = {"Métrica_ID": mob, "Métrica": formatar_nome_metrica(mob), "Killed": 0, "Killed_By": 0}
        
    for _, row in df_mobs_raw.iterrows():
        mob = row["Métrica_ID"]
        if mob in dados_mobs:
            if row["Categoria_Original"] == "killed": dados_mobs[mob]["Killed"] = row["Valor"]
            elif row["Categoria_Original"] == "killed_by": dados_mobs[mob]["Killed_By"] = row["Valor"]
            
    df_categoria = pd.DataFrame(list(dados_mobs.values()))
    if not df_categoria.empty:
        df_categoria['Total_Interacoes'] = df_categoria['Killed'] + df_categoria['Killed_By']
        
    if ocultar_zerados and categoria_selecionada_visual == "🐷 Mobs (Passivos)":
        df_categoria = df_categoria[df_categoria['Total_Interacoes'] > 0]
        
    df_categoria = aplicar_ordenacao(df_categoria, coluna_valor="Total_Interacoes")
    
    renderizar_grafico_horizontal(df_categoria, "Killed", "Top 15 Criaturas Eliminadas")
    st.markdown("#### 👾 Registo de Combate")
    
    colunas_por_linha = 4
    itens = df_categoria.to_dict('records')
    for i in range(0, len(itens), colunas_por_linha):
        cols = st.columns(colunas_por_linha)
        pedaco = itens[i:i + colunas_por_linha]
        for j, item in enumerate(pedaco):
            with cols[j]:
                icone = classificar_emoji(item["Métrica_ID"], "Mobs")
                if item['Total_Interacoes'] > 0:
                    st.markdown(f"<span style='font-size:16px; font-weight:600;'>{icone} {item['Métrica']}</span>", unsafe_allow_html=True)
                    st.code(f"Kills:     {int(item['Killed'])}\nKilled By: {int(item['Killed_By'])}", language="text")
                else:
                    estilo = f"<div style='opacity: 0.3; filter: grayscale(100%); margin-bottom: 1rem;'><p style='font-size: 16px; margin-bottom: 5px; font-weight: 600;'>{icone} {item['Métrica']}</p><div style='background-color: #0e1117; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px;'>Kills:     0<br>Killed By: 0</div></div>"
                    st.markdown(estilo, unsafe_allow_html=True)

# 3. Comida
elif categoria_selecionada_visual == "🍎 Food & Drinks":
    df_comida_raw = df_ativo[df_ativo["Categoria_Original"] == "used"]
    dados_comida = []
    for comida in FOOD_ITEMS:
        registro = df_comida_raw[df_comida_raw["Métrica_ID"] == comida]
        if not registro.empty:
            valor = registro["Valor"].values[0]
            nome = registro["Métrica"].values[0]
        else:
            valor, nome = 0, formatar_nome_metrica(comida)
        dados_comida.append({"Métrica_ID": comida, "Métrica": nome, "Categoria": "Comida", "Valor": valor})
        
    df_categoria = pd.DataFrame(dados_comida)
    renderizar_grade_nativa(df_categoria, "Alimentação (Vezes Consumidas)", aplicar_filtro_zeros=False)

# 4. Estatísticas Gerais (Sub-Abas Organizadas)
elif categoria_selecionada_visual == "📄 General":
    df_geral = df_ativo[(df_ativo["Categoria_Original"] == "custom") & (~df_ativo["Métrica_ID"].isin(["deaths", "mob_kills", "player_kills"]))]
    if ocultar_zerados: df_geral = df_geral[df_geral["Valor"] > 0]
    if termo_busca: df_geral = df_geral[df_geral["Métrica"].str.lower().str.contains(termo_busca) | df_geral["Métrica_ID"].str.lower().str.contains(termo_busca)]

    def classificar_subcategoria(row):
        m = row["Métrica_ID"].lower()
        if "time" in m or "minute" in m: return "⏱️ Tempo de Jogo"
        if any(x in m for x in ["one_cm", "meter", "fly", "aviate", "swim", "walk", "crouch", "sprint", "fall", "boat", "horse", "sneak", "climb"]): return "🏃 Movimento"
        if "jump" in m: return "🏃 Movimento"
        if any(x in m for x in ["interact", "open", "inspect", "pot", "use", "fill", "ring", "tune", "play", "enchant"]): return "🖐️ Interações"
        if any(x in m for x in ["damage", "sleep", "bed", "rest", "death", "drop"]): return "🛡️ Sobrevivência"
        if any(x in m for x in ["villager", "talked", "traded", "bred", "animal"]): return "🤝 Social & Comércio"
        return "⏱️ Diversos & Tempo"
        
    if not df_geral.empty:
        df_geral["Subcategoria"] = df_geral.apply(classificar_subcategoria, axis=1)
        
        ordem_abas = ["⏱️ Tempo de Jogo", "🏃 Movimento", "🖐️ Interações", "🛡️ Sobrevivência", "🤝 Social & Comércio", "⏱️ Diversos & Tempo"]
        lista_subcategorias = [sub for sub in ordem_abas if sub in df_geral["Subcategoria"].unique().tolist()]
        
        abas_gerais = st.tabs(lista_subcategorias)
        
        for i, subcat in enumerate(lista_subcategorias):
            with abas_gerais[i]:
                df_sub = df_geral[df_geral["Subcategoria"] == subcat]
                
                if eh_visao_geral and not df_sub.empty:
                    principal_metrica = df_sub.groupby("Métrica_ID")["Valor"].sum().idxmax()
                    nome_metrica_lider = df_sub[df_sub["Métrica_ID"] == principal_metrica]["Métrica"].iloc[0]
                    renderizar_grafico_comparativo_jogadores(df, principal_metrica, nome_metrica_lider)
                
                renderizar_grade_nativa(df_sub, f"Estatísticas de {subcat.split(' ', 1)[1]}", aplicar_filtro_zeros=False, mostrar_grafico=True)

# 5. Outros Filtros (Blocos)
else:
    categorias_alvo = opcoes_menu[categoria_selecionada_visual]
    df_categoria = df_ativo[(df_ativo["Categoria"] == categorias_alvo) & (~df_ativo["Métrica_ID"].isin(["deaths", "mob_kills", "player_kills"]))]
    
    if eh_visao_geral and not df_categoria.empty:
        top_metric_id = df_categoria.groupby("Métrica_ID")["Valor"].sum().idxmax()
        nome_bloco_lider = df_categoria[df_categoria["Métrica_ID"] == top_metric_id]["Métrica"].iloc[0]
        renderizar_grafico_comparativo_jogadores(df, top_metric_id, nome_bloco_lider)
        
    renderizar_grade_nativa(df_categoria, "Estatísticas Registadas", aplicar_filtro_zeros=True)