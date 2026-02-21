"""
⚔️ Данные игрового мира — текстовая MMO RPG v2
Классы, монстры, 8 зон, башня, квесты, экспедиции, колесо, крафт, аукцион
"""
import random

# ============ РЕДКОСТЬ ============
RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]
RARITY_EMOJI = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}
RARITY_NAMES = {"common": "Обычный", "uncommon": "Необычный", "rare": "Редкий", "epic": "Эпический", "legendary": "Легендарный"}
SELL_PRICES = {"common": 30, "uncommon": 80, "rare": 250, "epic": 800, "legendary": 3000}

# Цены аукциона (множители к SELL_PRICES)
AUCTION_PRICE_TIERS = {1: 2, 2: 3, 3: 5}
AUCTION_FEE = 0.10  # 10% комиссия

# Крафт — стоимость улучшения
UPGRADE_COSTS = {"common": 100, "uncommon": 300, "rare": 1000, "epic": 5000}
UPGRADE_NEXT = {"common": "uncommon", "uncommon": "rare", "rare": "epic", "epic": "legendary"}

# ============ РАСЫ ============
RACES = {
    "human": {
        "name": "👤 Человек",
        "desc": "Универсальная раса. Сбалансированные характеристики.",
        "bonus_hp": 0, "bonus_attack": 0, "bonus_defense": 0, "bonus_crit": 0,
    },
    "elf": {
        "name": "🧝 Эльф",
        "desc": "Магическая раса. Повышенный крит и атака.",
        "bonus_hp": -10, "bonus_attack": 2, "bonus_defense": -1, "bonus_crit": 3.0,
    },
    "orc": {
        "name": "👹 Орк",
        "desc": "Сильная раса. Много HP и атаки, но низкая защита.",
        "bonus_hp": 20, "bonus_attack": 3, "bonus_defense": -2, "bonus_crit": -1.0,
    },
    "dwarf": {
        "name": "🧔 Гном",
        "desc": "Выносливая раса. Высокая защита и HP.",
        "bonus_hp": 15, "bonus_attack": -1, "bonus_defense": 3, "bonus_crit": 0,
    },
    "dragonborn": {
        "name": "🐉 Драконорожденный",
        "desc": "Могущественная раса. Повышенные все характеристики.",
        "bonus_hp": 10, "bonus_attack": 2, "bonus_defense": 1, "bonus_crit": 2.0,
    },
}

# ============ КЛАССЫ (14 штук) ============
CLASSES = {
    "warrior": {
        "name": "⚔️ Воин", "desc": "Крепкий боец. Много HP и хорошая защита.",
        "base_hp": 130, "base_attack": 12, "base_defense": 8, "base_crit": 5.0,
        "hp_per_lvl": 7, "atk_per_lvl": 2.0, "def_per_lvl": 1.5,
    },
    "knight": {
        "name": "🛡 Рыцарь", "desc": "Тяжёлая броня. Максимальная защита.",
        "base_hp": 140, "base_attack": 11, "base_defense": 10, "base_crit": 4.0,
        "hp_per_lvl": 8, "atk_per_lvl": 1.8, "def_per_lvl": 1.8,
    },
    "mage": {
        "name": "🧙 Маг", "desc": "Стеклянная пушка. Огромный урон и крит.",
        "base_hp": 80, "base_attack": 18, "base_defense": 4, "base_crit": 12.0,
        "hp_per_lvl": 3, "atk_per_lvl": 3.0, "def_per_lvl": 0.5,
    },
    "necromancer": {
        "name": "💀 Некромант", "desc": "Тёмная магия. Высокий урон и крит.",
        "base_hp": 85, "base_attack": 19, "base_defense": 3, "base_crit": 14.0,
        "hp_per_lvl": 3, "atk_per_lvl": 3.2, "def_per_lvl": 0.4,
    },
    "assassin": {
        "name": "🗡 Ассасин", "desc": "Быстрый и смертоносный. Критует как бог.",
        "base_hp": 95, "base_attack": 15, "base_defense": 5, "base_crit": 20.0,
        "hp_per_lvl": 4, "atk_per_lvl": 2.5, "def_per_lvl": 1.0,
    },
    "ranger": {
        "name": "🏹 Рейнджер", "desc": "Дальний бой. Хороший баланс и крит.",
        "base_hp": 100, "base_attack": 14, "base_defense": 6, "base_crit": 15.0,
        "hp_per_lvl": 5, "atk_per_lvl": 2.3, "def_per_lvl": 1.2,
    },
    "archer": {
        "name": "🎯 Лучник", "desc": "Стрелок. Высокий урон и крит.",
        "base_hp": 90, "base_attack": 16, "base_defense": 4, "base_crit": 18.0,
        "hp_per_lvl": 4, "atk_per_lvl": 2.7, "def_per_lvl": 0.8,
    },
    "paladin": {
        "name": "🛡 Паладин", "desc": "Несокрушимый защитник. Максимум HP и брони.",
        "base_hp": 160, "base_attack": 10, "base_defense": 10, "base_crit": 3.0,
        "hp_per_lvl": 9, "atk_per_lvl": 1.5, "def_per_lvl": 2.0,
    },
    "druid": {
        "name": "🌿 Друид", "desc": "Природная магия. Сбалансированный класс.",
        "base_hp": 110, "base_attack": 13, "base_defense": 7, "base_crit": 8.0,
        "hp_per_lvl": 6, "atk_per_lvl": 2.2, "def_per_lvl": 1.3,
    },
    "priest": {
        "name": "✨ Жрец", "desc": "Светлая магия. Высокий HP и защита.",
        "base_hp": 120, "base_attack": 12, "base_defense": 8, "base_crit": 6.0,
        "hp_per_lvl": 7, "atk_per_lvl": 2.0, "def_per_lvl": 1.6,
    },
    "berserker": {
        "name": "🔥 Берсерк", "desc": "Ярость. Огромная атака, но низкая защита.",
        "base_hp": 105, "base_attack": 20, "base_defense": 2, "base_crit": 10.0,
        "hp_per_lvl": 5, "atk_per_lvl": 3.5, "def_per_lvl": 0.3,
    },
    "bard": {
        "name": "🎵 Бард", "desc": "Поддержка. Сбалансированные характеристики.",
        "base_hp": 100, "base_attack": 13, "base_defense": 6, "base_crit": 9.0,
        "hp_per_lvl": 5, "atk_per_lvl": 2.1, "def_per_lvl": 1.1,
    },
    "monk": {
        "name": "🥋 Монах", "desc": "Боевые искусства. Высокий крит и скорость.",
        "base_hp": 95, "base_attack": 14, "base_defense": 6, "base_crit": 16.0,
        "hp_per_lvl": 4, "atk_per_lvl": 2.4, "def_per_lvl": 1.0,
    },
    "demonologist": {
        "name": "😈 Демонолог", "desc": "Тёмная сила. Максимальный урон.",
        "base_hp": 85, "base_attack": 21, "base_defense": 3, "base_crit": 13.0,
        "hp_per_lvl": 3, "atk_per_lvl": 3.3, "def_per_lvl": 0.4,
    },
}


def get_class_stats(class_id: str, level: int, race_id: str = None) -> dict:
    c = CLASSES[class_id]
    race_bonus = RACES.get(race_id, {}) if race_id else {}
    
    return {
        "max_hp": int(c["base_hp"] + (level - 1) * c["hp_per_lvl"] + race_bonus.get("bonus_hp", 0)),
        "attack": int(c["base_attack"] + (level - 1) * c["atk_per_lvl"] + race_bonus.get("bonus_attack", 0)),
        "defense": int(c["base_defense"] + (level - 1) * c["def_per_lvl"] + race_bonus.get("bonus_defense", 0)),
        "crit": c["base_crit"] + race_bonus.get("bonus_crit", 0),
    }


def xp_for_level(level: int) -> int:
    return 100 + (level - 1) * 50


