import json
import urllib.request
import time

events = [
    ("FW-ATK-01", "RECONNAISSANCE", "network.port_scan", "firewall:perimeter-edge-01", "SYN-Stealth-Scan 1-65535", "DETECTED", "ALERT_LOGGED", "FW_SCAN_THRESHOLD_REACHED", False),
    ("FW-ATK-02", "RECONNAISSANCE", "network.service_probe", "firewall:perimeter-edge-01", "OS Fingerprinting via TCP Options", "DETECTED", "ALERT_LOGGED", "FW_FINGERPRINT_PROBE", False),
    ("FW-ATK-03", "RECONNAISSANCE", "network.dns_amplification", "firewall:perimeter-edge-01", "EDNS0 Pseudo-request query burst", "DENY", "DROP", "FW_DNS_AMP_BLOCKED", True),
    ("FW-ATK-04", "RECONNAISSANCE", "network.ip_fragmentation", "firewall:perimeter-edge-01", "Tiny Fragments Overlapping Attack", "DENY", "DROP", "FW_FRAG_ANOMALY", True),
    
    ("FW-ATK-05", "INITIAL-ACCESS", "auth.bruteforce_ssh", "firewall:perimeter-mgmt-gw", "Hydra SSH brute force admin portal", "DETECTED", "RATE_LIMITED", "FW_AUTH_FAILED_RATE", False),
    ("FW-ATK-06", "INITIAL-ACCESS", "auth.credential_stuffing", "firewall:perimeter-mgmt-gw", "Compromised admin token replay", "DENY", "REVOKED", "FW_INVALID_SIGNATURE", True),
    ("FW-ATK-07", "INITIAL-ACCESS", "auth.vpn_bruteforce", "firewall:ssl-vpn-gateway", "IPSec/IKEv2 PreSharedKey spray", "DETECTED", "CHALLENGE", "FW_IKE_AGGRESSIVE_FAIL", False),
    ("FW-ATK-08", "INITIAL-ACCESS", "auth.bypass_header", "firewall:perimeter-mgmt-gw", "X-Forwarded-For injection on admin port 8443", "DENY", "FORBIDDEN", "FW_SPOOF_HEADER_BLOCKED", True),

    ("FW-ATK-09", "EXPLOITATION", "cve.buffer_overflow", "firewall:perimeter-edge-01", "Heap overflow on PAN-OS/FortiOS daemon parser", "DETECTED", "SIGNATURE_MATCH", "FW_SIG_CVE_2024_PARSER_HIT", False),
    ("FW-ATK-10", "EXPLOITATION", "cve.rce_payload", "firewall:perimeter-edge-01", "Injected shellcode into packet inspection ring", "DENY", "MEM_CORRUPTION_KILL", "FW_ASLR_DEP_TRIGGER", True),
    ("FW-ATK-11", "EXPLOITATION", "cve.firmware_tamper", "firewall:perimeter-edge-01", "Attempt to patch kernel iptables in memory", "DENY", "INTEGRITY_FAULT", "FW_KERNEL_HOOK_REJECTED", True),
    ("FW-ATK-12", "EXPLOITATION", "cve.zero_day_tunnel", "firewall:perimeter-edge-01", "Covert ICMP Type 8 payload encapsulation tunnel", "DETECTED", "DPI_ANOMALY", "FW_COVERT_CHANNEL_FLAGGED", False),

    ("FW-ATK-13", "EVASION", "policy.rule_tampering", "firewall:policy-engine", "Unauthorized POST /api/v1/rules to allow ANY:ANY", "DENY", "REJECT_RBAC", "FW_POLICY_RBAC_VIOLATION", True),
    ("FW-ATK-14", "EVASION", "policy.acl_bypass", "firewall:packet-filter", "IPv6-in-IPv4 GRE tunneling over port 53", "DENY", "PROTOCOL_MISMATCH", "FW_GRE_ENCAP_DISALLOWED", True),
    ("FW-ATK-15", "EVASION", "transport.evasion_chunk", "firewall:dpi-engine", "HTTP Chunked transfer smuggling through proxy", "DENY", "RESET_TCP", "FW_SMUGGLING_TCP_RST", True),
    ("FW-ATK-16", "EVASION", "transport.tls_fingerprint", "firewall:dpi-engine", "JA3 rogue fingerprint detected: CobaltStrike client", "DETECTED", "QUARANTINE_IP", "FW_THREAT_INTEL_MATCH", False),

    ("FW-ATK-17", "CONTAINMENT", "data.exfiltration_attempt", "firewall:dmz-outbound", "DNS TXT staging 50MB base64 compressed data", "DENY", "DNS_SINKHOLED", "FW_EXFIL_DNS_BLOCKED", True),
    ("FW-ATK-18", "CONTAINMENT", "lateral.smb_propagation", "firewall:internal-segment", "EternalBlue SMBv1 probe to subnets", "DENY", "SEGMENT_ISOLATED", "FW_LATERAL_SEGMENT_DROP", True),
    ("FW-ATK-19", "CONTAINMENT", "c2.beaconing", "firewall:egress-gateway", "TLS beacon to untrusted TOR exit node", "DENY", "BLACKHOLED", "FW_C2_HOST_ISOLATED", True),
    ("FW-ATK-20", "CONTAINMENT", "incident.killswitch_active", "firewall:perimeter-edge-01", "SOAR automated lockdown: zero-trust isolation engaged", "CONTAINED", "DEFENSE_SUCCESS", "FW_ZERO_TRUST_LOCKDOWN", True),
]

