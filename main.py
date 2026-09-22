import streamlit as st
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

HOSTILE_MOBS = [
    "zombie", "skeleton", "creeper", "spider", "cave_spider", "enderman", 
    "witch", "slime", "magma_cube", "silverfish", "zombie_villager", 
    "phantom", "drowned", "husk", "stray", "vindicator", "evoker", 
    "pillager", "ravager", "guardian", "elder_guardian", "shulker", 
    "endermite", "blaze", "ghast", "wither_skeleton", "hoglin", "zoglin", 
    "piglin_brute", "warden", "wither", "ender_dragon"
]

# ==========================================
# FUNÇÕES DE SUPORTE E DADOS
# ==========================================
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
    
    if "apple" in item or "bread" in item or "beef" in item or "porkchop" in item: return "🥩"
    if "potion" in item or "bottle" in item: return "🧪"
    if "bucket" in item: return "🪣"
    if "boat" in item: return "🛶"
    if "bed" in item: return "🛏️"
    if "door" in item: return "🚪"
    
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
                        "Categoria_Original": categoria_limpa,
                        "Métrica_ID": metrica_limpa,
                        "Métrica": formatar_nome_metrica(metrica_limpa),
                        "Valor": valor
                    })
                    
    return pd.DataFrame(registros)

df = carregar_dados()

if df.empty:
    st.error("Nenhum dado encontrado. Verifique o mapeamento da pasta de estatísticas.")
    st.stop()

# ==========================================
# INTERFACE PRINCIPAL E BARRA LATERAL
# ==========================================
st.sidebar.title("🎮 Painel de Controlo")

lista_jogadores = sorted(df["Jogador"].unique().tolist())
jogador_selecionado = st.sidebar.selectbox("👤 Selecionar Jogador", lista_jogadores)
df_jogador = df[df["Jogador"] == jogador_selecionado]

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗂️ Filtros")

opcoes_menu = {
    "📄 General": "Estatísticas Gerais",
    "🧭 Items": "Agrupamento_Itens",
    "🟫 Blocks": "Blocos Minerados",
    "🐷 Mobs (Passivos)": "Criaturas Eliminadas", 
    "🧟 Hostile Mobs": "Criaturas Hostis",
    "🍎 Food & Drinks": "Comida"
}

categoria_selecionada_visual = st.sidebar.selectbox("Menu", list(opcoes_menu.keys()))
categorias_alvo = opcoes_menu[categoria_selecionada_visual]
termo_busca = st.sidebar.text_input("Pesquisar na categoria...", "").lower()

# ==========================================
# LÓGICA DE PROCESSAMENTO DE DADOS
# ==========================================
df_categoria = pd.DataFrame()

# 1. Agrupamento de Itens Consolidados
if categoria_selecionada_visual == "🧭 Items":
    categorias_excluidas = ["Estatísticas Gerais", "Criaturas Eliminadas", "Criaturas Hostis"]
    df_itens_raw = df_jogador[~df_jogador["Categoria"].isin(categorias_excluidas)]
    
    dados_agrupados = {}
    for _, row in df_itens_raw.iterrows():
        m_id = row["Métrica_ID"]
        cat = row["Categoria_Original"]
        val = row["Valor"]
        
        if m_id not in dados_agrupados:
            dados_agrupados[m_id] = {
                "Métrica_ID": m_id,
                "Métrica": row["Métrica"],
                "Criado": 0, "Usado": 0, "Minerado": 0, "Quebrado": 0, "Apanhado": 0, "Caído": 0
            }
        
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

# 2. Mobs Hostis (Exibe a Pokédex completa, interagidos ou não)
elif categoria_selecionada_visual == "🧟 Hostile Mobs":
    df_hostis_abatidos = df_jogador[(df_jogador["Categoria_Original"] == "killed") & (df_jogador["Métrica_ID"].isin(HOSTILE_MOBS))]
    
    dados_hostis = []
    for mob in HOSTILE_MOBS:
        registro = df_hostis_abatidos[df_hostis_abatidos["Métrica_ID"] == mob]
        if not registro.empty:
            valor = registro["Valor"].values[0]
            nome = registro["Métrica"].values[0]
        else:
            valor = 0
            nome = formatar_nome_metrica(mob)
        
        dados_hostis.append({
            "Métrica_ID": mob,
            "Métrica": nome,
            "Categoria": "Criaturas Hostis",
            "Valor": valor
        })
        
    df_categoria = pd.DataFrame(dados_hostis)
    
    # Injeta mortes/abates no topo
    df_combate = df_jogador[(df_jogador["Categoria_Original"] == "custom") & (df_jogador["Métrica_ID"].isin(["deaths", "mob_kills", "player_kills"]))]
    df_categoria = pd.concat([df_combate, df_categoria]).reset_index(drop=True)