# ============ 8 ЗОН С МОНСТРАМИ ============
ZONES = [
    {
        "id": 1, "name": "🌿 Зелёные поля", "min_level": 1,
        "monsters": [
            {"name": "Слайм", "emoji": "🟢", "hp": 35, "attack": 5, "defense": 2, "xp": 18, "gold": 15},
            {"name": "Гоблин", "emoji": "👺", "hp": 45, "attack": 8, "defense": 3, "xp": 22, "gold": 20},
            {"name": "Дикий волк", "emoji": "🐺", "hp": 55, "attack": 10, "defense": 4, "xp": 28, "gold": 22},
            {"name": "Бандит", "emoji": "🥷", "hp": 65, "attack": 12, "defense": 5, "xp": 32, "gold": 28},
            {"name": "Гигантский паук", "emoji": "🕷", "hp": 50, "attack": 14, "defense": 3, "xp": 35, "gold": 30},
        ],
        "boss": {"name": "🔴 Король гоблинов", "hp": 150, "attack": 20, "defense": 10, "xp": 100, "gold": 120},
        "drop_chance": 15, "drop_rates": {"common": 70, "uncommon": 25, "rare": 5},
    },
    {
        "id": 2, "name": "🌲 Тёмный лес", "min_level": 10,
        "monsters": [
            {"name": "Орк", "emoji": "👹", "hp": 120, "attack": 22, "defense": 10, "xp": 55, "gold": 50},
            {"name": "Скелет-воин", "emoji": "💀", "hp": 100, "attack": 25, "defense": 8, "xp": 50, "gold": 45},
            {"name": "Тёмный маг", "emoji": "🧙‍♂️", "hp": 85, "attack": 30, "defense": 6, "xp": 62, "gold": 55},
            {"name": "Минотавр", "emoji": "🐂", "hp": 150, "attack": 20, "defense": 14, "xp": 65, "gold": 60},
            {"name": "Тролль", "emoji": "🧌", "hp": 180, "attack": 18, "defense": 16, "xp": 70, "gold": 65},
        ],
        "boss": {"name": "🔴 Лесной дух", "hp": 300, "attack": 40, "defense": 20, "xp": 200, "gold": 250},
        "drop_chance": 18, "drop_rates": {"common": 20, "uncommon": 50, "rare": 25, "epic": 5},
    },
    {
        "id": 3, "name": "🏚 Проклятые руины", "min_level": 22,
        "monsters": [
            {"name": "Вампир", "emoji": "🧛", "hp": 220, "attack": 40, "defense": 18, "xp": 110, "gold": 100},
            {"name": "Некромант", "emoji": "☠️", "hp": 190, "attack": 48, "defense": 14, "xp": 120, "gold": 110},
            {"name": "Горгулья", "emoji": "🗿", "hp": 280, "attack": 35, "defense": 28, "xp": 125, "gold": 105},
            {"name": "Элементаль", "emoji": "🔥", "hp": 200, "attack": 55, "defense": 12, "xp": 135, "gold": 120},
            {"name": "Страж руин", "emoji": "⚔️", "hp": 300, "attack": 42, "defense": 25, "xp": 145, "gold": 130},
        ],
        "boss": {"name": "🔴 Лич-повелитель", "hp": 500, "attack": 65, "defense": 30, "xp": 400, "gold": 450},
        "drop_chance": 20, "drop_rates": {"uncommon": 15, "rare": 50, "epic": 30, "legendary": 5},
    },
    {
        "id": 4, "name": "🐉 Логово дракона", "min_level": 35,
        "monsters": [
            {"name": "Чёрный рыцарь", "emoji": "🖤", "hp": 400, "attack": 65, "defense": 35, "xp": 200, "gold": 200},
            {"name": "Демон", "emoji": "😈", "hp": 350, "attack": 80, "defense": 25, "xp": 220, "gold": 220},
            {"name": "Древний голем", "emoji": "🪨", "hp": 550, "attack": 50, "defense": 50, "xp": 240, "gold": 210},
            {"name": "Дракон", "emoji": "🐉", "hp": 500, "attack": 75, "defense": 40, "xp": 280, "gold": 260},
            {"name": "Хранитель портала", "emoji": "🌀", "hp": 450, "attack": 90, "defense": 30, "xp": 300, "gold": 280},
        ],
        "boss": {"name": "🔴 Древний дракон", "hp": 900, "attack": 100, "defense": 50, "xp": 700, "gold": 700},
        "drop_chance": 25, "drop_rates": {"rare": 20, "epic": 50, "legendary": 30},
    },
    {
        "id": 5, "name": "☁️ Небесная крепость", "min_level": 50,
        "monsters": [
            {"name": "Ангел-страж", "emoji": "👼", "hp": 650, "attack": 110, "defense": 50, "xp": 420, "gold": 380},
            {"name": "Грифон", "emoji": "🦅", "hp": 700, "attack": 100, "defense": 55, "xp": 450, "gold": 400},
            {"name": "Небесный голем", "emoji": "🏛", "hp": 900, "attack": 90, "defense": 70, "xp": 480, "gold": 420},
            {"name": "Архангел", "emoji": "✨", "hp": 600, "attack": 130, "defense": 45, "xp": 500, "gold": 450},
            {"name": "Серафим", "emoji": "🌟", "hp": 750, "attack": 120, "defense": 60, "xp": 550, "gold": 480},
        ],
        "boss": {"name": "🔴 Падший серафим", "hp": 1500, "attack": 160, "defense": 70, "xp": 1200, "gold": 1100},
        "drop_chance": 28, "drop_rates": {"rare": 30, "epic": 50, "legendary": 20},
    },
    {
        "id": 6, "name": "🌋 Вулкан Хаоса", "min_level": 65,
        "monsters": [
            {"name": "Лавовый элементаль", "emoji": "🔥", "hp": 950, "attack": 150, "defense": 65, "xp": 650, "gold": 550},
            {"name": "Огненный дракон", "emoji": "🐲", "hp": 1100, "attack": 140, "defense": 70, "xp": 700, "gold": 600},
            {"name": "Демон Хаоса", "emoji": "👿", "hp": 900, "attack": 170, "defense": 55, "xp": 720, "gold": 620},
            {"name": "Инфернал", "emoji": "💀", "hp": 1000, "attack": 160, "defense": 75, "xp": 750, "gold": 650},
            {"name": "Повелитель пепла", "emoji": "🌑", "hp": 1300, "attack": 145, "defense": 85, "xp": 800, "gold": 700},
        ],
        "boss": {"name": "🔴 Ифрит", "hp": 2500, "attack": 220, "defense": 90, "xp": 2000, "gold": 1800},
        "drop_chance": 30, "drop_rates": {"rare": 10, "epic": 55, "legendary": 35},
    },
    {
        "id": 7, "name": "❄️ Ледяная пустошь", "min_level": 80,
        "monsters": [
            {"name": "Ледяной великан", "emoji": "🧊", "hp": 1400, "attack": 190, "defense": 90, "xp": 950, "gold": 850},
            {"name": "Фростворм", "emoji": "🐍", "hp": 1200, "attack": 220, "defense": 80, "xp": 1000, "gold": 900},
            {"name": "Снежная ведьма", "emoji": "🧙‍♀️", "hp": 1100, "attack": 240, "defense": 70, "xp": 1050, "gold": 950},
            {"name": "Ледяной феникс", "emoji": "🦢", "hp": 1500, "attack": 200, "defense": 100, "xp": 1100, "gold": 1000},
            {"name": "Криоголем", "emoji": "🗻", "hp": 1800, "attack": 180, "defense": 120, "xp": 1200, "gold": 1050},
        ],
        "boss": {"name": "🔴 Король вечной зимы", "hp": 3500, "attack": 300, "defense": 120, "xp": 3000, "gold": 2800},
        "drop_chance": 33, "drop_rates": {"epic": 50, "legendary": 50},
    },
    {
        "id": 8, "name": "🕳 Бездна", "min_level": 100,
        "monsters": [
            {"name": "Порождение Бездны", "emoji": "👁", "hp": 2000, "attack": 280, "defense": 110, "xp": 1500, "gold": 1300},
            {"name": "Пожиратель миров", "emoji": "🌀", "hp": 2500, "attack": 260, "defense": 130, "xp": 1700, "gold": 1500},
            {"name": "Тёмный титан", "emoji": "🗿", "hp": 3000, "attack": 250, "defense": 150, "xp": 1800, "gold": 1600},
            {"name": "Void Wraith", "emoji": "👤", "hp": 1800, "attack": 350, "defense": 100, "xp": 2000, "gold": 1800},
            {"name": "Архидемон", "emoji": "😈", "hp": 2800, "attack": 300, "defense": 140, "xp": 2200, "gold": 2000},
        ],
        "boss": {"name": "🔴 Бог Хаоса", "hp": 6000, "attack": 450, "defense": 180, "xp": 5000, "gold": 5000},
        "drop_chance": 40, "drop_rates": {"epic": 20, "legendary": 80},
    },
]


