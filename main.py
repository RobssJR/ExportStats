import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import json
import os
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIGURAÇÃO INICIAL E AUTO-REFRESH
# ==========================================
st.set_page_config(page_title="Minecraft Server Telemetry", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=5000, key="data_refresh")

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
                    if "time" in metrica_limpa or "minute" in metrica_limpa:
                         valor = round(valor / 72000, 2)
                    elif "one_cm" in metrica_limpa:
                         metrica_limpa = metrica_limpa.replace("one_cm", "meters")
                         valor = round(valor / 100, 2)

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
termo_busca = st.sidebar.text_input("Pesquisar na categoria...", "").lower()

# ==========================================
# DEFINIÇÃO DO CONJUNTO DE DADOS (GLOBAL vs PLAYER)
# ==========================================
if jogador_selecionado == "Visão Geral do Servidor":
    st.title("🌐 Visão Geral do Servidor")
    st.markdown("### 🗺️ Mapa ao Vivo")
    components.iframe("http://lucas-server:25566/#world:1006:60:-697:88:0:0:0:1:flat", height=450, scrolling=True)
    st.divider()
    # Soma todas as estatísticas agrupando pela Métrica
    df_ativo = df.groupby(["Categoria_Original", "Categoria", "Métrica_ID", "Métrica"], as_index=False)["Valor"].sum()
else:
    st.title(f"👤 {jogador_selecionado}")
    df_ativo = df[df["Jogador"] == jogador_selecionado]

# ==========================================
# MOTORES DE RENDERIZAÇÃO
# ==========================================
def exibir_kpis_topo(df_dados):
    kpi_kills = df_dados[(df_dados["Métrica_ID"] == "mob_kills")]["Valor"].sum()
    kpi_deaths = df_dados[(df_dados["Métrica_ID"] == "deaths")]["Valor"].sum()
    col1, col2, col3 = st.columns([1, 1, 2])
    col1.metric("⚔️ Total Mobs Eliminados", int(kpi_kills))
    col2.metric("☠️ Mortes Globais", int(kpi_deaths))
    st.divider()

def renderizar_grafico_horizontal(df_grafico, coluna_valor, titulo):
    if df_grafico.empty: return
    # Pega os 15 maiores e inverte para o Plotly renderizar do topo para a base
    df_top = df_grafico.sort_values(coluna_valor, ascending=False).head(15)
    df_top = df_top.sort_values(coluna_valor, ascending=True)
    
    if df_top[coluna_valor].sum() == 0: return # Não exibe gráfico se tudo for 0
    
    fig = px.bar(df_top, x=coluna_valor, y="Métrica", orientation='h', text=coluna_valor, title=titulo)
    fig.update_layout(yaxis_title=None, xaxis_title="Quantidade", margin=dict(l=0, r=0, t=40, b=0), height=350)
    st.plotly_chart(fig, use_container_width=True)

def renderizar_itens_consolidados(df_dados, titulo, aplicar_filtro_zeros=True):
    if aplicar_filtro_zeros and ocultar_zerados:
        df_dados = df_dados[df_dados['Total_Interacoes'] > 0]
    if termo_busca:
        df_dados = df_dados[df_dados["Métrica"].str.lower().str.contains(termo_busca) | df_dados["Métrica_ID"].str.lower().str.contains(termo_busca)]
    if df_dados.empty:
        st.info("Nenhum dado para mostrar.")
        return
        
    renderizar_grafico_horizontal(df_dados, "Total_Interacoes", "Top 15 Itens Mais Interagidos")
    st.markdown(f"#### 📦 {titulo}")
    
    colunas_por_linha = 4
    itens = df_dados.to_dict('records')
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

def renderizar_mobs_consolidados(df_dados, titulo, aplicar_filtro_zeros=True):
    if aplicar_filtro_zeros and ocultar_zerados:
        df_dados = df_dados[df_dados['Total_Interacoes'] > 0]
    if termo_busca:
        df_dados = df_dados[df_dados["Métrica"].str.lower().str.contains(termo_busca) | df_dados["Métrica_ID"].str.lower().str.contains(termo_busca)]
    if df_dados.empty:
        st.info("Nenhum dado para mostrar.")
        return

    renderizar_grafico_horizontal(df_dados, "Killed", "Top 15 Criaturas Eliminadas")
    st.markdown(f"#### 👾 {titulo}")
    
    colunas_por_linha = 5
    itens = df_dados.to_dict('records')
    for i in range(0, len(itens), colunas_por_linha):
        cols = st.columns(colunas_por_linha)
        pedaco = itens[i:i + colunas_por_linha]
        for j, item in enumerate(pedaco):
            with cols[j]:
                icone = classificar_emoji(item["Métrica_ID"], "Mobs")
                if item['Total_Interacoes'] > 0:
                    st.markdown(f"**{icone} {item['Métrica']}**")
                    st.code(f"Kills:     {int(item['Killed'])}\nKilled By: {int(item['Killed_By'])}", language="text")
                else:
                    estilo = f"<div style='opacity: 0.3; filter: grayscale(100%); margin-bottom: 1rem;'><p style='font-size: 14px; margin-bottom: 5px; font-weight: bold;'>{icone} {item['Métrica']}</p><div style='background-color: #0e1117; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 13px;'>Kills:     0<br>Killed By: 0</div></div>"
                    st.markdown(estilo, unsafe_allow_html=True)

