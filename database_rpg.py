"""
🗄 База данных MMO RPG v3
Игроки, инвентарь (9 слотов), профессии, уровни предметов, квесты, башня, экспедиции, аукцион
"""
import aiosqlite
from datetime import datetime, timedelta
from config_rpg import DATABASE_PATH


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '', first_name TEXT DEFAULT '',
            class TEXT DEFAULT '', race TEXT DEFAULT '', level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0,
            gold INTEGER DEFAULT 500, crystals INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 100, max_energy INTEGER DEFAULT 100, energy_updated_at TEXT DEFAULT '',
            current_hp INTEGER DEFAULT 0, max_hp INTEGER DEFAULT 0,
            arena_rating INTEGER DEFAULT 1000, arena_wins INTEGER DEFAULT 0, arena_losses INTEGER DEFAULT 0,
            arena_fights_today INTEGER DEFAULT 0, arena_last_reset TEXT DEFAULT '',
            total_hunts INTEGER DEFAULT 0, total_kills INTEGER DEFAULT 0,
            tower_floor INTEGER DEFAULT 0, tower_attempts_today INTEGER DEFAULT 0, tower_last_reset TEXT DEFAULT '',
            profession TEXT DEFAULT '', profession_level INTEGER DEFAULT 1, profession_xp INTEGER DEFAULT 0,
            character_image_url TEXT DEFAULT '', daily_streak INTEGER DEFAULT 0, last_daily TEXT DEFAULT '',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            item_type TEXT, name TEXT, rarity TEXT,
            bonus_attack INTEGER DEFAULT 0, bonus_defense INTEGER DEFAULT 0,
            bonus_hp INTEGER DEFAULT 0, bonus_crit REAL DEFAULT 0,
            item_level INTEGER DEFAULT 1, base_attack INTEGER DEFAULT 0, base_defense INTEGER DEFAULT 0,
            base_hp INTEGER DEFAULT 0, base_crit REAL DEFAULT 0,
            image_url TEXT DEFAULT '', is_equipped INTEGER DEFAULT 0, obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            quest_type TEXT, description TEXT, target INTEGER, progress INTEGER DEFAULT 0,
            reward_gold INTEGER DEFAULT 0, reward_crystals INTEGER DEFAULT 0, reward_xp INTEGER DEFAULT 0,
            is_completed INTEGER DEFAULT 0, is_claimed INTEGER DEFAULT 0, date TEXT
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS expeditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            exp_type TEXT, duration_minutes INTEGER, started_at TEXT,
            reward_gold INTEGER DEFAULT 0, reward_xp INTEGER DEFAULT 0,
            reward_crystals INTEGER DEFAULT 0, reward_item_rarity TEXT DEFAULT '',
            is_collected INTEGER DEFAULT 0
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS auction (
            id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER,
            item_name TEXT, item_type TEXT, item_rarity TEXT,
            item_attack INTEGER DEFAULT 0, item_defense INTEGER DEFAULT 0,
            item_hp INTEGER DEFAULT 0, item_crit REAL DEFAULT 0, item_level INTEGER DEFAULT 1,
            price INTEGER, listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS premium (
            user_id INTEGER PRIMARY KEY,
            is_active INTEGER DEFAULT 0,
            expires_at TEXT DEFAULT '',
            activated_at TEXT DEFAULT ''
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS potions (
            user_id INTEGER,
            potion_type TEXT,
            quantity INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, potion_type)
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS skills (
            user_id INTEGER, skill_id TEXT, level INTEGER DEFAULT 1,
            skill_order INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, skill_id)
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS active_effects (
            user_id INTEGER,
            effect_type TEXT,
            multiplier REAL DEFAULT 1.0,
            bonus INTEGER DEFAULT 0,
            expires_at TEXT,
            PRIMARY KEY (user_id, effect_type)
        )""")
        await db.commit()


# ======== ИГРОКИ ========
async def get_player(user_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def create_player(user_id: int, username: str, first_name: str, class_id: str, race_id: str = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute("""INSERT OR IGNORE INTO players
            (user_id, username, first_name, class, race, energy_updated_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, username, first_name, class_id, race_id, now))
        await db.commit()

async def update_player_race(user_id: int, race_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET race=? WHERE user_id=?", (race_id, user_id))
        await db.commit()

async def update_player_class(user_id: int, class_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET class=? WHERE user_id=?", (class_id, user_id))
        await db.commit()

async def update_character_image(user_id: int, image_url: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET character_image_url=? WHERE user_id=?", (image_url, user_id))
        await db.commit()

async def set_player_hp(user_id: int, current_hp: int, max_hp: int = None):
    """Устанавливает HP игрока"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if max_hp is not None:
            await db.execute("UPDATE players SET current_hp=?, max_hp=? WHERE user_id=?", (current_hp, max_hp, user_id))
        else:
            await db.execute("UPDATE players SET current_hp=? WHERE user_id=?", (current_hp, user_id))
        await db.commit()

async def restore_hp(user_id: int, amount: int) -> int:
    """Восстанавливает HP игрока, возвращает новое значение HP"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT current_hp, max_hp FROM players WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if not row: return 0
        current_hp, max_hp = row[0] or 0, row[1] or 0
        new_hp = min(max_hp, current_hp + amount)
        await db.execute("UPDATE players SET current_hp=? WHERE user_id=?", (new_hp, user_id))
        await db.commit()
        return new_hp

async def get_current_hp(user_id: int) -> tuple[int, int]:
    """Возвращает (current_hp, max_hp) игрока"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT current_hp, max_hp FROM players WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if not row: return (0, 0)
        return (row[0] or 0, row[1] or 0)

async def update_player_name(user_id: int, username: str, first_name: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET username=?, first_name=? WHERE user_id=?",
            (username, first_name, user_id))
        await db.commit()

# ======== ПРОФЕССИИ ========
async def set_profession(user_id: int, profession_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET profession=?, profession_level=1, profession_xp=0 WHERE user_id=?",
            (profession_id, user_id))
        await db.commit()

async def add_profession_xp(user_id: int, xp: int):
    """Добавить XP профессии"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET profession_xp=profession_xp+? WHERE user_id=?", (xp, user_id))
        await db.commit()
        # Проверка повышения уровня профессии (100 XP за уровень)
        cur = await db.execute("SELECT profession_xp, profession_level FROM players WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if row and row[0] >= row[1] * 100:
            await db.execute("UPDATE players SET profession_level=profession_level+1, profession_xp=0 WHERE user_id=?", (user_id,))
            await db.commit()
            return True
    return False

# ======== ЭНЕРГИЯ ========
def calculate_energy(player: dict) -> int:
    stored, max_e = player["energy"], player["max_energy"]
    if stored >= max_e: return max_e
    updated = player.get("energy_updated_at", "")
    if not updated: return stored
    try:
        elapsed = (datetime.now() - datetime.fromisoformat(updated)).total_seconds() / 60.0
        return min(max_e, stored + int(elapsed / ENERGY_REGEN_MINUTES))
    except: return stored

async def spend_energy(user_id: int, amount: int, current: int):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET energy=?, energy_updated_at=? WHERE user_id=?",
            (current - amount, now, user_id))
        await db.commit()

async def set_energy(user_id: int, amount: int):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET energy=?, energy_updated_at=? WHERE user_id=?",
            (amount, now, user_id))
        await db.commit()

# ======== РЕСУРСЫ ========
async def add_gold(user_id: int, amount: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET gold=gold+? WHERE user_id=?", (amount, user_id))
        await db.commit()

async def add_crystals(user_id: int, amount: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (amount, user_id))
        await db.commit()

async def spend_gold(user_id: int, amount: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT gold FROM players WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if not row or row[0] < amount: return False
        await db.execute("UPDATE players SET gold=gold-? WHERE user_id=?", (amount, user_id))
        await db.commit()
        return True

async def spend_crystals(user_id: int, amount: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT crystals FROM players WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if not row or row[0] < amount: return False
        await db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (amount, user_id))
        await db.commit()
        return True

# ======== XP И УРОВЕНЬ ========
async def add_xp(user_id: int, xp: int) -> list:
    from game_data import xp_for_level
    player = await get_player(user_id)
    if not player: return []
    cur_xp, cur_lvl, new_levels = player["xp"] + xp, player["level"], []
    while cur_xp >= xp_for_level(cur_lvl):
        cur_xp -= xp_for_level(cur_lvl); cur_lvl += 1; new_levels.append(cur_lvl)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET xp=?, level=? WHERE user_id=?", (cur_xp, cur_lvl, user_id))
        await db.commit()
    return new_levels

async def record_hunt(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET total_hunts=total_hunts+1, total_kills=total_kills+1 WHERE user_id=?", (user_id,))
        await db.commit()

# ======== АРЕНА ========
async def get_arena_fights_left(user_id: int) -> int:
    from config import ARENA_FIGHTS_PER_DAY
    player = await get_player(user_id)
    if not player: return 0
    today = datetime.now().strftime("%Y-%m-%d")
    if player["arena_last_reset"] != today:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("UPDATE players SET arena_fights_today=0, arena_last_reset=? WHERE user_id=?", (today, user_id))
            await db.commit()
        return ARENA_FIGHTS_PER_DAY
    return max(0, ARENA_FIGHTS_PER_DAY - player["arena_fights_today"])

async def record_arena_fight(user_id: int, won: bool, rating_change: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if won:
            await db.execute("UPDATE players SET arena_wins=arena_wins+1,arena_fights_today=arena_fights_today+1,arena_rating=MAX(0,arena_rating+?) WHERE user_id=?", (rating_change, user_id))
        else:
            await db.execute("UPDATE players SET arena_losses=arena_losses+1,arena_fights_today=arena_fights_today+1,arena_rating=MAX(0,arena_rating-?) WHERE user_id=?", (abs(rating_change), user_id))
        await db.commit()

async def get_arena_opponent(user_id: int) -> dict | None:
    player = await get_player(user_id)
    if not player: return None
    lvl = player["level"]
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM players WHERE user_id!=? AND class!='' AND level BETWEEN ? AND ? ORDER BY RANDOM() LIMIT 1", (user_id, max(1,lvl-5), lvl+5))
        row = await cur.fetchone()
        if row: return dict(row)
        cur = await db.execute("SELECT * FROM players WHERE user_id!=? AND class!='' ORDER BY RANDOM() LIMIT 1", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

# ======== БАШНЯ ========
async def get_tower_attempts(user_id: int) -> int:
    from config import TOWER_ATTEMPTS_PER_DAY
    player = await get_player(user_id)
    if not player: return 0
    today = datetime.now().strftime("%Y-%m-%d")
    if player["tower_last_reset"] != today:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("UPDATE players SET tower_attempts_today=0,tower_last_reset=? WHERE user_id=?", (today, user_id))
            await db.commit()
        return TOWER_ATTEMPTS_PER_DAY
    return max(0, TOWER_ATTEMPTS_PER_DAY - player["tower_attempts_today"])

async def use_tower_attempt(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET tower_attempts_today=tower_attempts_today+1 WHERE user_id=?", (user_id,))
        await db.commit()

async def advance_tower(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET tower_floor=tower_floor+1 WHERE user_id=?", (user_id,))
        await db.commit()

# ======== ИНВЕНТАРЬ (С УРОВНЯМИ) ========
async def add_item(user_id: int, item: dict) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Базовые статы (для прокачки) или текущие если базовых нет
        base_atk = item.get("base_attack", item.get("bonus_attack", 0))
        base_def = item.get("base_defense", item.get("bonus_defense", 0))
        base_hp = item.get("base_hp", item.get("bonus_hp", 0))
        base_crit = item.get("base_crit", item.get("bonus_crit", 0))
        
        cur = await db.execute("""INSERT INTO inventory 
            (user_id, item_type, name, rarity, bonus_attack, bonus_defense, bonus_hp, bonus_crit,
             item_level, base_attack, base_defense, base_hp, base_crit, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, item["item_type"], item["name"], item["rarity"],
             item.get("bonus_attack", 0), item.get("bonus_defense", 0),
             item.get("bonus_hp", 0), item.get("bonus_crit", 0),
             item.get("item_level", 1),
             base_atk, base_def, base_hp, base_crit,
             item.get("image_url", "")))
        await db.commit()
        return cur.lastrowid

async def update_item_image(item_id: int, image_url: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE inventory SET image_url=? WHERE id=?", (image_url, item_id))
        await db.commit()

async def get_inventory(user_id: int) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM inventory WHERE user_id=? ORDER BY is_equipped DESC, rarity DESC, id", (user_id,))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

async def get_item(item_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM inventory WHERE id=?", (item_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def upgrade_item(item_id: int, new_level: int, new_stats: dict):
    """Улучшить предмет"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""UPDATE inventory SET 
            item_level=?, bonus_attack=?, bonus_defense=?, bonus_hp=?, bonus_crit=?
            WHERE id=?""",
            (new_level, new_stats["bonus_attack"], new_stats["bonus_defense"],
             new_stats["bonus_hp"], new_stats["bonus_crit"], item_id))
        await db.commit()

async def equip_item(user_id: int, item_id: int):
    item = await get_item(item_id)
    if not item or item["user_id"] != user_id: return
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE inventory SET is_equipped=0 WHERE user_id=? AND item_type=? AND is_equipped=1",
            (user_id, item["item_type"]))
        await db.execute("UPDATE inventory SET is_equipped=1 WHERE id=? AND user_id=?", (item_id, user_id))
        await db.commit()

async def sell_item(user_id: int, item_id: int) -> int:
    from game_data import SELL_PRICES
    item = await get_item(item_id)
    if not item or item["user_id"] != user_id or item["is_equipped"]: return 0
    # Бонус за уровень предмета
    base_price = SELL_PRICES.get(item["rarity"], 30)
    level_bonus = int(base_price * 0.1 * (item.get("item_level", 1) - 1))
    gold = base_price + level_bonus
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM inventory WHERE id=?", (item_id,))
        await db.execute("UPDATE players SET gold=gold+? WHERE user_id=?", (gold, user_id))
        await db.commit()
    return gold

async def get_equipment_bonuses(user_id: int) -> dict:
    """Получить суммарные бонусы от всей экипировки (9 слотов)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("""SELECT
            COALESCE(SUM(bonus_attack), 0) as attack,
            COALESCE(SUM(bonus_defense), 0) as defense,
            COALESCE(SUM(bonus_hp), 0) as hp,
            COALESCE(SUM(bonus_crit), 0) as crit
            FROM inventory
            WHERE user_id = ? AND is_equipped = 1""", (user_id,))
        row = await cur.fetchone()
        return {"attack": row[0], "defense": row[1], "hp": row[2], "crit": row[3]}

async def get_equipped_items(user_id: int) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM inventory WHERE user_id=? AND is_equipped=1", (user_id,))
        return [dict(r) for r in await cur.fetchall()]

async def count_inventory(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM inventory WHERE user_id=?", (user_id,))
        return (await cur.fetchone())[0]

async def get_items_by_rarity(user_id: int, rarity: str) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM inventory WHERE user_id=? AND rarity=? AND is_equipped=0 ORDER BY id", (user_id, rarity))
        return [dict(r) for r in await cur.fetchall()]

async def delete_items(item_ids: list):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for iid in item_ids:
            await db.execute("DELETE FROM inventory WHERE id=?", (iid,))
        await db.commit()

# ======== КВЕСТЫ ========
async def get_daily_quests(user_id: int) -> list:
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM quests WHERE user_id=? AND date=?", (user_id, today))
        return [dict(r) for r in await cur.fetchall()]

async def create_daily_quests(user_id: int, quests: list):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for q in quests:
            desc = q["desc"].replace("{t}", str(q["target"]))
            await db.execute("""INSERT INTO quests 
                (user_id, quest_type, description, target, reward_gold, reward_crystals, reward_xp, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, q["type"], desc, q["target"], q["gold"], q["crystals"], q["xp"], today))
        await db.commit()

async def update_quest_progress(user_id: int, quest_type: str, amount: int = 1):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""UPDATE quests SET progress=MIN(progress+?, target),
            is_completed=CASE WHEN progress+?>=target THEN 1 ELSE 0 END
            WHERE user_id=? AND quest_type=? AND date=? AND is_claimed=0""",
            (amount, amount, user_id, quest_type, today))
        await db.commit()

async def claim_quest(user_id: int, quest_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM quests WHERE id=? AND user_id=? AND is_completed=1 AND is_claimed=0",
            (quest_id, user_id))
        q = await cur.fetchone()
        if not q: return None
        q = dict(q)
        await db.execute("UPDATE quests SET is_claimed=1 WHERE id=?", (quest_id,))
        await db.execute("UPDATE players SET gold=gold+?, crystals=crystals+? WHERE user_id=?",
            (q["reward_gold"], q["reward_crystals"], user_id))
        await db.commit()
        return q

# ======== ЭКСПЕДИЦИИ ========
async def get_active_expedition(user_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM expeditions WHERE user_id=? AND is_collected=0 ORDER BY id DESC LIMIT 1", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def start_expedition(user_id: int, exp_type: str, duration: int, rewards: dict):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""INSERT INTO expeditions 
            (user_id, exp_type, duration_minutes, started_at, reward_gold, reward_xp, reward_crystals, reward_item_rarity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, exp_type, duration, now, rewards["gold"], rewards["xp"], rewards["crystals"], rewards.get("item_rarity", "")))
        await db.commit()

def is_expedition_done(expedition: dict) -> bool:
    try:
        started = datetime.fromisoformat(expedition["started_at"])
        return datetime.now() >= started + timedelta(minutes=expedition["duration_minutes"])
    except: return False

def expedition_time_left(expedition: dict) -> str:
    try:
        started = datetime.fromisoformat(expedition["started_at"])
        end = started + timedelta(minutes=expedition["duration_minutes"])
        left = end - datetime.now()
        if left.total_seconds() <= 0: return "Готово!"
        mins = int(left.total_seconds() / 60)
        if mins >= 60: return f"{mins//60}ч {mins%60}мин"
        return f"{mins}мин"
    except: return "?"

async def collect_expedition(user_id: int, exp_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE expeditions SET is_collected=1 WHERE id=? AND user_id=?", (exp_id, user_id))
        await db.commit()

# ======== АУКЦИОН ========
async def list_on_auction(seller_id: int, item_id: int, price: int) -> bool:
    item = await get_item(item_id)
    if not item or item["user_id"] != seller_id or item["is_equipped"]: return False
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""INSERT INTO auction 
            (seller_id, item_name, item_type, item_rarity, item_attack, item_defense, item_hp, item_crit, item_level, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (seller_id, item["name"], item["item_type"], item["rarity"],
             item["bonus_attack"], item["bonus_defense"], item["bonus_hp"], item["bonus_crit"],
             item.get("item_level", 1), price))
        await db.execute("DELETE FROM inventory WHERE id=?", (item_id,))
        await db.commit()
    return True

async def get_auction_listings(limit: int = 20, offset: int = 0) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM auction ORDER BY listed_at DESC LIMIT ? OFFSET ?", (limit, offset))
        return [dict(r) for r in await cur.fetchall()]

async def get_my_listings(user_id: int) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM auction WHERE seller_id=?", (user_id,))
        return [dict(r) for r in await cur.fetchall()]

async def count_my_listings(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM auction WHERE seller_id=?", (user_id,))
        return (await cur.fetchone())[0]

async def buy_from_auction(buyer_id: int, listing_id: int) -> tuple[bool, str | dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM auction WHERE id=?", (listing_id,))
        listing = await cur.fetchone()
        if not listing: return False, "Лот не найден"
        listing = dict(listing)
        if listing["seller_id"] == buyer_id: return False, "Нельзя купить свой лот"
        cur = await db.execute("SELECT gold FROM players WHERE user_id=?", (buyer_id,))
        buyer = await cur.fetchone()
        if not buyer or buyer[0] < listing["price"]: return False, "Не хватает золота"
        await db.execute("UPDATE players SET gold=gold-? WHERE user_id=?", (listing["price"], buyer_id))
        seller_gold = int(listing["price"] * 0.9)
        await db.execute("UPDATE players SET gold=gold+? WHERE user_id=?", (seller_gold, listing["seller_id"]))
        await db.execute("""INSERT INTO inventory 
            (user_id, item_type, name, rarity, bonus_attack, bonus_defense, bonus_hp, bonus_crit, item_level,
             base_attack, base_defense, base_hp, base_crit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (buyer_id, listing["item_type"], listing["item_name"], listing["item_rarity"],
             listing["item_attack"], listing["item_defense"], listing["item_hp"], listing["item_crit"],
             listing.get("item_level", 1),
             listing["item_attack"], listing["item_defense"], listing["item_hp"], listing["item_crit"]))
        await db.execute("DELETE FROM auction WHERE id=?", (listing_id,))
        await db.commit()
    return True, listing

async def cancel_listing(user_id: int, listing_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM auction WHERE id=? AND seller_id=?", (listing_id, user_id))
        listing = await cur.fetchone()
        if not listing: return False
        listing = dict(listing)
        await db.execute("""INSERT INTO inventory 
            (user_id, item_type, name, rarity, bonus_attack, bonus_defense, bonus_hp, bonus_crit, item_level,
             base_attack, base_defense, base_hp, base_crit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, listing["item_type"], listing["item_name"], listing["item_rarity"],
             listing["item_attack"], listing["item_defense"], listing["item_hp"], listing["item_crit"],
             listing.get("item_level", 1),
             listing["item_attack"], listing["item_defense"], listing["item_hp"], listing["item_crit"]))
        await db.execute("DELETE FROM auction WHERE id=?", (listing_id,))
        await db.commit()
    return True

async def get_auction_count() -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM auction")
        return (await cur.fetchone())[0]

# ======== ЕЖЕДНЕВНЫЙ БОНУС ========
async def check_daily(user_id: int) -> dict | None:
    player = await get_player(user_id)
    if not player: return None
    today = datetime.now().strftime("%Y-%m-%d")
    if player["last_daily"] == today: return None
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    new_streak = player["daily_streak"] + 1 if player["last_daily"] == yesterday else 1
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET last_daily=?, daily_streak=? WHERE user_id=?",
            (today, new_streak, user_id))
        await db.commit()
    return {"daily_streak": new_streak}

# ======== ЛИДЕРБОРД ========
async def get_leaderboard_xp(limit: int = 10) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("""SELECT user_id, username, first_name, class, level, arena_rating, total_kills, tower_floor
            FROM players WHERE class!='' ORDER BY level DESC, arena_rating DESC LIMIT ?""", (limit,))
        rows = await cur.fetchall()
        return [{"user_id": r[0], "username": r[1], "first_name": r[2], "class": r[3], "level": r[4],
                 "arena_rating": r[5], "total_kills": r[6], "tower_floor": r[7]} for r in rows]

async def get_leaderboard_arena(limit: int = 10) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("""SELECT user_id, username, first_name, class, level, arena_rating, arena_wins, arena_losses
            FROM players WHERE class!='' ORDER BY arena_rating DESC LIMIT ?""", (limit,))
        rows = await cur.fetchall()
        return [{"user_id": r[0], "username": r[1], "first_name": r[2], "class": r[3], "level": r[4],
                 "arena_rating": r[5], "arena_wins": r[6], "arena_losses": r[7]} for r in rows]

async def get_player_rank(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("""SELECT COUNT(*)+1 FROM players
            WHERE class!='' AND (level>(SELECT level FROM players WHERE user_id=?)
                OR (level=(SELECT level FROM players WHERE user_id=?) AND arena_rating>(SELECT arena_rating FROM players WHERE user_id=?)))""",
            (user_id, user_id, user_id))
        return (await cur.fetchone())[0]

async def get_bot_stats() -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        t = (await (await db.execute("SELECT COUNT(*) FROM players WHERE class!=''")).fetchone())[0]
        h = (await (await db.execute("SELECT COALESCE(SUM(total_hunts),0) FROM players")).fetchone())[0]
        a = (await (await db.execute("SELECT COALESCE(SUM(arena_wins+arena_losses),0) FROM players")).fetchone())[0]
        return {"total_players": t, "total_hunts": h, "total_arena_fights": a}

# ======== ПРЕМИУМ ========
async def is_premium_active(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT expires_at FROM premium WHERE user_id=? AND is_active=1", (user_id,))
        row = await cur.fetchone()
        if not row: return False
        try:
            expires = datetime.fromisoformat(row[0])
            if datetime.now() >= expires:
                await db.execute("UPDATE premium SET is_active=0 WHERE user_id=?", (user_id,))
                await db.commit()
                return False
            return True
        except: return False

async def activate_premium(user_id: int, days: int):
    from datetime import timedelta
    now = datetime.now()
    expires = now + timedelta(days=days)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""INSERT OR REPLACE INTO premium 
            (user_id, is_active, expires_at, activated_at)
            VALUES (?, 1, ?, ?)""",
            (user_id, expires.isoformat(), now.isoformat()))
        await db.commit()

async def get_premium_info(user_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM premium WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

# ======== ЗЕЛЬЯ ========
async def add_potion(user_id: int, potion_type: str, quantity: int = 1):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""INSERT INTO potions (user_id, potion_type, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, potion_type) DO UPDATE SET quantity=quantity+?""",
            (user_id, potion_type, quantity, quantity))
        await db.commit()

async def get_potions(user_id: int) -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT potion_type, quantity FROM potions WHERE user_id=?", (user_id,))
        rows = await cur.fetchall()
        return {r[0]: r[1] for r in rows}

async def use_potion(user_id: int, potion_type: str) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT quantity FROM potions WHERE user_id=? AND potion_type=?", (user_id, potion_type))
        row = await cur.fetchone()
        if not row or row[0] <= 0: return False
        await db.execute("UPDATE potions SET quantity=quantity-1 WHERE user_id=? AND potion_type=?", (user_id, potion_type))
        await db.commit()
        return True

# ======== АКТИВНЫЕ ЭФФЕКТЫ ========
async def add_effect(user_id: int, effect_type: str, multiplier: float = 1.0, bonus: int = 0, duration_minutes: int = 60):
    from datetime import timedelta
    expires = datetime.now() + timedelta(minutes=duration_minutes)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""INSERT OR REPLACE INTO active_effects
            (user_id, effect_type, multiplier, bonus, expires_at)
            VALUES (?, ?, ?, ?, ?)""",
            (user_id, effect_type, multiplier, bonus, expires.isoformat()))
        await db.commit()

async def get_active_effects(user_id: int) -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM active_effects WHERE user_id=? AND expires_at > ?",
            (user_id, datetime.now().isoformat()))
        rows = await cur.fetchall()
        return {r["effect_type"]: dict(r) for r in rows}

async def cleanup_expired_effects():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM active_effects WHERE expires_at < ?", (datetime.now().isoformat(),))
        await db.commit()

# ======== СКИЛЛЫ ========
async def get_skills(user_id: int) -> dict:
    """Возвращает все скиллы игрока с уровнями и порядком"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT skill_id, level, skill_order FROM skills WHERE user_id=? ORDER BY skill_order", (user_id,))
        rows = await cur.fetchall()
        return {r[0]: {"level": r[1], "order": r[2]} for r in rows}

async def upgrade_skill(user_id: int, skill_id: str) -> bool:
    """Прокачивает скилл (добавляет если нет)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT level FROM skills WHERE user_id=? AND skill_id=?", (user_id, skill_id))
        row = await cur.fetchone()
        if row:
            await db.execute("UPDATE skills SET level=level+1 WHERE user_id=? AND skill_id=?", (user_id, skill_id))
        else:
            # Получаем максимальный порядок
            cur = await db.execute("SELECT MAX(skill_order) FROM skills WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            max_order = (row[0] or -1) + 1
            await db.execute("INSERT INTO skills (user_id, skill_id, level, skill_order) VALUES (?, ?, 1, ?)",
                (user_id, skill_id, max_order))
        await db.commit()
        return True

async def set_skill_order(user_id: int, skill_id: str, new_order: int):
    """Устанавливает порядок использования скилла"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE skills SET skill_order=? WHERE user_id=? AND skill_id=?", (new_order, user_id, skill_id))
        await db.commit()

async def reorder_skills(user_id: int, skill_orders: dict):
    """Обновляет порядок всех скиллов (skill_id -> order)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for skill_id, order in skill_orders.items():
            await db.execute("UPDATE skills SET skill_order=? WHERE user_id=? AND skill_id=?", (order, user_id, skill_id))
        await db.commit()