def get_available_zones(level: int) -> list:
    return [z for z in ZONES if level >= z["min_level"]]


def pick_monster(zone_id: int) -> tuple:
    """Выбрать монстра. Возвращает (monster, is_boss)"""
    zone = next(z for z in ZONES if z["id"] == zone_id)
    # 8% шанс встретить мини-босса
    if random.randint(1, 100) <= 8 and zone.get("boss"):
        return zone["boss"], True
    return random.choice(zone["monsters"]), False


# ============ БАШНЯ ИСПЫТАНИЙ ============

def get_tower_monster(floor: int) -> dict:
    """Сгенерировать монстра башни для этажа"""
    is_boss = floor % 10 == 0
    mult = 2.0 if is_boss else 1.0

    names_normal = [
        "Страж", "Голем", "Призрак", "Химера", "Демон",
        "Рыцарь Тьмы", "Элементаль", "Минотавр", "Гидра", "Феникс",
    ]
    names_boss = [
        "Хранитель этажа", "Тёмный лорд", "Владыка подземелья",
        "Повелитель теней", "Древнее зло",
    ]
    emojis_normal = ["🗿", "👻", "🐉", "😈", "⚔️", "💀", "🔥", "🧌", "🐍", "🦇"]
    emojis_boss = ["👑", "🔱", "💎", "⭐", "🏆"]

    if is_boss:
        name = f"🔴 {random.choice(names_boss)} (Этаж {floor})"
        emoji = random.choice(emojis_boss)
    else:
        name = f"{random.choice(names_normal)} (Этаж {floor})"
        emoji = random.choice(emojis_normal)

    return {
        "name": name,
        "emoji": emoji,
        "hp": int((30 + floor * 18) * mult),
        "attack": int((5 + floor * 3.5) * mult),
        "defense": int((2 + floor * 1.8) * mult),
        "crit": 3.0 + floor * 0.1,
    }


