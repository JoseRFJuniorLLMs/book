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

# Sequência cronológica de invasão perimetral e progressão de rede
invasion_steps = [
    ("NET_WAF_01", "1. Borda/Firewall", "Varredura L7 e Scanners no Firewall de Borda"),
    ("NET_IAM_02", "2. Autenticação", "Tentativa de Bypass de MFA no Identity Provider"),
    ("LNX_APP_01", "3. Servidor de Aplicação", "Tentativa de Execução no SUSE Linux srv-app-07"),
    ("LNX_DB_02",  "4. Movimentação Lateral", "Pivot do srv-app-07 para o Banco srv-db-02"),
    ("DB_ORA_01",  "5. Banco de Dados", "Injeção SQL em Metadados Processuais Oracle RAC"),
    ("DB_ORA_02",  "6. Criptografia", "Tentativa de Bypass TDE no Oracle RAC"),
    ("IA_VIC_01",  "7. Agente IA", "Prompt Injection na IA Victor"),
    ("IA_VIT_03",  "8. Exfiltração", "Tentativa de Exfiltração de Jurisprudência Sigilosa"),
    ("APP_STF_01", "9. Processo Judicial", "Tentativa de Alteração de Processo no STF Digital"),
    ("NET_WAF_01", "10. Contenção Borda", "Bloqueio e Isolamento no Firewall de Borda"),
]

print("=== DISPARANDO INVASÃO ORQUESTRADA PELO MOTOR STF + HERACLITUSDB ===")
print("Observe o Grafo e o Ledger em https://35.247.217.66/stf/\n")

for i, (atk_id, phase_label, desc) in enumerate(invasion_steps, 1):
    try:
        r = post_json("/api/stf-attacks/execute", {"attack_id": atk_id})
        lsn = r.get("lsn")
        atk = r.get("attack", {})
        target = atk.get("target", "n/a")
        verdict = r.get("verdict", "OK")
        print(f"[{i:02d}/10] {phase_label:<25} | LSN: {lsn:>4} | Alvo: {target:<24} | Veredito: {verdict}")
    except Exception as e:
        print(f"[{i:02d}/10] ERRO ao executar {atk_id}: {e}")
    time.sleep(1.0)

print("\n=== VERIFICANDO SINCRONIZAÇÃO GRAFO + LEDGER ===")
s = get_json("/api/state")
print(f"• Nós ativos no Grafo visual: {len(s.get('graph', {}).get('nodes', []))}")
print(f"• Arestas ativas no Grafo:   {len(s.get('graph', {}).get('edges', []))}")
print(f"• Total de Eventos no STF:    {len(s.get('events', []))}")
print(f"• Total de Tentativas:        {s.get('total_attempts', 0)}")
print(f"• Total Bloqueado por Política: {s.get('total_blocked', 0)}")
