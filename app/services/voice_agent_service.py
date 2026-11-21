"""
FindHome Ukraine — Advanced AI Real Estate Voice & WhatsApp Agent
Conversational multi-turn engine with per-user session memory,
pagination, property cards, visit booking, and rent split calculations.
Connected to official WhatsApp support line: +34 603 331 391
"""

import re
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.models.database import get_properties

AGENT_WHATSAPP_NUMBER = "+34603331391"
AGENT_WHATSAPP_CLEAN = "34603331391"

BRAND_NAME = "FindHome Ukraine"
COUNTRY_NAME = "Ukraine"
CURRENCY_SYMBOL = "₴"
DEFAULT_LANG = "uk"
AVG_RENT_BENCHMARK = 38000
LOCAL_CITIES = ["Київ", "Львів", "Одеса", "Дніпро", "Харків", "Івано-Франківськ", "Вінниця", "Запоріжжя"]

class UserSession:
    def __init__(self, user_id: str, user_name: str = "Visitor"):
        self.user_id = user_id
        self.user_name = user_name or "Visitor"
        self.city: Optional[str] = None
        self.offset: int = 0
        self.last_properties: List[Dict[str, Any]] = []
        self.selected_property: Optional[Dict[str, Any]] = None
        self.budget_max: Optional[float] = None
        self.roommates_count: Optional[int] = None
        self.state: str = "idle"
        self.last_visit_booking: Optional[Dict[str, Any]] = None
        self.last_activity = datetime.now()

    def touch(self):
        self.last_activity = datetime.now()