def renderizar_grade_nativa(df_dados, titulo, aplicar_filtro_zeros=True, mostrar_grafico=True):
    if aplicar_filtro_zeros and ocultar_zerados:
        df_dados = df_dados[df_dados["Valor"] > 0]
    if termo_busca:
        df_dados = df_dados[df_dados["Métrica"].str.lower().str.contains(termo_busca) | df_dados["Métrica_ID"].str.lower().str.contains(termo_busca)]
    if df_dados.empty:
        st.info("Nenhum dado para mostrar.")
        return

    if mostrar_grafico:
        renderizar_grafico_horizontal(df_dados, "Valor", f"Top 15 {titulo.replace('Registadas', '')}")
        
    st.markdown(f"#### {titulo}")
    colunas_por_linha = 6
    itens = df_dados.to_dict('records')
    for i in range(0, len(itens), colunas_por_linha):
        cols = st.columns(colunas_por_linha)
        pedaco = itens[i:i + colunas_por_linha]
        for j, item in enumerate(pedaco):
            with cols[j]:
                icone = classificar_emoji(item["Métrica_ID"], item.get("Categoria", ""))
                valor = int(item["Valor"]) if isinstance(item["Valor"], (int, float)) and item["Valor"].is_integer() else item["Valor"]
                if valor > 0:
                    st.metric(label=f"{icone} {item['Métrica']}", value=valor)
                else:
                    estilo = f"<div style='opacity: 0.3; filter: grayscale(100%); margin-bottom: 1rem;'><p style='font-size: 14px; margin-bottom: -5px;'>{icone} {item['Métrica']}</p><h2 style='font-size: 1.8rem; margin-top: 0; font-weight: normal;'>0</h2></div>"
                    st.markdown(estilo, unsafe_allow_html=True)
    st.divider()

# ==========================================
# LÓGICA DE EXIBIÇÃO POR MENU
# ==========================================
st.subheader(f"{categoria_selecionada_visual.split(' ')[0]} {categoria_selecionada_visual.split(' ', 1)[1]}")

# 1. Agrupamento de Itens
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
        df_categoria = df_categoria.sort_values(by="Total_Interacoes", ascending=False)
    renderizar_itens_consolidados(df_categoria, "Registo de Itens")

# 2. Mobs Hostis e Passivos (Inclui KPIs no topo)
elif categoria_selecionada_visual in ["🧟 Hostile Mobs", "🐷 Mobs (Passivos)"]:
    exibir_kpis_topo(df_ativo)
    
    df_mobs_raw = df_ativo[df_ativo["Categoria_Original"].isin(["killed", "killed_by"])]
    if categoria_selecionada_visual == "🧟 Hostile Mobs":
        lista_alvo = HOSTILE_MOBS
    else:
        lista_alvo = df_mobs_raw[~df_mobs_raw["Métrica_ID"].isin(HOSTILE_MOBS)]["Métrica_ID"].unique()
        
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
        df_categoria = df_categoria.sort_values(by="Total_Interacoes", ascending=False)
        
    ignorar_zero = False if categoria_selecionada_visual == "🧟 Hostile Mobs" else True
    renderizar_mobs_consolidados(df_categoria, "Registo de Combate", aplicar_filtro_zeros=ignorar_zero)

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
        
    df_categoria = pd.DataFrame(dados_comida).sort_values(by="Valor", ascending=False)
    renderizar_grade_nativa(df_categoria, "Alimentação (Vezes Consumidas)", aplicar_filtro_zeros=False)

# 4. Estatísticas Gerais (Organizadas em Sub-Abas)
elif categoria_selecionada_visual == "📄 General":
    df_geral = df_ativo[(df_ativo["Categoria_Original"] == "custom") & (~df_ativo["Métrica_ID"].isin(["deaths", "mob_kills", "player_kills"]))]
    if ocultar_zerados: df_geral = df_geral[df_geral["Valor"] > 0]
    if termo_busca: df_geral = df_geral[df_geral["Métrica"].str.lower().str.contains(termo_busca) | df_geral["Métrica_ID"].str.lower().str.contains(termo_busca)]

    def classificar_subcategoria(row):
        m = row["Métrica_ID"].lower()
        if any(x in m for x in ["meter", "jump", "fly", "aviate", "swim", "walk", "crouch", "sprint", "fall", "boat", "horse", "sneak"]): return "🏃 Movimento"
        if any(x in m for x in ["interact", "open", "inspect", "pot", "use", "fill", "ring", "tune", "play", "enchant"]): return "🖐️ Interações"
        if any(x in m for x in ["damage", "sleep", "bed", "rest", "death", "drop"]): return "🛡️ Sobrevivência"
        if any(x in m for x in ["villager", "talked", "traded", "bred", "animal"]): return "🤝 Social & Comércio"
        return "⏱️ Diversos & Tempo"
        
    if not df_geral.empty:
        df_geral["Subcategoria"] = df_geral.apply(classificar_subcategoria, axis=1)
        lista_subcategorias = sorted(df_geral["Subcategoria"].unique().tolist())
        abas_gerais = st.tabs(lista_subcategorias)
        
        for i, subcat in enumerate(lista_subcategorias):
            with abas_gerais[i]:
                df_sub = df_geral[df_geral["Subcategoria"] == subcat]
                renderizar_grade_nativa(df_sub, f"Estatísticas de {subcat.split(' ', 1)[1]}", aplicar_filtro_zeros=False, mostrar_grafico=True)

# 5. Outros Filtros (Blocos)
else:
    df_categoria = df_ativo[(df_ativo["Categoria"] == opcoes_menu[categoria_selecionada_visual]) & (~df_ativo["Métrica_ID"].isin(["deaths", "mob_kills", "player_kills"]))]
    renderizar_grade_nativa(df_categoria, "Estatísticas Registadas", aplicar_filtro_zeros=True)