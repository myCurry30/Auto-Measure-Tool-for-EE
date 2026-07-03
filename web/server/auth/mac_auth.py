"""阶段 1: 基于 MAC 地址的免密认证."""
import subprocess
import re
import json
import threading
from pathlib import Path

_ARP_CACHE: dict[str, str] = {}  # ip → mac 短期缓存
_ARP_LOCK = threading.Lock()

USER_PINS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "user_pins.json"


def get_mac_from_ip(ip: str) -> str | None:
    """通过 ARP 表解析 IP → MAC 地址（Windows）."""
    with _ARP_LOCK:
        cached = _ARP_CACHE.get(ip)
        if cached:
            return cached

    try:
        # 先 ping 预热 ARP
        subprocess.run(
            ["ping", "-n", "1", "-w", "500", ip],
            capture_output=True, timeout=2,
        )
        result = subprocess.run(
            ["arp", "-a", ip],
            capture_output=True, text=True, timeout=5,
        )
        match = re.search(
            r"([0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}"
            r"[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2})",
            result.stdout,
        )
        if match:
            mac = match.group(1).replace("-", ":").upper()
            with _ARP_LOCK:
                _ARP_CACHE[ip] = mac
            return mac
    except Exception:
        pass
    return None


def authenticate(username: str, client_ip: str) -> dict | None:
    """验证用户名 + 客户端 MAC.

    Returns:
        {"role": "operator", "display_name": username} 或 None
    """
    if not USER_PINS_PATH.exists():
        return None

    with open(USER_PINS_PATH, "r", encoding="utf-8") as f:
        users = json.load(f)

    user = users.get(username)
    if not user:
        return None

    expected_macs = [m.upper().replace('-', ':') for m in user.get("mac_addresses", [])]
    if not expected_macs:
        return None

    actual_mac = get_mac_from_ip(client_ip)
    if actual_mac is None:
        # ARP 未命中 — 返回特殊标记让调用方重试
        return None  # caller should check get_mac_from_ip separately

    if actual_mac not in expected_macs:
        return None

    return {
        "role": user.get("role", "operator"),
        "display_name": user.get("display_name", username),
    }


def is_arp_miss(ip: str) -> bool:
    """检查是否因为 ARP 未命中导致 MAC 获取失败."""
    return get_mac_from_ip(ip) is None