campaign = f"FIREWALL-INTRUSION-SIM-{int(time.time())}"
print(f"=== INICIANDO APPEND NO HERACLITUSDB (CAMPANHA: {campaign}) ===")
print("Simulando 20 registros cronológicos de invasão de firewall perimetral...\n")

results = []
for i, item in enumerate(events, 1):
    atk_id, phase, vector, target, desc, res, exp, reason, blocked = item
    payload = {
        "attack_id": f"{atk_id}",
        "campaign_id": campaign,
        "vector": f"{vector}: {desc}",
        "target": target,
        "phase": phase,
        "result": res,
        "expected": exp,
        "reason_code": reason,
        "blocked": blocked,
        "upstream_delta": 0,
        "sequence": i
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8080/api/v1/agent/red-team/events",
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5.0) as r:
            resp = json.loads(r.read().decode("utf-8"))
            lsn = resp.get("lsn")
            ev_id = resp.get("evidence_id")
            accepted = resp.get("accepted")
            status_str = "BLOCKED" if blocked else "DETECTED"
            print(f"[{i:02d}/20] LSN: {lsn:>5} | ID: {atk_id:<9} | Fase: {phase:<15} | Status: {status_str:<8} | Evidence: {ev_id}")
            results.append(resp)
    except Exception as e:
        print(f"[{i:02d}/20] ERRO ao gravar {atk_id}: {e}")
    time.sleep(0.05)

print("\n=== VERIFICAÇÃO DE LEITURA DO LOG NO HERACLITUSDB ===")
verify_url = f"http://127.0.0.1:8080/api/v1/agent/red-team/events?campaign={campaign}&limit=25"
req_v = urllib.request.Request(verify_url, headers={"Accept": "application/json"})
with urllib.request.urlopen(req_v, timeout=5.0) as r:
    saved = json.loads(r.read().decode("utf-8"))
    ev_list = saved.get("events", [])
    print(f"Total de registros lidos no log: {len(ev_list)}")
    summary = saved.get("summary", {})
    print(f"Resumo da campanha: Bloqueados={summary.get('blocked')}, Alcançou Upstream={summary.get('reached_upstream')}")
    print("\n--- Amostra dos eventos lidos da cadeia criptográfica HRKL v6 ---")
    for ev in reversed(ev_list[:5]):
        print(f"• LSN {ev.get('lsn')} | {ev.get('phase')} | {ev.get('attack_id')} | Hash: {ev.get('record_hash')}")