class LocalizedVoiceAgent:
    def __init__(self):
        self.whatsapp_number = AGENT_WHATSAPP_NUMBER
        self.clean_whatsapp = AGENT_WHATSAPP_CLEAN
        self.brand = BRAND_NAME
        self.currency = CURRENCY_SYMBOL
        self.sessions: Dict[str, UserSession] = {}

    def get_or_create_session(self, user_id: Optional[str], user_name: Optional[str] = None) -> UserSession:
        uid = str(user_id or "anonymous_guest").strip()
        now = datetime.now()
        expired = [k for k, s in self.sessions.items() if (now - s.last_activity).total_seconds() > 86400]
        for k in expired:
            del self.sessions[k]

        if uid not in self.sessions:
            self.sessions[uid] = UserSession(uid, user_name or "Visitor")
        else:
            if user_name and user_name != "Visitor":
                self.sessions[uid].user_name = user_name
            self.sessions[uid].touch()

        return self.sessions[uid]

    def process_query(
        self,
        message: str,
        lang: Optional[str] = None,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        channel: str = "whatsapp"
    ) -> Dict[str, Any]:
        target_lang = lang or DEFAULT_LANG
        session = self.get_or_create_session(user_id, user_name)
        msg_raw = (message or "").strip()
        msg_clean = msg_raw.lower()

        # Greetings
        if any(msg_clean == w or msg_clean.startswith(f"{w} ") for w in [
            "hello", "hi", "hey", "hola", "привет", "здравствуйте", "добрый день",
            "привіт", "вітаю", "добрий день", "bună", "salut", "noroc"
        ]):
            return self._handle_greeting(session, target_lang, channel)

        # Pagination
        more_keywords = [
            "more options", "show more", "next", "see more", "more", "other options",
            "mas opciones", "más opciones", "muestrame mas", "tienes mas", "еще варианты",
            "еще", "покажи еще", "другие варианты", "ще варіанти", "ще", "покажи ще",
            "mai multe", "mai multe optiuni", "urmatoarele"
        ]
        if any(k in msg_clean for k in more_keywords):
            return self._handle_more_options(session, target_lang, channel)

        # Selection
        sel_idx = self._extract_selection_index(msg_clean)
        if sel_idx is not None and session.last_properties:
            return self._handle_select_property(session, sel_idx, target_lang, channel)

        # Visit Scheduling
        if self._is_visit_request(msg_clean):
            return self._handle_visit_scheduling(session, msg_raw, target_lang, channel)

        # City Search
        matched_city = None
        for city in LOCAL_CITIES:
            if city.lower() in msg_clean:
                matched_city = city
                break

        beds_match = re.search(r"(\d+)\s*(bedrooms|beds|rooms|комнат|кімнат|camere)", msg_clean)
        bedrooms = int(beds_match.group(1)) if beds_match else None

        budget_match = re.search(r"(\d[\d\.,]{2,})", msg_clean)
        budget_max = None
        if budget_match:
            try:
                budget_max = float(budget_match.group(1).replace(".", "").replace(",", ""))
            except Exception:
                budget_max = None

        if matched_city or (session.city and any(w in msg_clean for w in ["flat", "apartment", "квартира", "аренда", "оренда", "chirie", "apartament", "zona", "centru"])):
            target_city = matched_city or session.city
            return self._handle_city_search(session, target_city, bedrooms, budget_max, target_lang, channel)

        # Rent-Split Calculator
        calc_match = re.search(r"(\d+)\s*(people|roommates|человек|людей|persoane)", msg_clean)
        if any(w in msg_clean for w in ["calculate", "split", "rent", "посчитать", "разделить", "розрахувати", "calculeaza"]) or (calc_match and budget_max):
            roommates = int(calc_match.group(1)) if calc_match else (session.roommates_count or 4)
            total_rent = budget_max if budget_max else AVG_RENT_BENCHMARK
            return self._handle_calculator(session, roommates, total_rent, target_lang, channel)

        # Fallback
        return self._handle_fallback(session, msg_raw, target_lang, channel)

    def _handle_greeting(self, session: UserSession, lang: str, channel: str) -> Dict[str, Any]:
        session.state = "browsing"
        top_cities = ", ".join(LOCAL_CITIES[:4])

        if channel == "whatsapp":
            if lang == "ru":
                reply = (
                    f"Здравствуйте! Вас приветствует официальный ИИ-ассистент *{self.brand}* 🏡\n\n"
                    f"Я помогу найти просторную квартиру для совместной аренды и организовать просмотры в {COUNTRY_NAME}:\n"
                    f"• *Популярные города:* {top_cities}\n\n"
                    f"В каком городе вы ищете жилье или на какой бюджет рассчитываете?"
                )
            elif lang == "uk":
                reply = (
                    f"Вітаємо! Вас вітає офіційний ШІ-асистент *{self.brand}* 🏡\n\n"
                    f"Допоможу знайти якісне житло для спільної оренди та організувати перегляди в {COUNTRY_NAME}:\n"
                    f"• *Популярні міста:* {top_cities}\n\n"
                    f"У якому місті шукаєте квартиру або який у вас бюджет?"
                )
            elif lang == "ro":
                reply = (
                    f"Bună ziua! Vă salută asistentul oficial AI *{self.brand}* 🏡\n\n"
                    f"Vă ajut să găsiți locuințe partajate verificate și să programați vizionări în {COUNTRY_NAME}:\n"
                    f"• *Orașe recomandate:* {top_cities}\n\n"
                    f"În ce oraș căutați chirie sau care este bugetul lunar?"
                )
            else:
                reply = (
                    f"Hello! Welcome to *{self.brand}* Official AI Assistant 🏡\n\n"
                    f"I can help you find verified shared apartments in {COUNTRY_NAME}:\n"
                    f"• *Featured cities:* {top_cities}\n\n"
                    f"Which city or budget are you looking for?"
                )
        else:
            reply = f"Welcome to {self.brand}. Finding verified shared living in {COUNTRY_NAME}."

        return {
            "reply_text": reply,
            "action": "greeting",
            "whatsapp_url": self.build_whatsapp_link(f"Hello {self.brand}, I am looking for shared housing options.")
        }

    def _handle_city_search(self, session: UserSession, city: str, bedrooms: Optional[int], budget_max: Optional[float], lang: str, channel: str) -> Dict[str, Any]:
        session.city = city
        session.offset = 0

        props = self._query_properties(city=city)
        if not props:
            props = get_properties()

        session.last_properties = props[:3]
        total_found = len(props)

        if channel == "whatsapp":
            items_text = []
            for i, p in enumerate(session.last_properties, 1):
                rent_total = p.get("total_rent", AVG_RENT_BENCHMARK)
                beds = p.get("bedrooms", 4)
                rent_p = round(rent_total / max(1, beds))
                title = p.get("title", f"Apartment in {city}")
                addr = p.get("address") or p.get("neighborhood") or city
                surface = p.get("surface", 120)
                items_text.append(
                    f"*{i}️⃣ {title}*\n"
                    f"📍 {addr}\n"
                    f"🛏️ {beds} комн. | 📐 {surface} m² | 💵 *{rent_p:,} {self.currency}/чел/мес* (Всего: {rent_total:,} {self.currency})"
                    if lang in ["ru", "uk"] else
                    f"*{i}️⃣ {title}*\n"
                    f"📍 {addr}\n"
                    f"🛏️ {beds} camere | 📐 {surface} m² | 💵 *{rent_p:,} {self.currency}/pers/lună* (Total: {rent_total:,} {self.currency})"
                )

            cards = "\n\n".join(items_text)
            reply = (
                f"🏙️ *Доступные варианты в {city} (найдено: {total_found}):*\n\n"
                f"{cards}\n\n"
                f"👉 Напишите *1*, *2* или *3*, чтобы посмотреть фото и детали,\n"
                f"или напишите *'еще'*, чтобы увидеть следующие квартиры."
                if lang in ["ru", "uk"] else
                f"🏙️ *Opțiuni disponibile în {city} (găsite: {total_found}):*\n\n"
                f"{cards}\n\n"
                f"👉 Scrieți *1*, *2* sau *3* pentru detalii complete,\n"
                f"sau scrieți *'mai multe'* pentru alte oferte."
            )
        else:
            reply = f"Found {total_found} listings in {city}."

        return {
            "reply_text": reply,
            "action": "property_recommendations",
            "city": city,
            "suggested_properties": session.last_properties,
            "total_count": total_found
        }

    def _handle_more_options(self, session: UserSession, lang: str, channel: str) -> Dict[str, Any]:
        target_city = session.city or LOCAL_CITIES[0]
        session.offset += 3

        all_props = self._query_properties(city=target_city)
        if not all_props:
            all_props = get_properties()

        if session.offset >= len(all_props):
            session.offset = 0
            next_props = all_props[:3]
            wrapped = True
        else:
            next_props = all_props[session.offset:session.offset + 3]
            wrapped = False

        session.last_properties = next_props

        if channel == "whatsapp":
            items_text = []
            for i, p in enumerate(next_props, 1):
                rent_total = p.get("total_rent", AVG_RENT_BENCHMARK)
                beds = p.get("bedrooms", 4)
                rent_p = round(rent_total / max(1, beds))
                title = p.get("title", f"Apartment in {target_city}")
                addr = p.get("address") or p.get("neighborhood") or target_city
                surface = p.get("surface", 120)
                items_text.append(
                    f"*{i}️⃣ {title}*\n"
                    f"📍 {addr}\n"
                    f"🛏️ {beds} комн. | 📐 {surface} m² | 💵 *{rent_p:,} {self.currency}/чел/мес* (Всего: {rent_total:,} {self.currency})"
                    if lang in ["ru", "uk"] else
                    f"*{i}️⃣ {title}*\n"
                    f"📍 {addr}\n"
                    f"🛏️ {beds} camere | 📐 {surface} m² | 💵 *{rent_p:,} {self.currency}/pers/lună* (Total: {rent_total:,} {self.currency})"
                )

            cards = "\n\n".join(items_text)
            header = f"🔄 *Следующие {len(next_props)} вариантов в {target_city}:*" if lang in ["ru", "uk"] else f"🔄 *Următoarele {len(next_props)} opțiuni în {target_city}:*"
            reply = f"{header}\n\n{cards}\n\n👉 Напишите *1*, *2* или *3* для бронирования просмотра или укажите другой город." if lang in ["ru", "uk"] else f"{header}\n\n{cards}\n\n👉 Răspundeți cu *1*, *2* sau *3* pentru vizionare."
        else:
            reply = f"More listings in {target_city}."

        return {
            "reply_text": reply,
            "action": "property_recommendations",
            "city": target_city,
            "suggested_properties": next_props,
            "offset": session.offset
        }

    def _handle_select_property(self, session: UserSession, idx: int, lang: str, channel: str) -> Dict[str, Any]:
        if idx < 0 or idx >= len(session.last_properties):
            idx = 0

        prop = session.last_properties[idx]
        session.selected_property = prop
        session.state = "viewing_detail"

        title = prop.get("title", "Apartment")
        city = prop.get("city", session.city or LOCAL_CITIES[0])
        addr = prop.get("address", city)
        beds = prop.get("bedrooms", 4)
        baths = prop.get("bathrooms", 2)
        surface = prop.get("surface", 120)
        rent_total = prop.get("total_rent", AVG_RENT_BENCHMARK)
        rent_p = round(rent_total / max(1, beds))
        desc = prop.get("desc", prop.get("description", "Fully furnished co-living residence."))
        contact = prop.get("contact_name", f"{self.brand} Coordinator")

        if channel == "whatsapp":
            reply = (
                f"✨ *Детали варианта {idx + 1}:*\n"
                f"🏠 *{title}*\n\n"
                f"📍 *Адрес:* {addr}, {city}\n"
                f"💵 *Доля на человека:* *{rent_p:,} {self.currency}/мес*\n"
                f"💰 *Общая аренда:* {rent_total:,} {self.currency}/мес ({beds} комн, {baths} санузла)\n"
                f"📐 *Площадь:* {surface} m²\n"
                f"📋 *Описание:* {desc}\n"
                f"👤 *Координатор:* {contact}\n\n"
                f"📅 *Желаете записаться на онлайн или очный просмотр?*\n"
                f"Напишите удобный день и время (например: *'Завтра в 17:00'* или *'В пятницу днем'*), и я зафиксирую запись."
                if lang in ["ru", "uk"] else
                f"✨ *Detalii pentru Opțiunea {idx + 1}:*\n"
                f"🏠 *{title}*\n\n"
                f"📍 *Adresă:* {addr}, {city}\n"
                f"💵 *Chirie individuală:* *{rent_p:,} {self.currency}/lună*\n"
                f"💰 *Chirie totală:* {rent_total:,} {self.currency}/lună ({beds} camere, {baths} băi)\n"
                f"📐 *Suprafață:* {surface} m²\n"
                f"📋 *Descriere:* {desc}\n"
                f"👤 *Coordonator:* {contact}\n\n"
                f"📅 *Doriți să programați o vizionare?*\n"
                f"Menționați ziua și ora dorită (ex: *'Mâine la ora 17:00'*) și vă rezervăm vizita."
            )
        else:
            reply = f"Selected {title} in {city}."

        return {"reply_text": reply, "action": "property_detail", "property": prop}

    def _handle_visit_scheduling(self, session: UserSession, raw_msg: str, lang: str, channel: str) -> Dict[str, Any]:
        if not session.selected_property and session.last_properties:
            session.selected_property = session.last_properties[0]

        target_prop = session.selected_property
        prop_title = target_prop.get("title", "Apartment") if target_prop else "Listing"
        prop_city = target_prop.get("city", session.city or LOCAL_CITIES[0]) if target_prop else "City"
        prop_addr = target_prop.get("address", "") if target_prop else ""

        session.state = "visit_confirmed"
        session.last_visit_booking = {
            "property": prop_title, "city": prop_city, "time": raw_msg,
            "user": session.user_name, "phone": session.user_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if channel == "whatsapp":
            reply = (
                f"✅ *Просмотр успешно запланирован!*\n\n"
                f"🏠 *Объект:* {prop_title}\n"
                f"📍 *Локация:* {prop_addr or prop_city}\n"
                f"🕒 *Время:* {raw_msg}\n"
                f"👤 *Контакт:* {session.user_name} ({session.user_id})\n\n"
                f"Координатор {self.brand} свяжется с вами в этом чате WhatsApp для подтверждения доступа.\n"
                f"Хотите узнать больше об условиях договора или посмотреть другие квартиры?"
                if lang in ["ru", "uk"] else
                f"✅ *Vizionare Pre-Programată cu Succes!*\n\n"
                f"🏠 *Locuință:* {prop_title}\n"
                f"📍 *Adresă:* {prop_addr or prop_city}\n"
                f"🕒 *Ora solicitată:* {raw_msg}\n"
                f"👤 *Solicitant:* {session.user_name} ({session.user_id})\n\n"
                f"Coordonatorul nostru vă va contacta prin acest chat de WhatsApp pentru confirmare."
            )
        else:
            reply = f"Tour scheduled for {prop_title}."

        return {"reply_text": reply, "action": "visit_booked", "booking": session.last_visit_booking}

    def _handle_calculator(self, session: UserSession, roommates: int, total_rent: float, lang: str, channel: str) -> Dict[str, Any]:
        roommates = max(1, roommates)
        per_person = round(total_rent / roommates)

        if channel == "whatsapp":
            reply = (
                f"🧮 *Расчет распределения аренды:*\n\n"
                f"• Общая стоимость: {int(total_rent):,} {self.currency}/мес\n"
                f"• Количество сожителей: {roommates} чел.\n"
                f"• Доля каждого: 👉 *{per_person:,} {self.currency}/чел/мес*\n\n"
                f"Показать квартиры с {roommates} комнатами под этот бюджет?"
                if lang in ["ru", "uk"] else
                f"🧮 *Calcul Împărțire Chirie:*\n\n"
                f"• Chirie totală: {int(total_rent):,} {self.currency}/lună\n"
                f"• Colegi de apartament: {roommates} persoane\n"
                f"• Cotă individuală: 👉 *{per_person:,} {self.currency}/pers/lună*\n\n"
                f"Doriți apartamente cu {roommates} camere pentru acest buget?"
            )
        else:
            reply = f"Per-person quota: {per_person:,} {self.currency}."

        return {"reply_text": reply, "action": "calculator_result", "per_person": per_person, "total_rent": total_rent, "roommates": roommates}

    def _handle_fallback(self, session: UserSession, raw_msg: str, lang: str, channel: str) -> Dict[str, Any]:
        city_hint = f" в *{session.city}*" if session.city else ""
        if channel == "whatsapp":
            reply = (
                f"Ваш запрос: *'{raw_msg}'*\n\n"
                f"Вы можете:\n"
                f"• Указать город: *{', '.join(LOCAL_CITIES[:4])}*...\n"
                f"• Запросить *'еще варианты'*{city_hint}\n"
                f"• Написать номер (*1*, *2* или *3*) для деталей и записи на просмотр\n"
                f"• Или спросить расчет аренды на нескольких человек."
                if lang in ["ru", "uk"] else
                f"Mesajul dvs: *'{raw_msg}'*\n\n"
                f"Puteți indica un oraș (*{', '.join(LOCAL_CITIES[:4])}*), cere *'mai multe'* opțiuni, sau scrie numărul (*1*, *2*, *3*) pentru vizionare."
            )
        else:
            reply = f"Welcome to {self.brand}."
        return {"reply_text": reply, "action": "fallback"}

    def _query_properties(self, city: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            return get_properties(city=city)
        except Exception:
            try:
                from app.models.database import INITIAL_PROPERTIES
                return INITIAL_PROPERTIES
            except Exception:
                return []

    def _extract_selection_index(self, msg: str) -> Optional[int]:
        if msg in ["1", "1️⃣", "first", "первый", "первая", "перший", "перша", "primul", "prima"]:
            return 0
        if msg in ["2", "2️⃣", "second", "второй", "вторая", "другий", "друга", "al doilea", "a doua"]:
            return 1
        if msg in ["3", "3️⃣", "third", "третий", "третья", "третій", "третя", "al treilea", "a treia"]:
            return 2
        m1 = re.search(r"\b1\b", msg)
        if m1 and "10" not in msg and "11" not in msg:
            return 0
        m2 = re.search(r"\b2\b", msg)
        if m2 and "20" not in msg:
            return 1
        m3 = re.search(r"\b3\b", msg)
        if m3 and "30" not in msg:
            return 2
        return None

    def _is_visit_request(self, msg: str) -> bool:
        time_words = [
            "tomorrow", "today", "monday", "friday", "завтра", "сегодня", "пятница", "понедельник",
            "просмотр", "посмотреть", "записаться", "перегляд", "подивитися", "mâine", "astazi", "vizionare", "vizita"
        ]
        return any(w in msg for w in time_words) and any(w in msg for w in ["просмотр", "посмотреть", "перегляд", "vizionare", "vizita", "at", "в", "la", "ora"])

    def build_whatsapp_link(self, message: str) -> str:
        encoded = urllib.parse.quote(message)
        return f"https://wa.me/{self.clean_whatsapp}?text={encoded}"

voice_agent = LocalizedVoiceAgent()
