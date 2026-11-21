from typing import List, Dict, Any

SUPPORTED_PORTALS: List[Dict[str, Any]] = [{"id": "domria", "name": "DOM.RIA Україна", "badge": "🇺🇦 DOM.RIA"}, {"id": "olx_ua", "name": "OLX Нерухомість", "badge": "🇺🇦 OLX"}, {"id": "flatfy_ua", "name": "Flatfy Україна", "badge": "🇺🇦 Flatfy"}, {"id": "rieltor_ua", "name": "Rieltor.ua", "badge": "🇺🇦 Rieltor"}, {"id": "lun_ua", "name": "ЛУН Нерухомість", "badge": "🇺🇦 ЛУН"}]

def get_portal_by_id(portal_id: str):
    for p in SUPPORTED_PORTALS:
        if p["id"] == portal_id:
            return p
    return None
