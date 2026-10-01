import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8787"

def get_json(path):
    req = urllib.request.Request(f"{BASE_URL}{path}", headers={"Accept": "application/json", "Host": "127.0.0.1:8787"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))

def post_json(path, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-STF-POC": "1",
            "Host": "127.0.0.1:8787"
        }
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))

print("=== COLETANDO CATÁLOGO DE ATAQUES DISPONÍVEIS ===")
stf_resp = get_json("/api/stf-attacks")
stf_attacks = stf_resp.get("attacks", [])

hdb_resp = get_json("/api/heraclitus-attacks")
hdb_attacks = hdb_resp.get("attacks", [])

print(f"Encontrados {len(stf_attacks)} ataques do STF e {len(hdb_attacks)} ataques do HeraclitusDB.")

# Montando a bateria de 40 ataques
queue = []
# Adiciona todos os STF (20)
for a in stf_attacks:
    queue.append(("stf", a["id"], a["title"], a.get("target", "asset:unknown")))

# Adiciona todos os Heraclitus (10)
for a in hdb_attacks:
    queue.append(("hdb", a["id"], a["title"], a.get("target", "asset:heraclitusdb")))

# Completa mais 10 variados para fechar exatamente 40
for a in stf_attacks[:10]:
    queue.append(("stf", a["id"], f"{a['title']} (onda 2)", a.get("target", "asset:unknown")))

print(f"\n>>> INICIANDO EXECUÇÃO DE {len(queue)} ATAQUES EM TEMPO REAL <<<")
print("O grafo na tela https://35.247.217.66/stf/ deve pulsar e atualizar nós a cada segundo...\n")

for i, (kind, atk_id, title, target) in enumerate(queue, 1):
    try:
        if kind == "stf":
            res = post_json("/api/stf-attacks/execute", {"attack_id": atk_id})
        else:
            res = post_json("/api/heraclitus-attacks/execute", {"attack_id": atk_id})

        lsn = res.get("lsn")
        verdict = res.get("verdict") or res.get("decision") or "OK"
        print(f"[{i:02d}/40] LSN: {lsn:>5} | Alvo: {target:<25} | {title[:40]:<40} | Veredito: {verdict}")
    except Exception as e:
        print(f"[{i:02d}/40] ERRO ao disparar {atk_id}: {e}")
    time.sleep(0.7)

print("\n=== EXECUÇÃO DOS 40 ATAQUES CONCLUÍDA ===")
final_state = get_json("/api/state")
print(f"Total de eventos no STF: {len(final_state.get('events', []))}")
print(f"Nós no Grafo: {len(final_state.get('graph', {}).get('nodes', []))}")
print(f"Arestas no Grafo: {len(final_state.get('graph', {}).get('edges', []))}")
print(f"Última ação registrada: {final_state.get('last_action')}")
