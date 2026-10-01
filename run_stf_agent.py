import urllib.request
import json
import time
import sys

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

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "list"
    
    if action == "list":
        attacks = get_json("/api/stf-attacks")
        print(f"Total de ataques STF catalogados: {len(attacks.get('attacks', []))}")
        for a in attacks.get("attacks", [])[:5]:
            print(f"- [{a.get('id')}] {a.get('title')} -> Alvo: {a.get('target')}")

    elif action == "reset":
        r = post_json("/api/reset", {})
        print("Ambiente resetado com sucesso:", r.get("message"))

    elif action == "attack":
        attack_id = sys.argv[2] if len(sys.argv) > 2 else "IA_VIC_01"
        print(f"Disparando ataque STF: {attack_id}...")
        r = post_json("/api/stf-attacks/execute", {"attack_id": attack_id})
        print("Resultado do ataque:", json.dumps({
            "attack": r.get("attack", {}).get("title"),
            "target": r.get("attack", {}).get("target"),
            "verdict": r.get("verdict"),
            "lsn": r.get("lsn"),
            "hash": r.get("event_hash")
        }, indent=2, ensure_ascii=False))

    elif action == "step":
        print("Executando próximo passo da campanha...")
        r = post_json("/api/step", {})
        print(f"Passo {r.get('step')}/{r.get('total_steps')}: {r.get('last_action')}")
        print(f"Grafo atualizado: {len(r.get('graph', {}).get('nodes', []))} nós, {len(r.get('graph', {}).get('edges', []))} arestas")