def tower_rewards(floor: int) -> dict:
    """Награды за этаж башни"""
    is_boss = floor % 10 == 0
    return {
        "gold": (100 + floor * 12) * (3 if is_boss else 1),
        "xp": (15 + floor * 5) * (3 if is_boss else 1),
        "crystals": (floor // 5) + (10 if is_boss else 0),
        "drop_item": is_boss or random.randint(1, 100) <= 10 + floor // 5,
        "drop_rarity": _tower_drop_rarity(floor),
    }


def _tower_drop_rarity(floor: int) -> str:
    if floor >= 80:
        return random.choices(["epic", "legendary"], [40, 60])[0]
    if floor >= 50:
        return random.choices(["rare", "epic", "legendary"], [20, 50, 30])[0]
    if floor >= 30:
        return random.choices(["uncommon", "rare", "epic"], [20, 50, 30])[0]
    if floor >= 15:
        return random.choices(["common", "uncommon", "rare"], [20, 50, 30])[0]
    return random.choices(["common", "uncommon", "rare"], [50, 35, 15])[0]


# ============ КВЕСТЫ ============

QUEST_TEMPLATES = [
    {"type": "hunt", "target": 3, "desc": "Убей {t} монстров", "gold": 150, "crystals": 0, "xp": 50},
    {"type": "hunt", "target": 5, "desc": "Убей {t} монстров", "gold": 250, "crystals": 5, "xp": 80},
    {"type": "hunt", "target": 10, "desc": "Убей {t} монстров", "gold": 500, "crystals": 10, "xp": 150},
    {"type": "arena", "target": 1, "desc": "Выиграй {t} бой на арене", "gold": 100, "crystals": 5, "xp": 40},
    {"type": "arena", "target": 3, "desc": "Выиграй {t} боя на арене", "gold": 300, "crystals": 10, "xp": 100},
    {"type": "gacha", "target": 1, "desc": "Сделай {t} призыв", "gold": 200, "crystals": 0, "xp": 30},
    {"type": "gacha", "target": 3, "desc": "Сделай {t} призыва", "gold": 400, "crystals": 5, "xp": 60},
    {"type": "tower", "target": 3, "desc": "Пройди {t} этажа башни", "gold": 200, "crystals": 10, "xp": 100},
    {"type": "tower", "target": 5, "desc": "Пройди {t} этажей башни", "gold": 350, "crystals": 15, "xp": 150},
    {"type": "expedition", "target": 1, "desc": "Заверши {t} экспедицию", "gold": 150, "crystals": 5, "xp": 50},
    {"type": "sell", "target": 2, "desc": "Продай {t} предмета", "gold": 100, "crystals": 3, "xp": 30},
]


def generate_daily_quests(count: int = 3) -> list:
    """Сгенерировать ежедневные квесты"""
    # Берём разные типы
    types_used = set()
    quests = []
    shuffled = random.sample(QUEST_TEMPLATES, len(QUEST_TEMPLATES))
    for q in shuffled:
        if q["type"] not in types_used and len(quests) < count:
            quests.append(q.copy())
            types_used.add(q["type"])
    # Если не набрали — добираем любые
    while len(quests) < count:
        quests.append(random.choice(QUEST_TEMPLATES).copy())
    return quests


# ============ ЭКСПЕДИЦИИ ============

EXPEDITIONS = [
    {"id": "short", "name": "🏃 Быстрая вылазка", "duration": 15,
     "gold": (50, 150), "xp": (20, 50), "crystals": (0, 3), "item_chance": 5},
    {"id": "medium", "name": "🚶 Разведка", "duration": 60,
     "gold": (150, 400), "xp": (60, 150), "crystals": (2, 8), "item_chance": 18},
    {"id": "long", "name": "🗺 Дальний поход", "duration": 180,
     "gold": (400, 1000), "xp": (150, 400), "crystals": (5, 15), "item_chance": 30},
    {"id": "epic", "name": "⚔️ Великая экспедиция", "duration": 360,
     "gold": (800, 2000), "xp": (300, 800), "crystals": (10, 30), "item_chance": 45},
]


def generate_expedition_rewards(exp_id: str) -> dict:
    """Сгенерировать награды экспедиции"""
    exp = next(e for e in EXPEDITIONS if e["id"] == exp_id)
    gold = random.randint(*exp["gold"])
    xp = random.randint(*exp["xp"])
    crystals = random.randint(*exp["crystals"])
    has_item = random.randint(1, 100) <= exp["item_chance"]
    item_rarity = ""
    if has_item:
        item_rarity = random.choices(
            ["uncommon", "rare", "epic", "legendary"],
            [40, 35, 20, 5]
        )[0]
    return {"gold": gold, "xp": xp, "crystals": crystals, "item_rarity": item_rarity}


# ============ КОЛЕСО ФОРТУНЫ ============

WHEEL_PRIZES = [
    {"name": "💰 100 золота", "type": "gold", "amount": 100, "weight": 25},
    {"name": "💰 300 золота", "type": "gold", "amount": 300, "weight": 15},
    {"name": "💰 1000 золота", "type": "gold", "amount": 1000, "weight": 5},
    {"name": "💎 5 кристаллов", "type": "crystals", "amount": 5, "weight": 18},
    {"name": "💎 15 кристаллов", "type": "crystals", "amount": 15, "weight": 8},
    {"name": "💎 50 кристаллов!", "type": "crystals", "amount": 50, "weight": 2},
    {"name": "⚡ 30 энергии", "type": "energy", "amount": 30, "weight": 15},
    {"name": "⚡ Полная энергия!", "type": "energy", "amount": 100, "weight": 5},
    {"name": "🟢 Необычный предмет", "type": "item", "rarity": "uncommon", "weight": 5},
    {"name": "🔵 Редкий предмет!", "type": "item", "rarity": "rare", "weight": 4},
    {"name": "🟣 Эпический предмет!!", "type": "item", "rarity": "epic", "weight": 1},
    {"name": "🟡 ЛЕГЕНДАРНЫЙ!!!", "type": "item", "rarity": "legendary", "weight": 0.3},
    {"name": "😤 Пусто", "type": "nothing", "amount": 0, "weight": 5},
]


def spin_wheel() -> dict:
    weights = [p["weight"] for p in WHEEL_PRIZES]
    return random.choices(WHEEL_PRIZES, weights=weights)[0]


# ============ ПРЕДМЕТЫ ============

WEAPONS = {
    "common": [
        {"name": "Деревянный меч", "attack": 3, "defense": 0, "hp": 0, "crit": 0},
        {"name": "Ржавый кинжал", "attack": 2, "defense": 0, "hp": 0, "crit": 1.0},
        {"name": "Каменный топор", "attack": 4, "defense": 0, "hp": 0, "crit": 0},
        {"name": "Старая палка", "attack": 2, "defense": 1, "hp": 0, "crit": 0},
    ],
    "uncommon": [
        {"name": "Стальной меч", "attack": 6, "defense": 0, "hp": 0, "crit": 0},
        {"name": "Охотничий кинжал", "attack": 5, "defense": 0, "hp": 0, "crit": 2.0},
        {"name": "Железный топор", "attack": 7, "defense": 0, "hp": 0, "crit": 0},
        {"name": "Боевой молот", "attack": 6, "defense": 1, "hp": 5, "crit": 0},
    ],
    "rare": [
        {"name": "Зачарованный клинок", "attack": 10, "defense": 0, "hp": 0, "crit": 2.0},
        {"name": "Клинок ветра", "attack": 9, "defense": 0, "hp": 0, "crit": 3.0},
        {"name": "Магический жезл", "attack": 12, "defense": 0, "hp": 0, "crit": 1.0},
        {"name": "Серебряный меч", "attack": 11, "defense": 2, "hp": 0, "crit": 0},
    ],
    "epic": [
        {"name": "Драконий клинок", "attack": 17, "defense": 0, "hp": 10, "crit": 3.0},
        {"name": "Теневой кинжал", "attack": 14, "defense": 0, "hp": 0, "crit": 6.0},
        {"name": "Посох Бездны", "attack": 20, "defense": 0, "hp": 0, "crit": 2.0},
        {"name": "Молот Грома", "attack": 16, "defense": 3, "hp": 15, "crit": 0},
    ],
    "legendary": [
        {"name": "🔥 Экскалибур", "attack": 30, "defense": 5, "hp": 20, "crit": 5.0},
        {"name": "⚡ Мьёльнир", "attack": 28, "defense": 8, "hp": 30, "crit": 3.0},
        {"name": "💀 Жнец Душ", "attack": 35, "defense": 0, "hp": 0, "crit": 8.0},
        {"name": "✨ Клинок Бога", "attack": 32, "defense": 3, "hp": 10, "crit": 6.0},
    ],
}

ARMORS = {
    "common": [
        {"name": "Тряпичная рубашка", "attack": 0, "defense": 2, "hp": 8, "crit": 0},
        {"name": "Кожаный жилет", "attack": 0, "defense": 3, "hp": 5, "crit": 0},
    ],
    "uncommon": [
        {"name": "Кольчуга", "attack": 0, "defense": 5, "hp": 15, "crit": 0},
        {"name": "Кожаная броня", "attack": 0, "defense": 4, "hp": 20, "crit": 0},
    ],
    "rare": [
        {"name": "Латные доспехи", "attack": 0, "defense": 8, "hp": 30, "crit": 0},
        {"name": "Мифриловая кольчуга", "attack": 1, "defense": 7, "hp": 25, "crit": 0},
    ],
    "epic": [
        {"name": "Доспехи Дракона", "attack": 2, "defense": 14, "hp": 50, "crit": 0},
        {"name": "Теневая мантия", "attack": 3, "defense": 10, "hp": 30, "crit": 3.0},
    ],
    "legendary": [
        {"name": "🔥 Доспехи Бога", "attack": 5, "defense": 22, "hp": 80, "crit": 2.0},
        {"name": "💀 Броня Бессмертного", "attack": 0, "defense": 25, "hp": 100, "crit": 0},
    ],
}

ACCESSORIES = {
    "common": [
        {"name": "Медное кольцо", "attack": 1, "defense": 1, "hp": 3, "crit": 0},
        {"name": "Кожаный браслет", "attack": 2, "defense": 0, "hp": 5, "crit": 0},
    ],
    "uncommon": [
        {"name": "Серебряное кольцо", "attack": 2, "defense": 2, "hp": 8, "crit": 1.0},
        {"name": "Амулет удачи", "attack": 1, "defense": 1, "hp": 5, "crit": 2.0},
    ],
    "rare": [
        {"name": "Кольцо мощи", "attack": 5, "defense": 3, "hp": 15, "crit": 1.0},
        {"name": "Браслет теней", "attack": 4, "defense": 1, "hp": 10, "crit": 4.0},
    ],
    "epic": [
        {"name": "Кольцо Дракона", "attack": 8, "defense": 5, "hp": 25, "crit": 3.0},
        {"name": "Печать Короля", "attack": 6, "defense": 6, "hp": 30, "crit": 2.0},
    ],
    "legendary": [
        {"name": "🔥 Перстень Всевластия", "attack": 15, "defense": 8, "hp": 40, "crit": 5.0},
        {"name": "💀 Ожерелье Смерти", "attack": 18, "defense": 3, "hp": 20, "crit": 8.0},
    ],
}


# ============ ГАЧА ============
GACHA_FREE_COST = 500
GACHA_PREM_COST = 50
GACHA_10X_COST = 450

GACHA_RATES_FREE = {"common": 50, "uncommon": 30, "rare": 15, "epic": 4, "legendary": 1}
GACHA_RATES_PREMIUM = {"uncommon": 30, "rare": 40, "epic": 25, "legendary": 5}


def _pick_rarity(rates: dict) -> str:
    roll = random.randint(1, 100)
    cumulative = 0
    for rarity, chance in rates.items():
        cumulative += chance
        if roll <= cumulative:
            return rarity
    return list(rates.keys())[-1]


def generate_item(rarity: str, item_type: str = None) -> dict:
    if not item_type:
        item_type = random.choice(["weapon", "armor", "accessory"])
    templates = {"weapon": WEAPONS, "armor": ARMORS, "accessory": ACCESSORIES}
    pool = templates[item_type].get(rarity, templates[item_type]["common"])
    base = random.choice(pool)

    def vary(val):
        if val == 0: return 0
        return max(1, int(val * random.uniform(0.85, 1.15)))

    return {
        "item_type": item_type, "name": base["name"], "rarity": rarity,
        "bonus_attack": vary(base["attack"]), "bonus_defense": vary(base["defense"]),
        "bonus_hp": vary(base["hp"]), "bonus_crit": round(base["crit"] * random.uniform(0.9, 1.1), 1),
    }


def gacha_pull(is_premium=False):
    rarity = _pick_rarity(GACHA_RATES_PREMIUM if is_premium else GACHA_RATES_FREE)
    return generate_item(rarity)


def gacha_pull_10x():
    items = [gacha_pull(is_premium=True) for _ in range(10)]
    if not any(i["rarity"] in ("epic", "legendary") for i in items):
        items[-1] = generate_item(random.choice(["epic", "legendary"]))
    return items


# ============ БОЕВАЯ СИСТЕМА ============

def simulate_combat(attacker: dict, defender: dict, user_skills: dict = None) -> dict:
    """
    Симуляция боя с поддержкой скиллов
    user_skills: {skill_id: {"level": int, "order": int}}
    """
    atk_hp = attacker.get("hp", attacker.get("max_hp", 100))
    atk_max_hp = attacker.get("max_hp", atk_hp)
    def_hp = defender["hp"]
    log, total_dealt, total_received, crits, rounds = [], 0, 0, 0, 0
    
    # Инициализация скиллов
    active_skills = {}  # {skill_id: {"cooldown": int, "effect": dict, "duration": int}}
    skill_cooldowns = {}  # {skill_id: int}
    skill_durations = {}  # {skill_id: int}
    dot_effects = {}  # {skill_id: {"damage": int, "turns_left": int}}
    
    if user_skills:
        # Сортируем скиллы по порядку
        sorted_skills = sorted(user_skills.items(), key=lambda x: x[1]["order"])
        for skill_id, skill_data in sorted_skills:
            skill_stats = get_skill_stats(skill_id, skill_data["level"])
            skill_cooldowns[skill_id] = 0  # Начинаем с готовности
    
    # Активные эффекты от скиллов
    active_effects = {
        "damage_multiplier": 1.0,
        "defense_multiplier": 1.0,
        "attack_multiplier": 1.0,
        "guaranteed_crit": False,
    }

    while atk_hp > 0 and def_hp > 0 and rounds < 25:
        rounds += 1
        
        # Применяем DoT эффекты
        for skill_id, dot in list(dot_effects.items()):
            dot_dmg = int(def_hp * dot["damage"])
            def_hp -= dot_dmg
            total_dealt += dot_dmg
            dot["turns_left"] -= 1
            if dot["turns_left"] <= 0:
                del dot_effects[skill_id]
            log.append(f"☠️ {SKILLS[skill_id]['name']}: -{dot_dmg} HP врагу")
        
        # Проверяем использование скиллов (автоматически по порядку)
        skill_used = False
        if user_skills:
            sorted_skills = sorted(user_skills.items(), key=lambda x: x[1]["order"])
            for skill_id, skill_data in sorted_skills:
                if skill_cooldowns.get(skill_id, 999) <= 0:
                    skill = SKILLS.get(skill_id, {})
                    skill_stats = get_skill_stats(skill_id, skill_data["level"])
                    effect = skill_stats["effect"]
                    
                    if skill["type"] == "damage_boost":
                        active_effects["damage_multiplier"] = effect["damage_multiplier"]
                        skill_durations[skill_id] = effect.get("duration", 1)
                        skill_cooldowns[skill_id] = skill_stats["cooldown"]
                        log.append(f"⚡ {skill['name']} активирован!")
                        skill_used = True
                        break
                    elif skill["type"] == "defense_boost":
                        active_effects["defense_multiplier"] = effect["defense_multiplier"]
                        skill_durations[skill_id] = effect.get("duration", 1)
                        skill_cooldowns[skill_id] = skill_stats["cooldown"]
                        log.append(f"🛡 {skill['name']} активирован!")
                        skill_used = True
                        break
                    elif skill["type"] == "heal":
                        heal_amount = int(atk_max_hp * effect["heal_percent"])
                        atk_hp = min(atk_max_hp, atk_hp + heal_amount)
                        skill_cooldowns[skill_id] = skill_stats["cooldown"]
                        log.append(f"💚 {skill['name']}: +{heal_amount} HP")
                        skill_used = True
                        break
                    elif skill["type"] == "guaranteed_crit":
                        active_effects["guaranteed_crit"] = True
                        skill_durations[skill_id] = 1
                        skill_cooldowns[skill_id] = skill_stats["cooldown"]
                        log.append(f"⚡ {skill['name']} активирован!")
                        skill_used = True
                        break
                    elif skill["type"] == "berserker":
                        active_effects["attack_multiplier"] = effect["attack_multiplier"]
                        active_effects["defense_multiplier"] = effect["defense_multiplier"]
                        skill_durations[skill_id] = effect.get("duration", 2)
                        skill_cooldowns[skill_id] = skill_stats["cooldown"]
                        log.append(f"🔥 {skill['name']} активирован!")
                        skill_used = True
                        break
                    elif skill["type"] == "dot":
                        dot_effects[skill_id] = {
                            "damage": effect["dot_percent"],
                            "turns_left": effect.get("duration", 3)
                        }
                        skill_cooldowns[skill_id] = skill_stats["cooldown"]
                        log.append(f"☠️ {skill['name']} применён!")
                        skill_used = True
                        break
        
        # Атака игрока
        base_dmg = attacker["attack"] * random.uniform(0.8, 1.2)
        base_dmg *= active_effects["damage_multiplier"] * active_effects["attack_multiplier"]
        is_crit = active_effects["guaranteed_crit"] or (random.random() * 100 < attacker.get("crit", 5))
        if is_crit:
            base_dmg *= 2
            crits += 1
        dmg = max(1, int(base_dmg - defender["defense"] * 0.3))
        def_hp -= dmg
        total_dealt += dmg
        crit_emoji = "💥" if is_crit else ""
        skill_emoji = "⚡" if skill_used else ""
        log.append(f"⚔️ Ты: -{dmg} HP{crit_emoji}{skill_emoji}")
        
        # Сбрасываем guaranteed_crit после использования
        if active_effects["guaranteed_crit"]:
            active_effects["guaranteed_crit"] = False
        
        if def_hp <= 0:
            break
        
        # Атака врага
        base_defense = attacker["defense"] * active_effects["defense_multiplier"]
        dmg_b = max(1, int(defender["attack"] * random.uniform(0.8, 1.2) - base_defense * 0.3))
        atk_hp -= dmg_b
        total_received += dmg_b
        log.append(f"👹 Враг: -{dmg_b} HP")
        
        # Обновляем кулдауны и длительность эффектов
        for skill_id in skill_cooldowns:
            if skill_cooldowns[skill_id] > 0:
                skill_cooldowns[skill_id] -= 1
        
        for skill_id in list(skill_durations.keys()):
            skill_durations[skill_id] -= 1
            if skill_durations[skill_id] <= 0:
                del skill_durations[skill_id]
                # Сбрасываем эффекты
                if skill_id in user_skills:
                    skill = SKILLS.get(skill_id, {})
                    if skill.get("type") == "damage_boost":
                        active_effects["damage_multiplier"] = 1.0
                    elif skill.get("type") == "defense_boost":
                        active_effects["defense_multiplier"] = 1.0
                    elif skill.get("type") == "berserker":
                        active_effects["attack_multiplier"] = 1.0
                        active_effects["defense_multiplier"] = 1.0

    return {
        "won": def_hp <= 0, "rounds": rounds, "log": log[:10],
        "damage_dealt": total_dealt, "damage_received": total_received,
        "crits": crits, "hp_left": max(0, atk_hp), "hp_max": atk_max_hp,
    }


def get_total_stats(base: dict, equip: dict) -> dict:
    return {
        "hp": base["max_hp"] + equip.get("hp", 0),
        "attack": base["attack"] + equip.get("attack", 0),
        "defense": base["defense"] + equip.get("defense", 0),
        "crit": base["crit"] + equip.get("crit", 0),
    }


# ============ РАСШИРЕННЫЕ СЛОТЫ ЭКИПИРОВКИ ============
TYPE_EMOJI = {
    "weapon": "🗡", "armor": "🛡", "helmet": "⛑", "gloves": "🧤",
    "boots": "👢", "ring": "💍", "amulet": "🔮", "cloak": "🧥", "accessory": "✨"
}
TYPE_NAMES = {
    "weapon": "Оружие", "armor": "Броня", "helmet": "Шлем", "gloves": "Перчатки",
    "boots": "Сапоги", "ring": "Кольцо", "amulet": "Амулет", "cloak": "Плащ", "accessory": "Аксессуар"
}
EQUIPMENT_SLOTS = ["weapon", "armor", "helmet", "gloves", "boots", "ring", "amulet", "cloak", "accessory"]

def hp_bar(cur, mx, length=10):
    r = max(0, min(1, cur / mx)) if mx > 0 else 0
    f = int(r * length)
    return "█" * f + "░" * (length - f)

def format_item_short(item):
    return f"{TYPE_EMOJI.get(item.get('item_type',''),'📦')} {RARITY_EMOJI.get(item.get('rarity','common'),'⚪')} {item.get('name','???')}"

def format_item_stats(item):
    p = []
    if item.get("bonus_attack", 0): p.append(f"+{item['bonus_attack']}ATK")
    if item.get("bonus_defense", 0): p.append(f"+{item['bonus_defense']}DEF")
    if item.get("bonus_hp", 0): p.append(f"+{item['bonus_hp']}HP")
    if item.get("bonus_crit", 0): p.append(f"+{item['bonus_crit']}%КР")
    return ", ".join(p) if p else "—"

def try_drop_item(zone_id):
    zone = next((z for z in ZONES if z["id"] == zone_id), None)
    if not zone: return None
    if random.randint(1, 100) > zone["drop_chance"]: return None
    return generate_item(_pick_rarity(zone["drop_rates"]))


# ============ НОВЫЕ ТИПЫ ПРЕДМЕТОВ ============
HELMETS = {
    "common": [{"name": "Кожаный колпак", "attack": 0, "defense": 2, "hp": 5, "crit": 0}],
    "uncommon": [{"name": "Железный шлем", "attack": 0, "defense": 4, "hp": 10, "crit": 0}],
    "rare": [{"name": "Рыцарский шлем", "attack": 1, "defense": 6, "hp": 15, "crit": 0}],
    "epic": [{"name": "Драконий шлем", "attack": 2, "defense": 10, "hp": 25, "crit": 1.0}],
    "legendary": [{"name": "🔥 Корона Бога", "attack": 5, "defense": 15, "hp": 40, "crit": 2.0}],
}

GLOVES = {
    "common": [{"name": "Кожаные перчатки", "attack": 1, "defense": 1, "hp": 3, "crit": 0.5}],
    "uncommon": [{"name": "Железные перчатки", "attack": 2, "defense": 2, "hp": 5, "crit": 1.0}],
    "rare": [{"name": "Боевые перчатки", "attack": 3, "defense": 3, "hp": 8, "crit": 1.5}],
    "epic": [{"name": "Перчатки Дракона", "attack": 5, "defense": 5, "hp": 15, "crit": 2.0}],
    "legendary": [{"name": "🔥 Перчатки Титана", "attack": 8, "defense": 8, "hp": 25, "crit": 3.0}],
}

BOOTS = {
    "common": [{"name": "Кожаные сапоги", "attack": 0, "defense": 2, "hp": 5, "crit": 0}],
    "uncommon": [{"name": "Железные сапоги", "attack": 1, "defense": 3, "hp": 8, "crit": 0.5}],
    "rare": [{"name": "Рыцарские сапоги", "attack": 1, "defense": 5, "hp": 12, "crit": 1.0}],
    "epic": [{"name": "Сапоги Ветра", "attack": 2, "defense": 7, "hp": 20, "crit": 2.0}],
    "legendary": [{"name": "🔥 Сапоги Молнии", "attack": 4, "defense": 10, "hp": 30, "crit": 3.0}],
}

RINGS = {
    "common": [{"name": "Медное кольцо", "attack": 1, "defense": 1, "hp": 3, "crit": 0.5}],
    "uncommon": [{"name": "Серебряное кольцо", "attack": 2, "defense": 2, "hp": 5, "crit": 1.0}],
    "rare": [{"name": "Золотое кольцо", "attack": 3, "defense": 3, "hp": 8, "crit": 1.5}],
    "epic": [{"name": "Кольцо Дракона", "attack": 5, "defense": 5, "hp": 15, "crit": 2.5}],
    "legendary": [{"name": "🔥 Кольцо Всевластия", "attack": 8, "defense": 8, "hp": 25, "crit": 4.0}],
}

AMULETS = {
    "common": [{"name": "Деревянный амулет", "attack": 0, "defense": 1, "hp": 5, "crit": 1.0}],
    "uncommon": [{"name": "Каменный амулет", "attack": 1, "defense": 2, "hp": 8, "crit": 1.5}],
    "rare": [{"name": "Магический амулет", "attack": 2, "defense": 3, "hp": 12, "crit": 2.0}],
    "epic": [{"name": "Амулет Бездны", "attack": 4, "defense": 5, "hp": 20, "crit": 3.0}],
    "legendary": [{"name": "🔥 Амулет Вечности", "attack": 7, "defense": 7, "hp": 35, "crit": 5.0}],
}

CLOAKS = {
    "common": [{"name": "Тряпичный плащ", "attack": 0, "defense": 1, "hp": 3, "crit": 0}],
    "uncommon": [{"name": "Кожаный плащ", "attack": 1, "defense": 2, "hp": 5, "crit": 0.5}],
    "rare": [{"name": "Магический плащ", "attack": 2, "defense": 4, "hp": 10, "crit": 1.5}],
    "epic": [{"name": "Плащ Теней", "attack": 3, "defense": 6, "hp": 18, "crit": 2.5}],
    "legendary": [{"name": "🔥 Плащ Бога", "attack": 6, "defense": 10, "hp": 30, "crit": 4.0}],
}


def generate_item(rarity: str, item_type: str = None) -> dict:
    """Генерирует предмет с поддержкой всех типов"""
    if not item_type:
        item_type = random.choice(EQUIPMENT_SLOTS)
    
    templates = {
        "weapon": WEAPONS, "armor": ARMORS, "helmet": HELMETS, "gloves": GLOVES,
        "boots": BOOTS, "ring": RINGS, "amulet": AMULETS, "cloak": CLOAKS,
        "accessory": ACCESSORIES
    }
    pool = templates[item_type].get(rarity, templates[item_type]["common"])
    base = random.choice(pool)

    def vary(val):
        if val == 0: return 0
        return max(1, int(val * random.uniform(0.85, 1.15)))

    base_atk = vary(base["attack"])
    base_def = vary(base["defense"])
    base_hp = vary(base["hp"])
    base_crit = round(base["crit"] * random.uniform(0.9, 1.1), 1)
    
    return {
        "item_type": item_type, "name": base["name"], "rarity": rarity,
        "bonus_attack": base_atk, "bonus_defense": base_def,
        "bonus_hp": base_hp, "bonus_crit": base_crit,
        "item_level": 1,  # Уровень предмета для прокачки
        # Базовые статы для прокачки
        "base_attack": base_atk, "base_defense": base_def,
        "base_hp": base_hp, "base_crit": base_crit,
    }


# ============ ПРОФЕССИИ ============
PROFESSIONS = {
    "blacksmith": {
        "name": "⚒️ Кузнец",
        "desc": "Улучшает оружие и броню. Снижает стоимость прокачки на 20%.",
        "bonus": "Скидка 20% на прокачку",
        "daily_gold": 150,
    },
    "alchemist": {
        "name": "🧪 Алхимик",
        "desc": "Создаёт зелья и эликсиры. Получает бонусные кристаллы.",
        "bonus": "+5 кристаллов в день",
        "daily_crystals": 5,
    },
    "merchant": {
        "name": "💰 Торговец",
        "desc": "Мастер торговли. Продаёт предметы дороже на 30%.",
        "bonus": "+30% к продаже",
        "sell_bonus": 1.3,
    },
    "hunter": {
        "name": "🏹 Охотник",
        "desc": "Эксперт по охоте. Получает больше золота и XP с монстров.",
        "bonus": "+25% золота и XP",
        "hunt_bonus": 1.25,
    },
}


def get_profession_bonus(profession_id: str) -> dict:
    """Получить бонусы профессии"""
    prof = PROFESSIONS.get(profession_id, {})
    return {
        "daily_gold": prof.get("daily_gold", 0),
        "daily_crystals": prof.get("daily_crystals", 0),
        "sell_bonus": prof.get("sell_bonus", 1.0),
        "hunt_bonus": prof.get("hunt_bonus", 1.0),
        "upgrade_discount": 0.2 if profession_id == "blacksmith" else 0.0,
    }


# ============ ПРОКАЧКА ОРУЖИЯ ============
MAX_ITEM_LEVEL = 20
UPGRADE_COST_BASE = 50  # Базовая стоимость за уровень
UPGRADE_COST_MULTIPLIER = 1.5  # Множитель за каждый уровень


def get_upgrade_cost(item_level: int, rarity: str, profession_discount: float = 0.0) -> int:
    """Стоимость прокачки предмета"""
    rarity_mult = {"common": 1.0, "uncommon": 1.5, "rare": 2.5, "epic": 4.0, "legendary": 7.0}
    mult = rarity_mult.get(rarity, 1.0)
    cost = int(UPGRADE_COST_BASE * (UPGRADE_COST_MULTIPLIER ** (item_level - 1)) * mult)
    return int(cost * (1.0 - profession_discount))


def get_upgrade_stats(item_level: int, base_stats: dict) -> dict:
    """Статы предмета после прокачки"""
    # +5% статов за уровень
    multiplier = 1.0 + (item_level - 1) * 0.05
    
    def boost(val):
        if val == 0: return 0
        return max(1, int(val * multiplier))
    
    return {
        "bonus_attack": boost(base_stats.get("bonus_attack", 0)),
        "bonus_defense": boost(base_stats.get("bonus_defense", 0)),
        "bonus_hp": boost(base_stats.get("bonus_hp", 0)),
        "bonus_crit": round(base_stats.get("bonus_crit", 0) * multiplier, 1),
    }


# ============ НОВЫЕ ЛОКАЦИИ (6 ШТУК) ============
NEW_ZONES = [
    {
        "id": 9, "name": "🏔️ Горные вершины", "min_level": 120,
        "monsters": [
            {"name": "Горный тролль", "emoji": "⛰️", "hp": 3500, "attack": 320, "defense": 160, "xp": 2500, "gold": 2200},
            {"name": "Орёл-хищник", "emoji": "🦅", "hp": 2800, "attack": 380, "defense": 140, "xp": 2700, "gold": 2400},
            {"name": "Ледяной дракон", "emoji": "🐉", "hp": 4200, "attack": 350, "defense": 180, "xp": 3000, "gold": 2600},
            {"name": "Горный дух", "emoji": "👻", "hp": 3000, "attack": 400, "defense": 150, "xp": 3200, "gold": 2800},
            {"name": "Титан скал", "emoji": "🗿", "hp": 5000, "attack": 300, "defense": 200, "xp": 3500, "gold": 3000},
        ],
        "boss": {"name": "🔴 Повелитель гор", "hp": 8000, "attack": 500, "defense": 220, "xp": 6000, "gold": 5500},
        "drop_chance": 35, "drop_rates": {"epic": 30, "legendary": 70},
    },
    {
        "id": 10, "name": "🌊 Морские глубины", "min_level": 140,
        "monsters": [
            {"name": "Кракен", "emoji": "🐙", "hp": 4500, "attack": 380, "defense": 170, "xp": 3800, "gold": 3400},
            {"name": "Морской змей", "emoji": "🐍", "hp": 5000, "attack": 360, "defense": 190, "xp": 4000, "gold": 3600},
            {"name": "Сирена", "emoji": "🧜‍♀️", "hp": 3500, "attack": 420, "defense": 150, "xp": 4200, "gold": 3800},
            {"name": "Акула-демон", "emoji": "🦈", "hp": 4800, "attack": 400, "defense": 180, "xp": 4400, "gold": 4000},
            {"name": "Повелитель глубин", "emoji": "🌊", "hp": 5500, "attack": 370, "defense": 200, "xp": 4600, "gold": 4200},
        ],
        "boss": {"name": "🔴 Левиафан", "hp": 10000, "attack": 550, "defense": 240, "xp": 8000, "gold": 7500},
        "drop_chance": 38, "drop_rates": {"epic": 25, "legendary": 75},
    },
    {
        "id": 11, "name": "🌌 Звёздное небо", "min_level": 160,
        "monsters": [
            {"name": "Космический дракон", "emoji": "🐲", "hp": 6000, "attack": 450, "defense": 200, "xp": 5000, "gold": 4500},
            {"name": "Нейтронная звезда", "emoji": "⭐", "hp": 5500, "attack": 500, "defense": 180, "xp": 5200, "gold": 4700},
            {"name": "Квазар", "emoji": "💫", "hp": 6500, "attack": 430, "defense": 220, "xp": 5400, "gold": 4900},
            {"name": "Чёрная дыра", "emoji": "🕳️", "hp": 7000, "attack": 400, "defense": 250, "xp": 5600, "gold": 5100},
            {"name": "Бог космоса", "emoji": "🌠", "hp": 7500, "attack": 480, "defense": 230, "xp": 5800, "gold": 5300},
        ],
        "boss": {"name": "🔴 Создатель вселенной", "hp": 15000, "attack": 700, "defense": 300, "xp": 12000, "gold": 11000},
        "drop_chance": 40, "drop_rates": {"legendary": 100},
    },
    {
        "id": 12, "name": "🔥 Адские врата", "min_level": 180,
        "monsters": [
            {"name": "Демон-палач", "emoji": "😈", "hp": 8000, "attack": 550, "defense": 250, "xp": 6500, "gold": 6000},
            {"name": "Адский пёс", "emoji": "🐕", "hp": 7500, "attack": 580, "defense": 240, "xp": 6700, "gold": 6200},
            {"name": "Повелитель ада", "emoji": "👹", "hp": 9000, "attack": 520, "defense": 280, "xp": 6900, "gold": 6400},
            {"name": "Сатана", "emoji": "😡", "hp": 8500, "attack": 600, "defense": 260, "xp": 7100, "gold": 6600},
            {"name": "Владыка тьмы", "emoji": "🌑", "hp": 10000, "attack": 540, "defense": 300, "xp": 7300, "gold": 6800},
        ],
        "boss": {"name": "🔴 Люцифер", "hp": 20000, "attack": 800, "defense": 350, "xp": 15000, "gold": 14000},
        "drop_chance": 42, "drop_rates": {"legendary": 100},
    },
    {
        "id": 13, "name": "✨ Райские сады", "min_level": 200,
        "monsters": [
            {"name": "Архангел", "emoji": "👼", "hp": 10000, "attack": 600, "defense": 300, "xp": 8000, "gold": 7500},
            {"name": "Серафим", "emoji": "🌟", "hp": 9500, "attack": 650, "defense": 290, "xp": 8200, "gold": 7700},
            {"name": "Херувим", "emoji": "✨", "hp": 11000, "attack": 580, "defense": 320, "xp": 8400, "gold": 7900},
            {"name": "Божественный страж", "emoji": "🛡️", "hp": 10500, "attack": 620, "defense": 310, "xp": 8600, "gold": 8100},
            {"name": "Верховный ангел", "emoji": "👑", "hp": 12000, "attack": 640, "defense": 330, "xp": 8800, "gold": 8300},
        ],
        "boss": {"name": "🔴 Бог", "hp": 25000, "attack": 900, "defense": 400, "xp": 20000, "gold": 18000},
        "drop_chance": 45, "drop_rates": {"legendary": 100},
    },
    {
        "id": 14, "name": "🌀 Измерение Хаоса", "min_level": 250,
        "monsters": [
            {"name": "Хаос-элементаль", "emoji": "🌀", "hp": 15000, "attack": 750, "defense": 350, "xp": 10000, "gold": 9500},
            {"name": "Время-пожиратель", "emoji": "⏰", "hp": 14000, "attack": 800, "defense": 340, "xp": 10500, "gold": 10000},
            {"name": "Пространство-разрушитель", "emoji": "🌌", "hp": 16000, "attack": 720, "defense": 380, "xp": 11000, "gold": 10500},
            {"name": "Абсолютное зло", "emoji": "💀", "hp": 17000, "attack": 780, "defense": 360, "xp": 11500, "gold": 11000},
            {"name": "Верховный хаос", "emoji": "⚡", "hp": 18000, "attack": 760, "defense": 400, "xp": 12000, "gold": 11500},
        ],
        "boss": {"name": "🔴 Абсолют", "hp": 50000, "attack": 1200, "defense": 500, "xp": 50000, "gold": 50000},
        "drop_chance": 50, "drop_rates": {"legendary": 100},
    },
]

# Добавляем новые локации к существующим
ZONES.extend(NEW_ZONES)

# ============ СКИЛЛЫ ============
SKILLS = {
    "power_strike": {
        "name": "💥 Мощный удар",
        "desc": "Увеличивает урон на 50% на 1 ход",
        "type": "damage_boost",
        "cooldown": 3,  # Ходов до следующего использования
        "effect": {"damage_multiplier": 1.5, "duration": 1},
        "max_level": 10,
        "cost_per_level": 100,  # Золота за уровень
    },
    "shield": {
        "name": "🛡 Щит",
        "desc": "Уменьшает получаемый урон на 30% на 1 ход",
        "type": "defense_boost",
        "cooldown": 4,
        "effect": {"defense_multiplier": 0.7, "duration": 1},
        "max_level": 10,
        "cost_per_level": 100,
    },
    "heal": {
        "name": "💚 Лечение",
        "desc": "Восстанавливает 20% от максимального HP",
        "type": "heal",
        "cooldown": 5,
        "effect": {"heal_percent": 0.2},
        "max_level": 10,
        "cost_per_level": 120,
    },
    "critical_strike": {
        "name": "⚡ Критический удар",
        "desc": "Гарантированный критический удар (x2 урона)",
        "type": "guaranteed_crit",
        "cooldown": 4,
        "effect": {"guaranteed_crit": True},
        "max_level": 10,
        "cost_per_level": 150,
    },
    "berserker_rage": {
        "name": "🔥 Ярость берсерка",
        "desc": "+30% к атаке и -20% к защите на 2 хода",
        "type": "berserker",
        "cooldown": 6,
        "effect": {"attack_multiplier": 1.3, "defense_multiplier": 0.8, "duration": 2},
        "max_level": 10,
        "cost_per_level": 130,
    },
    "poison": {
        "name": "☠ Яд",
        "desc": "Наносит 10% от урона врагу каждый ход (3 хода)",
        "type": "dot",
        "cooldown": 5,
        "effect": {"dot_percent": 0.1, "duration": 3},
        "max_level": 10,
        "cost_per_level": 110,
    },
}

def get_skill_stats(skill_id: str, level: int) -> dict:
    """Возвращает статистику скилла на определённом уровне"""
    skill = SKILLS.get(skill_id, {})
    if not skill:
        return {}
    
    base_effect = skill.get("effect", {}).copy()
    
    # Улучшение эффектов с уровнем
    if skill["type"] == "damage_boost":
        base_effect["damage_multiplier"] = 1.5 + (level - 1) * 0.05
    elif skill["type"] == "defense_boost":
        base_effect["defense_multiplier"] = max(0.3, 0.7 - (level - 1) * 0.03)
    elif skill["type"] == "heal":
        base_effect["heal_percent"] = 0.2 + (level - 1) * 0.02
    elif skill["type"] == "berserker":
        base_effect["attack_multiplier"] = 1.3 + (level - 1) * 0.03
    elif skill["type"] == "dot":
        base_effect["dot_percent"] = 0.1 + (level - 1) * 0.01
        base_effect["duration"] = 3 + (level - 1) // 3
    
    # Уменьшение кулдауна с уровнем
    cooldown = max(1, skill.get("cooldown", 3) - (level - 1) // 2)
    
    return {
        "effect": base_effect,
        "cooldown": cooldown,
        "current_cooldown": 0,
    }

# ============ ЗЕЛЬЯ ============
POTIONS = {
    "hp_small": {
        "name": "🧪 Малое зелье HP",
        "type": "hp",
        "restore": 50,
        "cost": 100,
        "emoji": "🧪",
        "description": "Восстанавливает 50 HP",
    },
    "hp_medium": {
        "name": "🧪 Среднее зелье HP",
        "type": "hp",
        "restore": 150,
        "cost": 250,
        "emoji": "🧪",
        "description": "Восстанавливает 150 HP",
    },
    "hp_large": {
        "name": "🧪 Большое зелье HP",
        "type": "hp",
        "restore": 300,
        "cost": 500,
        "emoji": "🧪",
        "description": "Восстанавливает 300 HP",
    },
    "hp_epic": {
        "name": "🧪 Эпическое зелье HP",
        "type": "hp",
        "restore": 500,
        "cost": 800,
        "emoji": "🧪",
        "description": "Восстанавливает 500 HP",
    },
    "mp_small": {
        "name": "💙 Малое зелье MP",
        "type": "mp",
        "restore": 30,
        "cost": 80,
        "emoji": "💙",
        "description": "Восстанавливает 30 MP",
    },
    "mp_medium": {
        "name": "💙 Среднее зелье MP",
        "type": "mp",
        "restore": 80,
        "cost": 200,
        "emoji": "💙",
        "description": "Восстанавливает 80 MP",
    },
    "mp_large": {
        "name": "💙 Большое зелье MP",
        "type": "mp",
        "restore": 150,
        "cost": 400,
        "emoji": "💙",
        "description": "Восстанавливает 150 MP",
    },
    "xp_boost": {
        "name": "✨ Зелье опыта",
        "type": "xp_boost",
        "multiplier": 1.5,
        "duration_minutes": 60,
        "cost": 300,
        "emoji": "✨",
        "description": "+50% XP на 1 час",
    },
    "gold_boost": {
        "name": "💰 Зелье золота",
        "type": "gold_boost",
        "multiplier": 1.5,
        "duration_minutes": 60,
        "cost": 350,
        "emoji": "💰",
        "description": "+50% золота на 1 час",
    },
    "luck_potion": {
        "name": "🍀 Зелье удачи",
        "type": "luck",
        "drop_chance_bonus": 10,
        "duration_minutes": 120,
        "cost": 400,
        "emoji": "🍀",
        "description": "+10% к шансу дропа на 2 часа",
    },
}

# ============ ПРЕМИУМ БОНУСЫ ============
PREMIUM_BONUSES = {
    "xp_multiplier": 1.5,  # +50% XP
    "gold_multiplier": 1.5,  # +50% золота
    "drop_chance_bonus": 15,  # +15% к шансу дропа
    "crystals_per_day": 10,  # +10 кристаллов в день
    "daily_gold_bonus": 200,  # +200 золота в день
}
