import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8787"

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

def get_json(path):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Accept": "application/json", "Host": "127.0.0.1:8787"}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))

stf_resp = get_json("/api/stf-attacks")
stf_attacks = stf_resp.get("attacks", [])

hdb_resp = get_json("/api/heraclitus-attacks")
hdb_attacks = hdb_resp.get("attacks", [])

queue = []
for a in stf_attacks:
    queue.append(("stf", a["id"], a["title"], a.get("target", "asset:unknown")))
for a in hdb_attacks:
    queue.append(("hdb", a["id"], a["title"], a.get("target", "asset:heraclitusdb")))
if len(queue) < 30:
    for a in stf_attacks[:(30 - len(queue))]:
        queue.append(("stf", a["id"], f"{a['title']} (onda 2)", a.get("target", "asset:unknown")))

queue = queue[:30]

print(f"=== DISPARANDO ONDA DE 30 ATAQUES AO VIVO ===")
print("Observe o grafo pulsando e atualizando em https://35.247.217.66/stf/\n")

for i, (kind, atk_id, title, target) in enumerate(queue, 1):
    try:
        if kind == "stf":
            res = post_json("/api/stf-attacks/execute", {"attack_id": atk_id})
        else:
            res = post_json("/api/heraclitus-attacks/execute", {"attack_id": atk_id})

        lsn = res.get("lsn")
        verdict = res.get("verdict") or res.get("decision") or "pass"
        print(f"[{i:02d}/30] LSN: {lsn:>4} | Alvo: {target:<25} | {title[:38]:<38} | Veredito: {verdict}")
    except Exception as e:
        print(f"[{i:02d}/30] ERRO em {atk_id}: {e}")
    time.sleep(0.7)

print("\n=== ONDA DE 30 ATAQUES FINALIZADA ===")
final_s = get_json("/api/state")
print(f"• Nós no Grafo:      {len(final_s.get('graph', {}).get('nodes', []))}")
print(f"• Arestas no Grafo:  {len(final_s.get('graph', {}).get('edges', []))}")
print(f"• Total no Ledger:   {final_s.get('total_attempts', 0)} tentativas ({final_s.get('total_blocked', 0)} bloqueadas)")
