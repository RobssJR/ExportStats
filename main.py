from fastapi import FastAPI
import json
import os

app = FastAPI(title="Minecraft Stats API")

# IMPORTANTE: Altere para o caminho absoluto ou relativo da raiz do seu servidor
SERVER_DIR = "../"  # Exemplo: "/home/usuario/minecraft_server/"
STATS_DIR = os.path.join(SERVER_DIR, "world/stats")
USERCACHE = os.path.join(SERVER_DIR, "usercache.json")

def obter_nomes_jogadores():
    """Lê o usercache.json para mapear UUID -> Nickname"""
    if not os.path.exists(USERCACHE):
        return {}
    with open(USERCACHE, "r") as f:
        try:
            cache = json.load(f)
            return {jogador["uuid"]: jogador["name"] for jogador in cache}
        except json.JSONDecodeError:
            return {}

@app.get("/api/v1/stats/all")
def obter_todas_estatisticas():
    """
    Retorna o JSON completo estruturado por Jogador -> Categoria -> Métrica.
    Converte automaticamente ticks para horas (para tempo de jogo) e 
    centímetros para metros (para distância).
    """
    nomes = obter_nomes_jogadores()
    resultado = []
    
    if not os.path.exists(STATS_DIR):
        return {"erro": "Pasta de estatísticas não encontrada."}

    for arquivo in os.listdir(STATS_DIR):
        if arquivo.endswith(".json"):
            uuid = arquivo.replace(".json", "")
            nome_jogador = nomes.get(uuid, f"Unknown_{uuid[:8]}")
            caminho_arquivo = os.path.join(STATS_DIR, arquivo)
            
            with open(caminho_arquivo, "r") as f:
                try:
                    dados = json.load(f)
                except json.JSONDecodeError:
                    continue
            
            stats_nativas = dados.get("stats", {})
            estatisticas_formatadas = {}
            
            # Itera sobre as categorias (custom, mined, killed, etc)
            for categoria_bruta, metricas in stats_nativas.items():
                categoria_limpa = categoria_bruta.replace("minecraft:", "")
                estatisticas_formatadas[categoria_limpa] = {}
                
                for metrica_bruta, valor in metricas.items():
                    metrica_limpa = metrica_bruta.replace("minecraft:", "")
                    
                    # Conversões úteis para telemetria
                    # 1 segundo = 20 ticks. 1 hora = 72000 ticks
                    if "time" in metrica_limpa or "minute" in metrica_limpa:
                         # Retorna em horas com 2 casas decimais
                         valor = round(valor / 72000, 2)
                    
                    # Minecraft salva distâncias em centímetros. Converte para metros.
                    elif "one_cm" in metrica_limpa:
                         metrica_limpa = metrica_limpa.replace("one_cm", "meters")
                         valor = round(valor / 100, 2)

                    estatisticas_formatadas[categoria_limpa][metrica_limpa] = valor
            
            # Adiciona ao array de resultados
            resultado.append({
                "player": nome_jogador,
                "uuid": uuid,
                "stats": estatisticas_formatadas
            })
            
    return resultado

@app.get("/api/v1/ranking/{categoria}/{metrica}")
def obter_ranking(categoria: str, metrica: str):
    """
    Retorna um ranking ordenado (maior para menor) de uma métrica específica.
    Exemplo: /api/v1/ranking/custom/play_time
    """
    todos_dados = obter_todas_estatisticas()
    ranking = []
    
    if isinstance(todos_dados, dict) and "erro" in todos_dados:
        return todos_dados

    for jogador_data in todos_dados:
        # Busca o valor na estrutura aninhada
        try:
            valor = jogador_data["stats"][categoria][metrica]
            if valor > 0:
                ranking.append({
                    "player": jogador_data["player"],
                    "value": valor
                })
        except KeyError:
            continue
            
    # Ordena do maior para o menor
    ranking.sort(key=lambda x: x["value"], reverse=True)
    return ranking