# 3. Mobs Passivos (Filtra os hostis da categoria killed)
elif categoria_selecionada_visual == "🐷 Mobs (Passivos)":
    df_categoria = df_jogador[(df_jogador["Categoria_Original"] == "killed") & (~df_jogador["Métrica_ID"].isin(HOSTILE_MOBS))]
    df_combate = df_jogador[(df_jogador["Categoria_Original"] == "custom") & (df_jogador["Métrica_ID"].isin(["deaths", "mob_kills", "player_kills"]))]
    df_categoria = pd.concat([df_combate, df_categoria]).reset_index(drop=True)

# 4. Comida (Exemplo de filtro customizado)
elif categoria_selecionada_visual == "🍎 Food & Drinks":
    # Se você quiser mapear comidas no futuro, pode isolar os IDs aqui
    df_categoria = pd.DataFrame() 

# 5. Outros (Geral, Blocos)
else:
    if isinstance(categorias_alvo, list):
        df_categoria = df_jogador[df_jogador["Categoria"].isin(categorias_alvo)]
    else:
        df_categoria = df_jogador[df_jogador["Categoria"] == categorias_alvo]

# ==========================================
# MOTORES DE RENDERIZAÇÃO
# ==========================================
def renderizar_itens_consolidados(df_dados, titulo):
    if termo_busca:
        df_dados = df_dados[df_dados["Métrica"].str.lower().str.contains(termo_busca) | df_dados["Métrica_ID"].str.lower().str.contains(termo_busca)]
        
    if df_dados.empty:
        st.info("Nenhum dado encontrado para esta seleção.")
        return

    st.markdown(f"#### 📦 {titulo}")
    
    colunas_por_linha = 4
    itens = df_dados.to_dict('records')
    
    for i in range(0, len(itens), colunas_por_linha):
        cols = st.columns(colunas_por_linha)
        pedaco = itens[i:i + colunas_por_linha]
        
        for j, item in enumerate(pedaco):
            with cols[j]:
                icone = classificar_emoji(item["Métrica_ID"], "Itens")
                nome = item["Métrica"]
                id_raw = item["Métrica_ID"]
                
                st.markdown(f"**{icone} {nome}**")
                st.caption(f"`minecraft:{id_raw}`")
                
                st.code(
                    f"Times Crafted: {int(item['Criado'])}\n"
                    f"Times Used:    {int(item['Usado'])}\n"
                    f"Times Broken:  {int(item['Minerado'] + item['Quebrado'])}\n"
                    f"Picked Up:     {int(item['Apanhado'])}\n"
                    f"Dropped:       {int(item['Caído'])}",
                    language="text"
                )
    st.divider()

def renderizar_grade_nativa(df_dados, titulo):
    if termo_busca:
        df_dados = df_dados[df_dados["Métrica"].str.lower().str.contains(termo_busca) | df_dados["Métrica_ID"].str.lower().str.contains(termo_busca)]
        
    if df_dados.empty:
        st.info("Nenhum dado encontrado para esta seleção.")
        return

    st.markdown(f"#### {titulo}")
    
    colunas_por_linha = 8
    itens = df_dados.to_dict('records')
    
    for i in range(0, len(itens), colunas_por_linha):
        cols = st.columns(colunas_por_linha)
        pedaco = itens[i:i + colunas_por_linha]
        
        for j, item in enumerate(pedaco):
            with cols[j]:
                icone = classificar_emoji(item["Métrica_ID"], item.get("Categoria", ""))
                nome = item["Métrica"]
                valor = item["Valor"]
                
                valor_formatado = int(valor) if isinstance(valor, (int, float)) and valor.is_integer() else valor
                
                if valor > 0:
                    st.metric(label=f"{icone} {nome}", value=valor_formatado)
                else:
                    estilo_apagado = f"""
                    <div style='opacity: 0.3; filter: grayscale(100%); margin-bottom: 1rem;'>
                        <p style='font-size: 14px; margin-bottom: -5px;'>{icone} {nome}</p>
                        <h2 style='font-size: 1.8rem; margin-top: 0; font-weight: normal;'>{valor_formatado}</h2>
                    </div>
                    """
                    st.markdown(estilo_apagado, unsafe_allow_html=True)
                    
    st.divider()

# ==========================================
# EXIBIÇÃO FINAL
# ==========================================
st.title("⛏️ Telemetria do Servidor")
st.subheader(f"{categoria_selecionada_visual.split(' ')[0]} {categoria_selecionada_visual.split(' ', 1)[1]}")

if categoria_selecionada_visual == "🧭 Items":
    renderizar_itens_consolidados(df_categoria, "Registro Completo de Itens e Ferramentas")
else:
    renderizar_grade_nativa(df_categoria, "Registos Ativos")