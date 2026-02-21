"""
⚔️ Текстовая MMO RPG v2 — Telegram
Охота (8 зон, боссы), Арена PvP, Башня 100 этажей, Квесты,
Экспедиции (AFK), Колесо фортуны, Гача, Крафт, Аукцион, Магазин Stars
"""
import asyncio, logging, random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, LabeledPrice, PreCheckoutQuery
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import config_rpg as config, database_rpg as db
from game_data import (
    CLASSES, RACES, ZONES, RARITY_EMOJI, RARITY_NAMES, SELL_PRICES, TYPE_EMOJI, TYPE_NAMES, EQUIPMENT_SLOTS,
    EXPEDITIONS, WHEEL_PRIZES, UPGRADE_COSTS, UPGRADE_NEXT, AUCTION_PRICE_TIERS,
    PROFESSIONS, get_profession_bonus, MAX_ITEM_LEVEL, get_upgrade_cost, get_upgrade_stats,
    get_class_stats, get_available_zones, pick_monster, xp_for_level,
    simulate_combat, get_total_stats, gacha_pull, gacha_pull_10x,
    hp_bar, format_item_short, format_item_stats, try_drop_item,
    get_tower_monster, tower_rewards, generate_item, spin_wheel,
    generate_daily_quests, generate_expedition_rewards,
    GACHA_FREE_COST, GACHA_PREM_COST, GACHA_10X_COST,
    POTIONS, PREMIUM_BONUSES,
)
from image_generator import (
    generate_item_image, generate_character_image, get_item_image_prompt,
    GENERATE_IMAGES as IMG_ENABLED
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ======== КЛАВИАТУРЫ ========
def kb_main():
    return IKM(inline_keyboard=[
        [IKB(text="🗺 Охота", callback_data="hunt"), IKB(text="⚔️ Арена", callback_data="arena"), IKB(text="🏰 Башня", callback_data="tower")],
        [IKB(text="🌍 Экспедиция", callback_data="exped"), IKB(text="📜 Квесты", callback_data="quests")],
        [IKB(text="🎰 Призыв", callback_data="gacha"), IKB(text="🎡 Колесо", callback_data="wheel")],
        [IKB(text="📦 Инвентарь", callback_data="inv"), IKB(text="🧪 Зелья", callback_data="potions")],
        [IKB(text="⚒️ Профессия", callback_data="profession")],
        [IKB(text="🔧 Прокачка", callback_data="upgrade_item"), IKB(text="⛏️ Крафт", callback_data="upgrade")],
        [IKB(text="👤 Профиль", callback_data="prof"), IKB(text="🏆 Топ", callback_data="top")],
        [IKB(text="🏪 Обычный магазин", callback_data="shop"), IKB(text="👑 Премиум магазин", callback_data="premium_shop")],
        [IKB(text="🎪 Аукцион", callback_data="auc")],
    ])

def kb_back():
    return IKM(inline_keyboard=[[IKB(text="🏠 Меню", callback_data="menu")]])

async def get_combat_stats(user_id):
    player = await db.get_player(user_id)
    if not player: return {}
    return get_total_stats(
        get_class_stats(player["class"], player["level"], player.get("race")),
        await db.get_equipment_bonuses(user_id)
    )

async def track_quest(user_id, qtype, amount=1):
    await db.update_quest_progress(user_id, qtype, amount)

async def add_item_with_image(user_id: int, item: dict) -> int:
    """Добавляет предмет с генерацией изображения"""
    if config.GENERATE_IMAGES and not item.get("image_url"):
        try:
            img_url = await generate_item_image(item["name"], item["item_type"], item["rarity"])
            if img_url:
                item["image_url"] = img_url
        except Exception as e:
            logger.error(f"Ошибка генерации изображения предмета: {e}")
    try:
        item_id = await db.add_item(user_id, item)
        if item.get("image_url") and item_id:
            await db.update_item_image(item_id, item["image_url"])
        return item_id if item_id else 0
    except Exception as e:
        logger.error(f"Ошибка добавления предмета: {e}")
        return 0

# ======== /START ========
@dp.message(CommandStart())
async def cmd_start(msg: types.Message):
    player = await db.get_player(msg.from_user.id)
    if player and player["class"]:
        await db.update_player_name(msg.from_user.id, msg.from_user.username or "", msg.from_user.first_name or "")
        daily = await db.check_daily(msg.from_user.id)
        dt = ""
        if daily:
            ds = daily["daily_streak"]
            p = await db.get_player(msg.from_user.id)
            prof_bonus = get_profession_bonus(p.get("profession", "")) if p else {}
            is_prem = await db.is_premium_active(msg.from_user.id) if p else False
            bg = config.DAILY_GOLD + ds*10 + prof_bonus.get("daily_gold", 0)
            bc = config.DAILY_CRYSTALS + (1 if ds>=3 else 0) + prof_bonus.get("daily_crystals", 0)
            if is_prem:
                bg += PREMIUM_BONUSES["daily_gold_bonus"]
                bc += PREMIUM_BONUSES["crystals_per_day"]
            await db.add_gold(msg.from_user.id, bg); await db.add_crystals(msg.from_user.id, bc)
            prof_text = f" (+{prof_bonus.get('daily_gold',0)}💰 от профессии)" if prof_bonus.get("daily_gold") else ""
            prem_text = f" (+{PREMIUM_BONUSES['daily_gold_bonus']}💰 +{PREMIUM_BONUSES['crystals_per_day']}💎 от премиума)" if is_prem else ""
            dt = f"\n🌅 <b>Ежедневный бонус!</b> +{bg}💰 +{bc}💎 (📅{ds} дней){prof_text}{prem_text}\n"
        player = await db.get_player(msg.from_user.id)
        e = db.calculate_energy(player)
        cls = CLASSES[player["class"]]
        premium_text = ""
        if await db.is_premium_active(msg.from_user.id):
            premium_text = " 👑 ПРЕМИУМ"
        await msg.answer(f"{cls['name']} <b>{msg.from_user.first_name}</b>{premium_text} (Lv.{player['level']})\n💰{player['gold']} 💎{player['crystals']}{dt}\nВыбери действие:", reply_markup=kb_main())
    else:
        t = "⚔️ <b>Добро пожаловать в мир приключений!</b>\n\n<i>Сначала выбери расу, затем класс:</i>\n\n"
        t += "<b>Расы:</b>\n"
        for rid, r in RACES.items():
            t += f"{r['name']} — {r['desc']}\n"
        t += "\n<b>Классы:</b>\n"
        for cid, c in CLASSES.items():
            t += f"{c['name']} — {c['desc']}\n"
        await msg.answer(t, reply_markup=IKM(inline_keyboard=[
            [IKB(text="1️⃣ Выбрать расу", callback_data="race_select")],
            [IKB(text="2️⃣ Выбрать класс", callback_data="class_select")],
        ]))

@dp.callback_query(F.data == "race_select")
async def cb_race_select(cb: types.CallbackQuery):
    await cb.answer()
    player = await db.get_player(cb.from_user.id)
    if player and player.get("race"): await cb.answer("Раса уже выбрана!",show_alert=True); return
    t = "🧬 <b>Выбери расу:</b>\n\n"
    btns = []
    for rid, r in RACES.items():
        t += f"{r['name']}\n<i>{r['desc']}</i>\n"
        if r.get("bonus_hp"): t += f"❤️{r['bonus_hp']:+d} "
        if r.get("bonus_attack"): t += f"⚔️{r['bonus_attack']:+d} "
        if r.get("bonus_defense"): t += f"🛡{r['bonus_defense']:+d} "
        if r.get("bonus_crit"): t += f"💥{r['bonus_crit']:+.1f}%"
        t += "\n\n"
        btns.append([IKB(text=r['name'], callback_data=f"race_{rid}")])
    btns.append([IKB(text="🏠 Назад", callback_data="menu")])
    try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=btns))
    except: await cb.message.answer(t, reply_markup=IKM(inline_keyboard=btns))

@dp.callback_query(F.data.startswith("race_"))
async def cb_race(cb: types.CallbackQuery):
    rid = cb.data[5:]
    if rid not in RACES: await cb.answer("Ошибка!",show_alert=True); return
    player = await db.get_player(cb.from_user.id)
    if player and player.get("race"): await cb.answer("Раса уже выбрана!",show_alert=True); return
    await cb.answer()
    if not player:
        await db.create_player(cb.from_user.id, cb.from_user.username or "", cb.from_user.first_name or "", "", rid)
    else:
        await db.update_player_race(cb.from_user.id, rid)
    r = RACES[rid]
    await cb.message.edit_text(f"✅ <b>Раса выбрана: {r['name']}</b>\n\n<i>Теперь выбери класс!</i>", reply_markup=IKM(inline_keyboard=[[IKB(text="Выбрать класс", callback_data="class_select")]]))

@dp.callback_query(F.data == "class_select")
async def cb_class_select(cb: types.CallbackQuery):
    await cb.answer()
    player = await db.get_player(cb.from_user.id)
    if not player or not player.get("race"): await cb.answer("Сначала выбери расу!",show_alert=True); return
    if player.get("class"): await cb.answer("Класс уже выбран!",show_alert=True); return
    t = "⚔️ <b>Выбери класс:</b>\n\n"
    btns = []
    for cid, c in CLASSES.items():
        t += f"{c['name']}\n<i>{c['desc']}</i>\n❤️{c['base_hp']} ⚔️{c['base_attack']} 🛡{c['base_defense']} 💥{c['base_crit']}%\n\n"
        btns.append([IKB(text=c["name"], callback_data=f"cls_{cid}")])
    btns.append([IKB(text="🏠 Назад", callback_data="menu")])
    try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=btns))
    except: await cb.message.answer(t, reply_markup=IKM(inline_keyboard=btns))

@dp.callback_query(F.data.startswith("cls_"))
async def cb_cls(cb: types.CallbackQuery):
    cid = cb.data[4:]
    if cid not in CLASSES: await cb.answer("Ошибка!",show_alert=True); return
    player = await db.get_player(cb.from_user.id)
    if not player or not player.get("race"): await cb.answer("Сначала выбери расу!",show_alert=True); return
    if player.get("class"): await cb.answer("Уже есть персонаж!",show_alert=True); return
    await cb.answer()
    await db.create_player(cb.from_user.id, cb.from_user.username or "", cb.from_user.first_name or "", cid, player.get("race"))
    s = get_class_stats(cid, 1, player.get("race")); c = CLASSES[cid]; r = RACES[player.get("race")]
    
    # Генерируем изображение персонажа
    img_url = None
    if config.GENERATE_IMAGES:
        try:
            img_url = await generate_character_image(c["name"], r["name"])
            if img_url:
                await db.update_character_image(cb.from_user.id, img_url)
        except Exception as e:
            logger.error(f"Ошибка генерации изображения персонажа: {e}")
    
    text = f"🎉 <b>{r['name']} {c['name']} создан!</b>\n\n❤️{s['max_hp']} ⚔️{s['attack']} 🛡{s['defense']} 💥{s['crit']}%\n💰500 золота ⚡100 энергии\n\nУдачи! ⚔️"
    
    if img_url:
        try:
            await cb.message.answer_photo(img_url, caption=text, reply_markup=kb_main())
            await cb.message.delete()
        except:
            await cb.message.edit_text(text, reply_markup=kb_main())
    else:
        await cb.message.edit_text(text, reply_markup=kb_main())

@dp.callback_query(F.data == "menu")
async def cb_menu(cb: types.CallbackQuery):
    await cb.answer()
    player = await db.get_player(cb.from_user.id)
    if not player or not player["class"]:
        try: await cb.message.edit_text("Нажми /start!")
        except: pass
        return
    cls = CLASSES[player["class"]]
    premium_text = ""
    if await db.is_premium_active(cb.from_user.id):
        premium_text = " 👑 ПРЕМИУМ"
    t = f"{cls['name']} <b>{player['first_name']}</b>{premium_text} (Lv.{player['level']})\n💰{player['gold']} 💎{player['crystals']}"
    try: await cb.message.edit_text(t, reply_markup=kb_main())
    except: await cb.message.answer(t, reply_markup=kb_main())

# ======== ОХОТА ========
@dp.callback_query(F.data == "hunt")
async def cb_hunt(cb: types.CallbackQuery):
    await cb.answer()
    p = await db.get_player(cb.from_user.id)
    if not p or not p["class"]: return
    zones = get_available_zones(p["level"])
    btns = [[IKB(text=f"{z['name']} (Lv.{z['min_level']}+)", callback_data=f"hz_{z['id']}")] for z in zones]
    btns.append([IKB(text="🏠 Меню", callback_data="menu")])
    premium_bonus = ""
    if await db.is_premium_active(cb.from_user.id):
        premium_bonus = "\n👑 <b>Премиум активен!</b> +50% XP и золота!"
    try: await cb.message.edit_text(f"🗺 <b>Охота</b>{premium_bonus}\n\nВыбери зону:", reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data.startswith("hz_"))
async def cb_hz(cb: types.CallbackQuery):
    zid = int(cb.data[3:])
    uid = cb.from_user.id
    p = await db.get_player(uid)
    if not p: return
    zone = next((z for z in ZONES if z["id"]==zid), None)
    if not zone or p["level"]<zone["min_level"]: await cb.answer(f"Нужен Lv.{zone['min_level']}!",show_alert=True); return
    await cb.answer()
    monster, is_boss = pick_monster(zid)
    ps = await get_combat_stats(uid)
    ms = {"hp": monster["hp"], "attack": monster["attack"], "defense": monster["defense"], "crit": 5.0 if is_boss else 3.0}
    r = simulate_combat(ps, ms)
    boss_tag = " 👑БОСС!" if is_boss else ""
    if r["won"]:
        gold, xp = monster["gold"], monster["xp"]
        # Крит лут (10%)
        crit_loot = random.randint(1,100) <= 10
        if crit_loot: gold *= 2; xp = int(xp * 1.5)
        # Бонус охотника
        p = await db.get_player(uid)
        prof_bonus = get_profession_bonus(p.get("profession", ""))
        if prof_bonus.get("hunt_bonus", 1.0) > 1.0:
            gold = int(gold * prof_bonus["hunt_bonus"])
            xp = int(xp * prof_bonus["hunt_bonus"])
        # Бонус премиума
        is_prem = await db.is_premium_active(uid)
        if is_prem:
            gold = int(gold * PREMIUM_BONUSES["gold_multiplier"])
            xp = int(xp * PREMIUM_BONUSES["xp_multiplier"])
        # Активные эффекты
        effects = await db.get_active_effects(uid)
        if "xp_boost" in effects:
            xp = int(xp * effects["xp_boost"]["multiplier"])
        if "gold_boost" in effects:
            gold = int(gold * effects["gold_boost"]["multiplier"])
        await db.add_gold(uid, gold); lvls = await db.add_xp(uid, xp); await db.record_hunt(uid)
        # XP профессии охотнику
        if p.get("profession") == "hunter":
            await db.add_profession_xp(uid, 5)
        await track_quest(uid, "hunt")
        # Бонус премиума к дропу
        drop_chance_bonus = 0
        if is_prem:
            drop_chance_bonus = PREMIUM_BONUSES["drop_chance_bonus"]
        # Активный эффект удачи
        effects = await db.get_active_effects(uid)
        if "luck" in effects:
            drop_chance_bonus += effects["luck"]["bonus"]
        
        drop = None
        if drop_chance_bonus > 0:
            # Увеличиваем шанс дропа
            zone = next((z for z in ZONES if z["id"]==zid), None)
            if zone:
                base_chance = zone["drop_chance"]
                final_chance = min(100, base_chance + drop_chance_bonus)
                if random.randint(1, 100) <= final_chance:
                    drop = try_drop_item(zid)
        else:
            drop = try_drop_item(zid)
        
        dt = ""
        if drop:
            await add_item_with_image(uid, drop)
            prem_drop_text = " 👑" if is_prem else ""
            dt = f"\n🎁 <b>Дроп:</b>{prem_drop_text} {format_item_short(drop)} ({format_item_stats(drop)})"
        lt = ""
        for l in lvls:
            await db.add_gold(uid, config.GOLD_PER_LEVELUP); await db.add_crystals(uid, config.CRYSTALS_PER_LEVELUP)
            lt += f"\n🎉 <b>Уровень {l}!</b> +{config.GOLD_PER_LEVELUP}💰 +{config.CRYSTALS_PER_LEVELUP}💎"
        cl = crit_loot and "💎 <b>Критический лут! x2 золота!</b>\n" or ""
        log = "\n".join(r["log"][:5])
        prem_text = " 👑" if is_prem else ""
        t = f"⚔️ <b>{monster['emoji']} {monster['name']}</b>{boss_tag}{prem_text}\n\n{log}\n\n✅ <b>ПОБЕДА!</b> ({r['rounds']}р)\n❤️ {r['hp_left']}/{r['hp_max']} [{hp_bar(r['hp_left'],r['hp_max'])}]\n\n{cl}💰+{gold} ✨+{xp}XP{dt}{lt}"
    else:
        log = "\n".join(r["log"][:5])
        t = f"⚔️ <b>{monster['emoji']} {monster['name']}</b>{boss_tag}\n\n{log}\n\n❌ <b>ПОРАЖЕНИЕ!</b>\n💡 Улучши экипировку!"
    kb = IKM(inline_keyboard=[[IKB(text="🗺 Ещё", callback_data="hunt")],[IKB(text="🏠 Меню", callback_data="menu")]])
    try: await cb.message.edit_text(t, reply_markup=kb)
    except: await cb.message.answer(t, reply_markup=kb)

# ======== АРЕНА ========
@dp.callback_query(F.data == "arena")
async def cb_arena(cb: types.CallbackQuery):
    await cb.answer()
    p = await db.get_player(cb.from_user.id)
    if not p or not p["class"]: return
    fl = await db.get_arena_fights_left(cb.from_user.id)
    btns = []
    if fl > 0: btns.append([IKB(text="⚔️ Сразиться!", callback_data="afight")])
    btns += [[IKB(text="🏆 Рейтинг", callback_data="top_a")],[IKB(text="🏠 Меню", callback_data="menu")]]
    try: await cb.message.edit_text(f"⚔️ <b>Арена</b>\n🏅{p['arena_rating']} 🎫{fl}/{config.ARENA_FIGHTS_PER_DAY}\nW/L: {p['arena_wins']}/{p['arena_losses']}\n\nНаграда: 💰{config.ARENA_WIN_GOLD} 💎{config.ARENA_WIN_CRYSTALS}", reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data == "afight")
async def cb_afight(cb: types.CallbackQuery):
    uid = cb.from_user.id
    fl = await db.get_arena_fights_left(uid)
    if fl <= 0: await cb.answer("Бои закончились!",show_alert=True); return
    opp = await db.get_arena_opponent(uid)
    if not opp: await cb.answer("Нет противников!",show_alert=True); return
    await cb.answer()
    ms = await get_combat_stats(uid)
    ob = get_class_stats(opp["class"], opp["level"])
    oe = await db.get_equipment_bonuses(opp["user_id"])
    os_ = get_total_stats(ob, oe)
    r = simulate_combat(ms, os_)
    oc = CLASSES[opp["class"]]; on = opp["first_name"] or opp["username"] or "???"
    log = "\n".join(r["log"][:5])
    if r["won"]:
        await db.record_arena_fight(uid, True, config.ARENA_WIN_RATING)
        await db.add_gold(uid, config.ARENA_WIN_GOLD); await db.add_crystals(uid, config.ARENA_WIN_CRYSTALS)
        await track_quest(uid, "arena")
        t = f"⚔️ Ты vs {oc['name']} <b>{on}</b> (Lv.{opp['level']})\n\n{log}\n\n🏆 <b>ПОБЕДА!</b> ({r['rounds']}р)\n📈+{config.ARENA_WIN_RATING}рейтинга 💰+{config.ARENA_WIN_GOLD} 💎+{config.ARENA_WIN_CRYSTALS}"
    else:
        await db.record_arena_fight(uid, False, config.ARENA_LOSE_RATING)
        t = f"⚔️ Ты vs {oc['name']} <b>{on}</b> (Lv.{opp['level']})\n\n{log}\n\n❌ <b>ПОРАЖЕНИЕ!</b>\n📉-{config.ARENA_LOSE_RATING}рейтинга"
    try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=[[IKB(text="⚔️ Ещё",callback_data="afight")],[IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

# ======== БАШНЯ ========
@dp.callback_query(F.data == "tower")
async def cb_tower(cb: types.CallbackQuery):
    await cb.answer()
    p = await db.get_player(cb.from_user.id)
    if not p or not p["class"]: return
    att = await db.get_tower_attempts(cb.from_user.id)
    nf = p["tower_floor"] + 1
    m = get_tower_monster(nf)
    is_boss = nf % 10 == 0
    btns = []
    if att > 0: btns.append([IKB(text=f"⚔️ Штурм этаж {nf}{'👑' if is_boss else ''}", callback_data="tw_go")])
    btns.append([IKB(text="🏠 Меню", callback_data="menu")])
    try: await cb.message.edit_text(f"🏰 <b>Башня испытаний</b>\n\n📊 Текущий этаж: <b>{p['tower_floor']}</b>\n🎫 Попыток: {att}/{config.TOWER_ATTEMPTS_PER_DAY}\n\nСледующий: <b>Этаж {nf}</b>{'👑 БОСС!' if is_boss else ''}\n👹 {m['name']}\n❤️{m['hp']} ⚔️{m['attack']} 🛡{m['defense']}\n\n<i>Без затрат энергии!</i>", reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data == "tw_go")
async def cb_tw_go(cb: types.CallbackQuery):
    uid = cb.from_user.id
    att = await db.get_tower_attempts(uid)
    if att <= 0: await cb.answer("Попытки закончились!",show_alert=True); return
    await cb.answer()
    p = await db.get_player(uid); nf = p["tower_floor"] + 1
    m = get_tower_monster(nf); ps = await get_combat_stats(uid)
    ms = {"hp": m["hp"], "attack": m["attack"], "defense": m["defense"], "crit": m.get("crit",3)}
    r = simulate_combat(ps, ms)
    await db.use_tower_attempt(uid)
    log = "\n".join(r["log"][:5])
    if r["won"]:
        await db.advance_tower(uid)
        rw = tower_rewards(nf)
        await db.add_gold(uid, rw["gold"]); await db.add_crystals(uid, rw["crystals"])
        await db.add_xp(uid, rw["xp"])
        await track_quest(uid, "tower")
        dt = ""
        if rw["drop_item"]:
            item = generate_item(rw["drop_rarity"])
            await add_item_with_image(uid, item)
            dt = f"\n🎁 {format_item_short(item)} ({format_item_stats(item)})"
        t = f"🏰 <b>Этаж {nf}</b> — {m['name']}\n\n{log}\n\n✅ <b>ПРОЙДЕН!</b>\n💰+{rw['gold']} ✨+{rw['xp']}XP 💎+{rw['crystals']}{dt}"
    else:
        t = f"🏰 <b>Этаж {nf}</b> — {m['name']}\n\n{log}\n\n❌ <b>Не пройден!</b>\nСтань сильнее и попробуй снова!"
    try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=[[IKB(text="🏰 Башня",callback_data="tower")],[IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

# ======== КВЕСТЫ ========
@dp.callback_query(F.data == "quests")
async def cb_quests(cb: types.CallbackQuery):
    await cb.answer()
    uid = cb.from_user.id
    quests = await db.get_daily_quests(uid)
    if not quests:
        ql = generate_daily_quests(3)
        await db.create_daily_quests(uid, ql)
        quests = await db.get_daily_quests(uid)
    lines = ["📜 <b>Ежедневные квесты</b>\n"]
    btns = []
    for q in quests:
        status = "✅" if q["is_claimed"] else ("🟢" if q["is_completed"] else "⬜")
        lines.append(f"{status} {q['description']} [{q['progress']}/{q['target']}]")
        lines.append(f"   💰{q['reward_gold']} 💎{q['reward_crystals']} ✨{q['reward_xp']}XP")
        if q["is_completed"] and not q["is_claimed"]:
            btns.append([IKB(text=f"🎁 Забрать: {q['description']}", callback_data=f"qcl_{q['id']}")])
    btns.append([IKB(text="🏠 Меню", callback_data="menu")])
    try: await cb.message.edit_text("\n".join(lines), reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data.startswith("qcl_"))
async def cb_qclaim(cb: types.CallbackQuery):
    qid = int(cb.data[4:])
    q = await db.claim_quest(cb.from_user.id, qid)
    if not q: await cb.answer("Уже забрано!",show_alert=True); return
    await db.add_xp(cb.from_user.id, q["reward_xp"])
    await cb.answer(f"🎁 +{q['reward_gold']}💰 +{q['reward_crystals']}💎 +{q['reward_xp']}XP!", show_alert=True)
    # Обновить список
    await cb_quests(cb)

# ======== ЭКСПЕДИЦИИ ========
@dp.callback_query(F.data == "exped")
async def cb_exped(cb: types.CallbackQuery):
    await cb.answer()
    uid = cb.from_user.id
    active = await db.get_active_expedition(uid)
    if active:
        done = db.is_expedition_done(active)
        tl = db.expedition_time_left(active)
        exp = next((e for e in EXPEDITIONS if e["id"]==active["exp_type"]),None)
        name = exp["name"] if exp else "???"
        btns = []
        if done:
            btns.append([IKB(text="🎁 Забрать награду!", callback_data="exp_col")])
        btns.append([IKB(text="🏠 Меню", callback_data="menu")])
        t = f"🌍 <b>Экспедиция</b>\n\n📋 {name}\n⏰ {'✅ Готово!' if done else f'Осталось: {tl}'}\n\n{'Нажми чтобы забрать!' if done else 'Ожидай завершения...'}"
        try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=btns))
        except: pass
    else:
        btns = [[IKB(text=f"{e['name']} ({e['duration']}мин)", callback_data=f"exps_{e['id']}")] for e in EXPEDITIONS]
        btns.append([IKB(text="🏠 Меню", callback_data="menu")])
        t = "🌍 <b>Экспедиции</b>\n\n<i>Отправь героя в поход! Не тратит энергию.</i>\n<i>Дольше поход = лучше награда.</i>\n\nВыбери экспедицию:"
        try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=btns))
        except: pass

@dp.callback_query(F.data.startswith("exps_"))
async def cb_exp_start(cb: types.CallbackQuery):
    eid = cb.data[5:]
    exp = next((e for e in EXPEDITIONS if e["id"]==eid), None)
    if not exp: await cb.answer("Ошибка!",show_alert=True); return
    active = await db.get_active_expedition(cb.from_user.id)
    if active: await cb.answer("Уже есть активная экспедиция!",show_alert=True); return
    await cb.answer()
    rewards = generate_expedition_rewards(eid)
    await db.start_expedition(cb.from_user.id, eid, exp["duration"], rewards)
    t = f"🌍 <b>Экспедиция начата!</b>\n\n📋 {exp['name']}\n⏰ Длительность: {exp['duration']} мин\n\nВозвращайся позже за наградой!"
    try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=[[IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

@dp.callback_query(F.data == "exp_col")
async def cb_exp_collect(cb: types.CallbackQuery):
    uid = cb.from_user.id
    active = await db.get_active_expedition(uid)
    if not active or not db.is_expedition_done(active): await cb.answer("Ещё не готово!",show_alert=True); return
    await cb.answer()
    await db.collect_expedition(uid, active["id"])
    await db.add_gold(uid, active["reward_gold"]); await db.add_crystals(uid, active["reward_crystals"])
    await db.add_xp(uid, active["reward_xp"])
    await track_quest(uid, "expedition")
    dt = ""
    if active["reward_item_rarity"]:
        item = generate_item(active["reward_item_rarity"])
        await add_item_with_image(uid, item)
        dt = f"\n🎁 {format_item_short(item)} ({format_item_stats(item)})"
    t = f"🌍 <b>Экспедиция завершена!</b>\n\n💰+{active['reward_gold']} 💎+{active['reward_crystals']} ✨+{active['reward_xp']}XP{dt}"
    try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=[[IKB(text="🌍 Новая экспедиция",callback_data="exped")],[IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

# ======== КОЛЕСО ФОРТУНЫ ========
@dp.callback_query(F.data == "wheel")
async def cb_wheel(cb: types.CallbackQuery):
    await cb.answer()
    can = await db.can_spin_wheel(cb.from_user.id)
    btns = []
    if can: btns.append([IKB(text="🎡 Крутить!", callback_data="wspin")])
    btns.append([IKB(text="🏠 Меню", callback_data="menu")])
    st = "✅ Доступно!" if can else "❌ Уже крутил сегодня"
    try: await cb.message.edit_text(f"🎡 <b>Колесо фортуны</b>\n\nБесплатное вращение: {st}\n\nВозможные призы:\n💰 Золото • 💎 Кристаллы • ⚡ Энергия\n🟢🔵🟣🟡 Экипировка", reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data == "wspin")
async def cb_wspin(cb: types.CallbackQuery):
    uid = cb.from_user.id
    can = await db.can_spin_wheel(uid)
    if not can: await cb.answer("Уже крутил сегодня!",show_alert=True); return
    await cb.answer()
    await db.use_wheel_spin(uid)
    prize = spin_wheel()
    t = f"🎡 <b>Колесо крутится...</b>\n\n🎯 Выпало: <b>{prize['name']}</b>\n\n"
    if prize["type"] == "gold":
        await db.add_gold(uid, prize["amount"]); t += f"💰 +{prize['amount']} золота!"
    elif prize["type"] == "crystals":
        await db.add_crystals(uid, prize["amount"]); t += f"💎 +{prize['amount']} кристаллов!"
    elif prize["type"] == "energy":
        # Энергия больше не используется, заменяем на золото
        await db.add_gold(uid, prize["amount"] * 10); t += f"💰 +{prize['amount'] * 10} золота!"
    elif prize["type"] == "item":
        item = generate_item(prize["rarity"]); await add_item_with_image(uid, item)
        t += f"🎁 {format_item_short(item)}\n{format_item_stats(item)}"
    else:
        t += "Увы, в этот раз не повезло... 😤"
    try: await cb.message.edit_text(t, reply_markup=kb_back())
    except: pass

# ======== ГАЧА ========
@dp.callback_query(F.data == "gacha")
async def cb_gacha(cb: types.CallbackQuery):
    await cb.answer()
    p = await db.get_player(cb.from_user.id)
    if not p: return
    try: await cb.message.edit_text(f"🎰 <b>Призыв</b>\n💰{p['gold']} 💎{p['crystals']}\n\n🪙 Обычный — {GACHA_FREE_COST}💰\n  ⚪50% 🟢30% 🔵15% 🟣4% 🟡1%\n\n💎 Премиум — {GACHA_PREM_COST}💎\n  🟢30% 🔵40% 🟣25% 🟡5%\n\n💎 10x — {GACHA_10X_COST}💎 (гарантия 🟣+)", reply_markup=IKM(inline_keyboard=[
        [IKB(text=f"🪙 Обычный ({GACHA_FREE_COST}💰)",callback_data="gfree")],
        [IKB(text=f"💎 Премиум ({GACHA_PREM_COST}💎)",callback_data="gprem")],
        [IKB(text=f"💎 10x ({GACHA_10X_COST}💎)",callback_data="g10x")],
        [IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

@dp.callback_query(F.data == "gfree")
async def cb_gfree(cb: types.CallbackQuery):
    if not await db.spend_gold(cb.from_user.id, GACHA_FREE_COST): await cb.answer("Мало золота!",show_alert=True); return
    await cb.answer(); item = gacha_pull(False); await add_item_with_image(cb.from_user.id, item); await track_quest(cb.from_user.id, "gacha")
    try: await cb.message.edit_text(f"🎰 <b>Призыв!</b>\n\n{format_item_short(item)}\n{RARITY_EMOJI[item['rarity']]} {RARITY_NAMES[item['rarity']]}\n📊 {format_item_stats(item)}", reply_markup=IKM(inline_keyboard=[[IKB(text="🎰 Ещё",callback_data="gacha")],[IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

@dp.callback_query(F.data == "gprem")
async def cb_gprem(cb: types.CallbackQuery):
    if not await db.spend_crystals(cb.from_user.id, GACHA_PREM_COST): await cb.answer("Мало кристаллов!",show_alert=True); return
    await cb.answer(); item = gacha_pull(True); await add_item_with_image(cb.from_user.id, item); await track_quest(cb.from_user.id, "gacha")
    try: await cb.message.edit_text(f"💎 <b>Премиум призыв!</b>\n\n{format_item_short(item)}\n{RARITY_EMOJI[item['rarity']]} {RARITY_NAMES[item['rarity']]}\n📊 {format_item_stats(item)}", reply_markup=IKM(inline_keyboard=[[IKB(text="🎰 Ещё",callback_data="gacha")],[IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

@dp.callback_query(F.data == "g10x")
async def cb_g10x(cb: types.CallbackQuery):
    if not await db.spend_crystals(cb.from_user.id, GACHA_10X_COST): await cb.answer("Мало кристаллов!",show_alert=True); return
    await cb.answer(); items = gacha_pull_10x()
    lines = []
    for item in items:
        await add_item_with_image(cb.from_user.id, item); lines.append(f"{format_item_short(item)} — {format_item_stats(item)}")
    await track_quest(cb.from_user.id, "gacha", 10)
    try: await cb.message.edit_text(f"💎 <b>10x Призыв!</b>\n\n"+"\n".join(lines), reply_markup=IKM(inline_keyboard=[[IKB(text="📦 Инвентарь",callback_data="inv")],[IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

# ======== ИНВЕНТАРЬ ========
@dp.callback_query(F.data == "inv")
async def cb_inv(cb: types.CallbackQuery):
    await cb.answer(); await show_inv(cb.from_user.id, cb.message)

@dp.callback_query(F.data.startswith("invp_"))
async def cb_invp(cb: types.CallbackQuery):
    await cb.answer(); await show_inv(cb.from_user.id, cb.message, int(cb.data[5:]))

async def show_inv(uid, msg, page=1):
    items = await db.get_inventory(uid)
    if not items:
        try: await msg.edit_text("📦 <b>Пусто!</b>\nСходи на охоту или сделай призыв 🎰", reply_markup=IKM(inline_keyboard=[[IKB(text="🗺 Охота",callback_data="hunt"),IKB(text="🎰 Призыв",callback_data="gacha")],[IKB(text="🏠 Меню",callback_data="menu")]]))
        except: pass
        return
    eq = [i for i in items if i["is_equipped"]]; bag = [i for i in items if not i["is_equipped"]]
    lines = ["📦 <b>Инвентарь</b>\n"]
    if eq:
        lines.append("🔧 <b>Надето:</b>")
        for i in eq: lines.append(f"  {format_item_short(i)} — {format_item_stats(i)}")
        lines.append("")
    pp = 8; tp = max(1,(len(bag)+pp-1)//pp); page = max(1,min(page,tp))
    pi = bag[(page-1)*pp:page*pp]
    if pi: lines.append(f"🎒 <b>Сумка</b> ({len(bag)}):")
    for i in pi:
        lvl_text = f" Lv.{i['item_level']}" if i.get("item_level", 1) > 1 else ""
        lines.append(f"  {format_item_short(i)}{lvl_text} — {format_item_stats(i)}")
    btns = [[IKB(text=f"👆 {i['name']}", callback_data=f"itm_{i['id']}")] for i in pi]
    nav = []
    if page > 1: nav.append(IKB(text="◀️",callback_data=f"invp_{page-1}"))
    if tp > 1: nav.append(IKB(text=f"{page}/{tp}",callback_data="noop"))
    if page < tp: nav.append(IKB(text="▶️",callback_data=f"invp_{page+1}"))
    if nav: btns.append(nav)
    btns.append([IKB(text="🏠 Меню",callback_data="menu")])
    try: await msg.edit_text("\n".join(lines), reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data.startswith("itm_"))
async def cb_itm(cb: types.CallbackQuery):
    iid = int(cb.data[4:]); item = await db.get_item(iid)
    if not item or item["user_id"] != cb.from_user.id: await cb.answer("Не найдено!",show_alert=True); return
    await cb.answer()
    lvl = item.get("item_level", 1)
    sp = SELL_PRICES.get(item["rarity"], 30)
    level_bonus = int(sp * 0.1 * (lvl - 1))
    final_sell = sp + level_bonus
    btns = []
    if not item["is_equipped"]:
        btns.append([IKB(text="✅ Надеть",callback_data=f"eqp_{iid}"), IKB(text=f"💰 Продать ({final_sell}💰)",callback_data=f"sel_{iid}")])
        # Аукцион
        ap = final_sell * 3
        btns.append([IKB(text=f"🎪 На аукцион ({ap}💰)", callback_data=f"alst_{iid}")])
    else:
        if lvl < MAX_ITEM_LEVEL:
            p = await db.get_player(cb.from_user.id)
            prof_bonus = get_profession_bonus(p.get("profession", ""))
            cost = get_upgrade_cost(lvl, item["rarity"], prof_bonus.get("upgrade_discount", 0))
            btns.append([IKB(text=f"🔧 Прокачать Lv.{lvl}→{lvl+1} ({cost}💰)", callback_data=f"upitm_{iid}")])
    btns.append([IKB(text="📦 Назад",callback_data="inv")])
    lvl_text = f" Lv.{lvl}" if lvl > 1 else ""
    text = f"{format_item_short(item)}{lvl_text}\n\n{RARITY_EMOJI[item['rarity']]} {RARITY_NAMES[item['rarity']]}\n{TYPE_EMOJI.get(item['item_type'],'')} {TYPE_NAMES.get(item['item_type'],'')}\n📊 {format_item_stats(item)}\n💰 Продажа: {final_sell}💰"
    
    # Показываем изображение если есть
    img_url = item.get("image_url")
    if img_url:
        try:
            await cb.message.answer_photo(img_url, caption=text, reply_markup=IKM(inline_keyboard=btns))
            await cb.message.delete()
        except:
            try: await cb.message.edit_text(text, reply_markup=IKM(inline_keyboard=btns))
            except: pass
    else:
        # Генерируем изображение если включено
        if config.GENERATE_IMAGES and not item.get("image_url"):
            try:
                img_url = await generate_item_image(item["name"], item["item_type"], item["rarity"])
                if img_url:
                    await db.update_item_image(iid, img_url)
                    try:
                        await cb.message.answer_photo(img_url, caption=text, reply_markup=IKM(inline_keyboard=btns))
                        await cb.message.delete()
                        return
                    except:
                        try: await cb.message.edit_text(text, reply_markup=IKM(inline_keyboard=btns))
                        except: pass
                        return
            except Exception as e:
                logger.error(f"Ошибка генерации изображения: {e}")
        try: await cb.message.edit_text(text, reply_markup=IKM(inline_keyboard=btns))
        except: pass

@dp.callback_query(F.data.startswith("eqp_"))
async def cb_eqp(cb: types.CallbackQuery):
    iid = int(cb.data[4:]); await db.equip_item(cb.from_user.id, iid)
    await cb.answer("✅ Надето!",show_alert=True); await show_inv(cb.from_user.id, cb.message)

@dp.callback_query(F.data.startswith("sel_"))
async def cb_sel(cb: types.CallbackQuery):
    iid = int(cb.data[4:])
    item = await db.get_item(iid)
    if not item: await cb.answer("Ошибка!",show_alert=True); return
    
    # Базовая цена (из database_rpg уже с учётом уровня)
    base_gold = await db.sell_item(cb.from_user.id, iid)
    if not base_gold: await cb.answer("Ошибка!",show_alert=True); return
    
    # Бонус торговца применяем отдельно
    p = await db.get_player(cb.from_user.id)
    prof_bonus = get_profession_bonus(p.get("profession", ""))
    if prof_bonus.get("sell_bonus", 1.0) > 1.0:
        bonus_gold = int(base_gold * (prof_bonus["sell_bonus"] - 1.0))
        await db.add_gold(cb.from_user.id, bonus_gold)
        final_gold = base_gold + bonus_gold
        bonus_text = f" (+{bonus_gold}💰 бонус торговца)"
    else:
        final_gold = base_gold
        bonus_text = ""
    
    await track_quest(cb.from_user.id, "sell")
    await cb.answer(f"💰 Продано за {final_gold}💰{bonus_text}!",show_alert=True)
    # XP профессии торговцу
    if p.get("profession") == "merchant":
        await db.add_profession_xp(cb.from_user.id, 3)
    await show_inv(cb.from_user.id, cb.message)

# ======== УЛУЧШЕНИЕ (КРАФТ) ========
@dp.callback_query(F.data == "upgrade")
async def cb_upgrade(cb: types.CallbackQuery):
    await cb.answer()
    uid = cb.from_user.id
    inv = await db.get_inventory(uid)
    bag = [i for i in inv if not i["is_equipped"]]
    counts = {}
    for i in bag: counts[i["rarity"]] = counts.get(i["rarity"], 0) + 1
    lines = ["⛏️ <b>Улучшение экипировки</b>\n\n<i>Объедини 3 предмета одной редкости\nв 1 предмет следующей!</i>\n"]
    btns = []
    for r in ["common","uncommon","rare","epic"]:
        nr = UPGRADE_NEXT.get(r)
        if not nr: continue
        cnt = counts.get(r, 0)
        cost = UPGRADE_COSTS.get(r, 999)
        ok = cnt >= 3
        lines.append(f"3× {RARITY_EMOJI[r]} → 1× {RARITY_EMOJI[nr]} ({cost}💰) [{cnt}/3]")
        if ok: btns.append([IKB(text=f"⛏️ 3×{RARITY_EMOJI[r]} → {RARITY_EMOJI[nr]} ({cost}💰)", callback_data=f"upgr_{r}")])
    btns.append([IKB(text="🏠 Меню",callback_data="menu")])
    try: await cb.message.edit_text("\n".join(lines), reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data.startswith("upgr_"))
async def cb_upgr(cb: types.CallbackQuery):
    r = cb.data[5:]; nr = UPGRADE_NEXT.get(r); cost = UPGRADE_COSTS.get(r)
    if not nr or not cost: await cb.answer("Ошибка!",show_alert=True); return
    uid = cb.from_user.id
    items = await db.get_items_by_rarity(uid, r)
    if len(items) < 3: await cb.answer("Нужно 3 предмета!",show_alert=True); return
    if not await db.spend_gold(uid, cost): await cb.answer("Мало золота!",show_alert=True); return
    await cb.answer()
    to_delete = [i["id"] for i in items[:3]]
    await db.delete_items(to_delete)
    new_item = generate_item(nr)
    await add_item_with_image(uid, new_item)
    t = f"⛏️ <b>Улучшение!</b>\n\n3×{RARITY_EMOJI[r]} → {RARITY_EMOJI[nr]}\n\n🎁 Получен:\n{format_item_short(new_item)}\n📊 {format_item_stats(new_item)}\n\n💰 -{cost} золота"
    try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=[[IKB(text="⛏️ Ещё",callback_data="upgrade")],[IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

# ======== АУКЦИОН ========
@dp.callback_query(F.data == "auc")
async def cb_auc(cb: types.CallbackQuery):
    await cb.answer()
    cnt = await db.get_auction_count()
    try: await cb.message.edit_text(f"🎪 <b>Аукцион</b>\n\n📋 Лотов: {cnt}\n💰 Комиссия: 10%\n\nПокупай экипировку у других игроков!", reply_markup=IKM(inline_keyboard=[
        [IKB(text="🔍 Смотреть лоты",callback_data="auc_b")],
        [IKB(text="📋 Мои лоты",callback_data="auc_m")],
        [IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

@dp.callback_query(F.data.startswith("auc_b"))
async def cb_auc_browse(cb: types.CallbackQuery):
    await cb.answer()
    page = 1
    if cb.data.startswith("auc_bp_"): page = int(cb.data[7:])
    listings = await db.get_auction_listings(50)
    pp = 8; tp = max(1,(len(listings)+pp-1)//pp); page = max(1,min(page,tp))
    pl = listings[(page-1)*pp:page*pp]
    if not pl:
        try: await cb.message.edit_text("🎪 Аукцион пуст!", reply_markup=IKM(inline_keyboard=[[IKB(text="🎪 Назад",callback_data="auc")],[IKB(text="🏠 Меню",callback_data="menu")]]))
        except: pass
        return
    lines = [f"🎪 <b>Аукцион</b> ({len(listings)} лотов)\n"]
    btns = []
    for l in pl:
        re = RARITY_EMOJI.get(l["item_rarity"],"⚪"); te = TYPE_EMOJI.get(l["item_type"],"📦")
        lines.append(f"{te}{re} {l['item_name']} — <b>{l['price']}💰</b>")
        btns.append([IKB(text=f"💰 {l['item_name']} ({l['price']}💰)", callback_data=f"abuy_{l['id']}")])
    nav = []
    if page > 1: nav.append(IKB(text="◀️",callback_data=f"auc_bp_{page-1}"))
    if tp > 1: nav.append(IKB(text=f"{page}/{tp}",callback_data="noop"))
    if page < tp: nav.append(IKB(text="▶️",callback_data=f"auc_bp_{page+1}"))
    if nav: btns.append(nav)
    btns.append([IKB(text="🎪 Назад",callback_data="auc")])
    try: await cb.message.edit_text("\n".join(lines), reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data.startswith("abuy_"))
async def cb_abuy(cb: types.CallbackQuery):
    lid = int(cb.data[5:])
    ok, info = await db.buy_from_auction(cb.from_user.id, lid)
    if not ok: await cb.answer(str(info),show_alert=True); return
    await cb.answer(f"✅ Куплено: {info['item_name']}!", show_alert=True)
    await cb_auc_browse(cb)

@dp.callback_query(F.data == "auc_m")
async def cb_auc_my(cb: types.CallbackQuery):
    await cb.answer()
    listings = await db.get_my_listings(cb.from_user.id)
    if not listings:
        try: await cb.message.edit_text("📋 У тебя нет лотов.", reply_markup=IKM(inline_keyboard=[[IKB(text="🎪 Назад",callback_data="auc")],[IKB(text="🏠 Меню",callback_data="menu")]]))
        except: pass
        return
    lines = ["📋 <b>Мои лоты</b>\n"]
    btns = []
    for l in listings:
        re = RARITY_EMOJI.get(l["item_rarity"],"⚪")
        lines.append(f"{re} {l['item_name']} — {l['price']}💰")
        btns.append([IKB(text=f"❌ Снять {l['item_name']}", callback_data=f"acan_{l['id']}")])
    btns.append([IKB(text="🎪 Назад",callback_data="auc")])
    try: await cb.message.edit_text("\n".join(lines), reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data.startswith("acan_"))
async def cb_acan(cb: types.CallbackQuery):
    lid = int(cb.data[5:])
    ok = await db.cancel_listing(cb.from_user.id, lid)
    if not ok: await cb.answer("Ошибка!",show_alert=True); return
    await cb.answer("✅ Снято, предмет возвращён!", show_alert=True)
    await cb_auc_my(cb)

@dp.callback_query(F.data.startswith("alst_"))
async def cb_alst(cb: types.CallbackQuery):
    """Выставить на аукцион"""
    iid = int(cb.data[5:])
    item = await db.get_item(iid)
    if not item or item["user_id"] != cb.from_user.id: await cb.answer("Не найдено!",show_alert=True); return
    cnt = await db.count_my_listings(cb.from_user.id)
    if cnt >= config.AUCTION_MAX_LISTINGS: await cb.answer(f"Максимум {config.AUCTION_MAX_LISTINGS} лота!",show_alert=True); return
    price = SELL_PRICES.get(item["rarity"],30) * 3
    ok = await db.list_on_auction(cb.from_user.id, iid, price)
    if not ok: await cb.answer("Ошибка!",show_alert=True); return
    await cb.answer(f"🎪 Выставлено за {price}💰!", show_alert=True)
    await show_inv(cb.from_user.id, cb.message)

# ======== ЗЕЛЬЯ ========
@dp.callback_query(F.data == "potions")
async def cb_potions(cb: types.CallbackQuery):
    await cb.answer()
    uid = cb.from_user.id
    potions = await db.get_potions(uid)
    effects = await db.get_active_effects(uid)
    
    text = "🧪 <b>Мои зелья</b>\n\n"
    
    if not potions and not effects:
        text += "<i>У тебя нет зелий</i>\n\nКупи в обычном магазине!"
    else:
        if potions:
            text += "<b>В инвентаре:</b>\n"
            for pid, qty in potions.items():
                if qty > 0 and pid in POTIONS:
                    pot = POTIONS[pid]
                    text += f"{pot['emoji']} {pot['name']} — {qty} шт.\n"
            text += "\n"
        
        if effects:
            text += "<b>Активные эффекты:</b>\n"
            for etype, effect in effects.items():
                try:
                    expires = datetime.fromisoformat(effect["expires_at"])
                    mins_left = int((expires - datetime.now()).total_seconds() / 60)
                    if etype == "xp_boost":
                        text += f"✨ Зелье опыта — +{int((effect['multiplier']-1)*100)}% XP ({mins_left} мин)\n"
                    elif etype == "gold_boost":
                        text += f"💰 Зелье золота — +{int((effect['multiplier']-1)*100)}% золота ({mins_left} мин)\n"
                    elif etype == "luck":
                        text += f"🍀 Зелье удачи — +{effect['bonus']}% к дропу ({mins_left} мин)\n"
                except: pass
    
    btns = []
    if potions:
        for pid, qty in potions.items():
            if qty > 0 and pid in POTIONS:
                pot = POTIONS[pid]
                if pot["type"] in ("hp", "mp"):
                    btns.append([IKB(text=f"Использовать {pot['emoji']} {pot['name']} ({qty})", callback_data=f"use_pot_{pid}")])
    
    btns.append([IKB(text="🏪 Магазин", callback_data="shop")])
    btns.append([IKB(text="🏠 Меню", callback_data="menu")])
    
    try: await cb.message.edit_text(text, reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data.startswith("use_pot_"))
async def cb_use_potion(cb: types.CallbackQuery):
    pid = cb.data[8:]
    if pid not in POTIONS: await cb.answer("Ошибка!", show_alert=True); return
    pot = POTIONS[pid]
    
    if not await db.use_potion(cb.from_user.id, pid):
        await cb.answer("У тебя нет этого зелья!", show_alert=True)
        return
    
    await cb.answer()
    
    if pot["type"] == "hp":
        # Восстанавливаем HP (в бою это не работает, но можно добавить)
        await cb.answer(f"✅ {pot['name']} использовано! Восстановлено {pot['restore']} HP", show_alert=True)
    elif pot["type"] == "mp":
        await cb.answer(f"✅ {pot['name']} использовано! Восстановлено {pot['restore']} MP", show_alert=True)
    
    await cb_potions(cb)

# ======== ПРОФЕССИИ ========
@dp.callback_query(F.data == "profession")
async def cb_profession(cb: types.CallbackQuery):
    await cb.answer()
    p = await db.get_player(cb.from_user.id)
    if not p or not p["class"]: return
    
    if not p.get("profession"):
        # Выбор профессии
        text = "⚒️ <b>Выбери профессию</b>\n\n<i>Профессию можно выбрать только один раз!</i>\n\n"
        btns = []
        for pid, prof in PROFESSIONS.items():
            text += f"{prof['name']}\n<i>{prof['desc']}</i>\n{prof['bonus']}\n\n"
            btns.append([IKB(text=prof['name'], callback_data=f"prof_{pid}")])
        btns.append([IKB(text="🏠 Меню", callback_data="menu")])
        try: await cb.message.edit_text(text, reply_markup=IKM(inline_keyboard=btns))
        except: pass
    else:
        # Просмотр профессии
        prof = PROFESSIONS.get(p["profession"], {})
        prof_lvl = p.get("profession_level", 1)
        prof_xp = p.get("profession_xp", 0)
        xp_needed = prof_lvl * 100
        text = (
            f"⚒️ <b>Профессия: {prof.get('name', '???')}</b>\n\n"
            f"📊 Уровень: {prof_lvl}\n"
            f"✨ XP: {prof_xp}/{xp_needed} [{hp_bar(prof_xp, xp_needed)}]\n\n"
            f"💡 <b>Бонус:</b> {prof.get('bonus', '—')}\n\n"
            f"<i>Получай XP профессии выполняя действия!</i>"
        )
        try: await cb.message.edit_text(text, reply_markup=IKM(inline_keyboard=[[IKB(text="🏠 Меню",callback_data="menu")]]))
        except: pass

@dp.callback_query(F.data.startswith("prof_"))
async def cb_set_profession(cb: types.CallbackQuery):
    pid = cb.data[5:]
    if pid not in PROFESSIONS: await cb.answer("Ошибка!",show_alert=True); return
    p = await db.get_player(cb.from_user.id)
    if p and p.get("profession"): await cb.answer("Профессия уже выбрана!",show_alert=True); return
    await cb.answer()
    await db.set_profession(cb.from_user.id, pid)
    prof = PROFESSIONS[pid]
    await cb.message.edit_text(f"🎉 <b>Профессия выбрана!</b>\n\n{prof['name']}\n{prof['desc']}\n\n{prof['bonus']}", reply_markup=IKM(inline_keyboard=[[IKB(text="🏠 Меню",callback_data="menu")]]))

# ======== ПРОКАЧКА ОРУЖИЯ ========
@dp.callback_query(F.data == "upgrade_item")
async def cb_upgrade_item(cb: types.CallbackQuery):
    await cb.answer()
    uid = cb.from_user.id
    inv = await db.get_inventory(uid)
    equipped = [i for i in inv if i["is_equipped"]]
    
    if not equipped:
        try: await cb.message.edit_text("🔧 <b>Прокачка предметов</b>\n\nНадень предмет чтобы прокачать его!", reply_markup=IKM(inline_keyboard=[[IKB(text="📦 Инвентарь",callback_data="inv")],[IKB(text="🏠 Меню",callback_data="menu")]]))
        except: pass
        return
    
    text = "🔧 <b>Прокачка предметов</b>\n\n<i>Выбери предмет для прокачки:</i>\n\n"
    btns = []
    for item in equipped:
        lvl = item.get("item_level", 1)
        if lvl >= MAX_ITEM_LEVEL:
            text += f"{format_item_short(item)} — <b>МАКС УРОВЕНЬ!</b>\n"
        else:
            p = await db.get_player(uid)
            prof_bonus = get_profession_bonus(p.get("profession", ""))
            cost = get_upgrade_cost(lvl, item["rarity"], prof_bonus.get("upgrade_discount", 0))
            text += f"{format_item_short(item)} Lv.{lvl} → Lv.{lvl+1} ({cost}💰)\n"
            btns.append([IKB(text=f"🔧 {item['name']} Lv.{lvl}→{lvl+1}", callback_data=f"upitm_{item['id']}")])
    
    btns.append([IKB(text="🏠 Меню", callback_data="menu")])
    try: await cb.message.edit_text(text, reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data.startswith("upitm_"))
async def cb_upgrade_item_do(cb: types.CallbackQuery):
    iid = int(cb.data[6:])
    item = await db.get_item(iid)
    if not item or item["user_id"] != cb.from_user.id or not item["is_equipped"]:
        await cb.answer("Ошибка! Предмет не надет.", show_alert=True)
        return
    
    lvl = item.get("item_level", 1)
    if lvl >= MAX_ITEM_LEVEL:
        await cb.answer("Уже максимальный уровень!", show_alert=True)
        return
    
    p = await db.get_player(cb.from_user.id)
    prof_bonus = get_profession_bonus(p.get("profession", ""))
    cost = get_upgrade_cost(lvl, item["rarity"], prof_bonus.get("upgrade_discount", 0))
    
    if not await db.spend_gold(cb.from_user.id, cost):
        await cb.answer(f"Не хватает золота! Нужно {cost}💰", show_alert=True)
        return
    
    await cb.answer()
    
    # Базовые статы
    base_stats = {
        "bonus_attack": item.get("base_attack", item.get("bonus_attack", 0)),
        "bonus_defense": item.get("base_defense", item.get("bonus_defense", 0)),
        "bonus_hp": item.get("base_hp", item.get("bonus_hp", 0)),
        "bonus_crit": item.get("base_crit", item.get("bonus_crit", 0)),
    }
    
    new_lvl = lvl + 1
    new_stats = get_upgrade_stats(new_lvl, base_stats)
    await db.upgrade_item(iid, new_lvl, new_stats)
    
    # XP профессии кузнецу
    if p.get("profession") == "blacksmith":
        leveled = await db.add_profession_xp(cb.from_user.id, 10)
        if leveled:
            await cb.answer(f"✅ Прокачано! +10 XP профессии! Уровень профессии повышен!", show_alert=True)
        else:
            await cb.answer(f"✅ Прокачано! +10 XP профессии!", show_alert=True)
    else:
        await cb.answer(f"✅ Прокачано до Lv.{new_lvl}!", show_alert=True)
    
    await cb_upgrade_item(cb)

# ======== ПРОФИЛЬ ========
@dp.callback_query(F.data == "prof")
async def cb_prof(cb: types.CallbackQuery):
    await cb.answer(); uid = cb.from_user.id
    p = await db.get_player(uid)
    if not p or not p["class"]: return
    cls = CLASSES[p["class"]]; race = RACES.get(p.get("race", ""), {})
    base = get_class_stats(p["class"], p["level"], p.get("race"))
    eq = await db.get_equipment_bonuses(uid); tot = get_total_stats(base, eq)
    xn = xp_for_level(p["level"])
    eqi = await db.get_equipped_items(uid); ic = await db.count_inventory(uid)
    el = ""
    for s in EQUIPMENT_SLOTS:
        i = next((x for x in eqi if x["item_type"]==s), None)
        lvl_text = f" Lv.{i['item_level']}" if i and i.get("item_level", 1) > 1 else ""
        el += f"  {format_item_short(i)}{lvl_text} — {format_item_stats(i)}\n" if i else f"  {TYPE_EMOJI.get(s,'📦')} <i>пусто</i>\n"
    prof_text = ""
    if p.get("profession"):
        prof = PROFESSIONS.get(p["profession"], {})
        prof_lvl = p.get("profession_level", 1)
        prof_text = f"\n⚒️ Профессия: {prof.get('name', '???')} Lv.{prof_lvl}"
    
    prem_text = ""
    is_prem = await db.is_premium_active(cb.from_user.id)
    if is_prem:
        prem_info = await db.get_premium_info(cb.from_user.id)
        if prem_info:
            try:
                expires = datetime.fromisoformat(prem_info["expires_at"])
                days_left = (expires - datetime.now()).days
                prem_text = f"\n👑 <b>ПРЕМИУМ</b> (осталось {days_left} дней)"
            except:
                prem_text = "\n👑 <b>ПРЕМИУМ</b>"
    
    race_text = f" {race.get('name', '')}" if race else ""
    t = (f"{race_text} {cls['name']} <b>{p['first_name']}</b>{prem_text}{prof_text}\n\n📊 <b>Lv.{p['level']}</b> XP:{p['xp']}/{xn} [{hp_bar(p['xp'],xn)}]\n\n"
         f"❤️HP:{tot['hp']}(+{eq['hp']}) ⚔️ATK:{tot['attack']}(+{eq['attack']})\n🛡DEF:{tot['defense']}(+{eq['defense']}) 💥КР:{tot['crit']:.0f}%\n\n"
         f"💰{p['gold']} 💎{p['crystals']}\n\n🔧 <b>Экипировка (9 слотов):</b>\n{el}\n"
         f"📦{ic} 🏅{p['arena_rating']} W/L:{p['arena_wins']}/{p['arena_losses']}\n🏰Башня:{p['tower_floor']} 🗺Охот:{p['total_hunts']} ☠️{p['total_kills']}\n📅Дней подряд:{p['daily_streak']}")
    
    # Показываем изображение персонажа если есть
    char_img = p.get("character_image_url")
    if char_img:
        try:
            await cb.message.answer_photo(char_img, caption=t, reply_markup=IKM(inline_keyboard=[[IKB(text="🏠 Меню",callback_data="menu")]]))
            await cb.message.delete()
        except:
            try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=[[IKB(text="🏠 Меню",callback_data="menu")]]))
            except: pass
    else:
        try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=[[IKB(text="🏠 Меню",callback_data="menu")]]))
        except: pass

# ======== ТОП ========
@dp.callback_query(F.data == "top")
async def cb_top(cb: types.CallbackQuery):
    await cb.answer(); leaders = await db.get_leaderboard_xp(10); rank = await db.get_player_rank(cb.from_user.id)
    medals = ["🥇","🥈","🥉"]; lines = []
    for i,p in enumerate(leaders):
        m = medals[i] if i<3 else f"#{i+1}"; ce = CLASSES.get(p["class"],{}).get("name","?").split()[0]; n = p["first_name"] or "???"
        lines.append(f"{m} {ce} <b>{n}</b> Lv.{p['level']} 🏅{p['arena_rating']} 🏰{p['tower_floor']}")
    t = "🏆 <b>Топ игроков</b>\n\n" + ("\n".join(lines) or "Пусто") + f"\n\n👤 Ты: #{rank}"
    try: await cb.message.edit_text(t, reply_markup=IKM(inline_keyboard=[[IKB(text="⚔️ Топ арены",callback_data="top_a")],[IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

@dp.callback_query(F.data == "top_a")
async def cb_top_a(cb: types.CallbackQuery):
    await cb.answer(); leaders = await db.get_leaderboard_arena(10)
    medals = ["🥇","🥈","🥉"]; lines = []
    for i,p in enumerate(leaders):
        m = medals[i] if i<3 else f"#{i+1}"; n = p["first_name"] or "???"; wr = round(p["arena_wins"]/max(1,p["arena_wins"]+p["arena_losses"])*100)
        lines.append(f"{m} <b>{n}</b> 🏅{p['arena_rating']} W/L:{p['arena_wins']}/{p['arena_losses']} ({wr}%)")
    try: await cb.message.edit_text("⚔️ <b>Топ арены</b>\n\n"+("\n".join(lines) or "Пусто"), reply_markup=IKM(inline_keyboard=[[IKB(text="🏆 По уровню",callback_data="top")],[IKB(text="🏠 Меню",callback_data="menu")]]))
    except: pass

# ======== МАГАЗИН ========
@dp.callback_query(F.data == "shop")
async def cb_shop(cb: types.CallbackQuery):
    await cb.answer()
    p = await db.get_player(cb.from_user.id)
    if not p: return
    
    potions_list = []
    for pid, pot in POTIONS.items():
        potions_list.append(f"{pot['emoji']} {pot['name']} — {pot['cost']}💰\n<i>{pot['description']}</i>")
    
    text = f"🏪 <b>Обычный магазин</b> (за золото)\n\n💰 Золото: {p['gold']}\n\n<b>Зелья:</b>\n" + "\n".join(potions_list)
    
    btns = []
    for pid, pot in POTIONS.items():
        btns.append([IKB(text=f"{pot['emoji']} {pot['name']} ({pot['cost']}💰)", callback_data=f"buy_pot_{pid}")])
    btns.append([IKB(text="🏠 Меню", callback_data="menu")])
    
    try: await cb.message.edit_text(text, reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data.startswith("buy_pot_"))
async def cb_buy_potion(cb: types.CallbackQuery):
    pid = cb.data[8:]
    if pid not in POTIONS: await cb.answer("Ошибка!", show_alert=True); return
    pot = POTIONS[pid]
    p = await db.get_player(cb.from_user.id)
    if not p: return
    if p["gold"] < pot["cost"]: await cb.answer(f"Не хватает золота! Нужно {pot['cost']}💰", show_alert=True); return
    await cb.answer()
    await db.spend_gold(cb.from_user.id, pot["cost"])
    await db.add_potion(cb.from_user.id, pid, 1)
    
    # Активируем эффект если это буст
    if pot["type"] in ("xp_boost", "gold_boost", "luck"):
        duration = pot.get("duration_minutes", 60)
        mult = pot.get("multiplier", 1.0)
        bonus = pot.get("drop_chance_bonus", 0)
        await db.add_effect(cb.from_user.id, pot["type"], mult, bonus, duration)
        await cb.answer(f"✅ {pot['name']} активировано на {duration} минут!", show_alert=True)
        else:
        await cb.answer(f"✅ {pot['name']} куплено!", show_alert=True)
    
    await cb_shop(cb)

@dp.callback_query(F.data == "premium_shop")
async def cb_premium_shop(cb: types.CallbackQuery):
    await cb.answer()
    p = await db.get_player(cb.from_user.id)
    if not p: return
    
    is_prem = await db.is_premium_active(cb.from_user.id)
    prem_info = await db.get_premium_info(cb.from_user.id)
    
    text = f"👑 <b>Премиум магазин</b>\n\n💎 Кристаллы: {p['crystals']}\n\n"
    
    if is_prem and prem_info:
        try:
            expires = datetime.fromisoformat(prem_info["expires_at"])
            days_left = (expires - datetime.now()).days
            text += f"✅ <b>Премиум активен!</b>\n⏰ Осталось: {days_left} дней\n\n"
        except: pass
    
    text += "<b>Премиум подписка:</b>\n"
    text += "👑 3 дня — 50💎\n"
    text += "👑 7 дней — 100💎\n"
    text += "👑 14 дней — 180💎\n"
    text += "👑 30 дней — 350💎\n\n"
    text += "<b>Бонусы премиума:</b>\n"
    text += f"✨ +{int((PREMIUM_BONUSES['xp_multiplier']-1)*100)}% XP\n"
    text += f"💰 +{int((PREMIUM_BONUSES['gold_multiplier']-1)*100)}% золота\n"
    text += f"🎁 +{PREMIUM_BONUSES['drop_chance_bonus']}% к шансу дропа\n"
    text += f"💎 +{PREMIUM_BONUSES['crystals_per_day']} кристаллов в день\n\n"
    text += "<b>Купить кристаллы:</b>\n"
    text += "💎 50 — 25⭐\n"
    text += "💎 150 — 65⭐\n"
    text += "💎 500 — 200⭐\n"
    
    btns = [
        [IKB(text="👑 Премиум 3 дня (50💎)", callback_data="buy_prem_3")],
        [IKB(text="👑 Премиум 7 дней (100💎)", callback_data="buy_prem_7")],
        [IKB(text="👑 Премиум 14 дней (180💎)", callback_data="buy_prem_14")],
        [IKB(text="👑 Премиум 30 дней (350💎)", callback_data="buy_prem_30")],
        [IKB(text="💎 50 кристаллов (25⭐)", callback_data="buy_c50")],
        [IKB(text="💎 150 кристаллов (65⭐)", callback_data="buy_c150")],
        [IKB(text="💎 500 кристаллов (200⭐)", callback_data="buy_c500")],
        [IKB(text="🏠 Меню", callback_data="menu")],
    ]
    
    try: await cb.message.edit_text(text, reply_markup=IKM(inline_keyboard=btns))
    except: pass

@dp.callback_query(F.data.startswith("buy_prem_"))
async def cb_buy_premium(cb: types.CallbackQuery):
    days = int(cb.data[9:])
    costs = {3: 50, 7: 100, 14: 180, 30: 350}
    cost = costs.get(days)
    if not cost: await cb.answer("Ошибка!", show_alert=True); return
    p = await db.get_player(cb.from_user.id)
    if not p: return
    if p["crystals"] < cost: await cb.answer(f"Не хватает кристаллов! Нужно {cost}💎", show_alert=True); return
    await cb.answer()
    await db.spend_crystals(cb.from_user.id, cost)
    await db.activate_premium(cb.from_user.id, days)
    await cb.answer(f"🎉 Премиум активирован на {days} дней!", show_alert=True)
    await cb_premium_shop(cb)

@dp.callback_query(F.data.startswith("buy_"))
async def cb_buy(cb: types.CallbackQuery):
    pm = {"c50":"crystals_50","c150":"crystals_150","c500":"crystals_500","eng":"energy_full"}
    pk = pm.get(cb.data[4:])
    if not pk or pk not in config.STARS_SHOP: await cb.answer("Ошибка!",show_alert=True); return
    pr = config.STARS_SHOP[pk]; await cb.answer()
    await bot.send_invoice(cb.from_user.id, title=pr["label"], description="Покупка в RPG", payload=f"{pk}_{cb.from_user.id}", currency="XTR", prices=[LabeledPrice(label=pr["label"],amount=pr["stars"])])

@dp.pre_checkout_query()
async def pre_checkout(pcq: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pcq.id, ok=True)

@dp.message(F.successful_payment)
async def succ_pay(msg: types.Message):
    pl = msg.successful_payment.invoice_payload; uid = msg.from_user.id
    if "crystals" in pl:
        ak = "_".join(pl.split("_")[:2]); pr = config.STARS_SHOP.get(ak)
        if pr: await db.add_crystals(uid, pr["crystals"]); await msg.answer(f"🎉 +{pr['crystals']}💎!", reply_markup=kb_main())
    elif "energy" in pl:
        # Энергия больше не используется, даём кристаллы
        await db.add_crystals(uid, 20); await msg.answer(f"🎉 +20💎!", reply_markup=kb_main())

# ======== ПРОЧЕЕ ========
@dp.callback_query(F.data == "noop")
async def cb_noop(cb: types.CallbackQuery): await cb.answer()

@dp.message(Command("help"))
async def cmd_help(msg: types.Message):
    await msg.answer("📋 <b>Команды:</b>\n/start — Меню\n/profile — Профиль\n/top — Топ\n/help — Справка\n\n<b>Что делать:</b>\n🗺 Охота — бей монстров (8 зон, боссы)\n⚔️ Арена — PvP 5 боёв/день\n🏰 Башня — 100 этажей, 3 попытки/день\n🌍 Экспедиция — AFK поход за лутом\n📜 Квесты — 3 задания/день\n🎡 Колесо — бесплатный спин/день\n🎰 Призыв — гача экипировки\n⛏️ Улучшение — 3 предмета → 1 лучше\n🎪 Аукцион — торговля с игроками\n🏪 Магазин — кристаллы за Stars", reply_markup=kb_main())

@dp.message(Command("profile"))
async def cmd_prof(msg: types.Message): 
    p = await db.get_player(msg.from_user.id)
    if not p or not p["class"]: await msg.answer("Нажми /start!"); return
    # Redirect to callback handler
    await msg.answer("👤 Используй кнопку Профиль в меню!", reply_markup=kb_main())

@dp.message(Command("top"))
async def cmd_top(msg: types.Message):
    leaders = await db.get_leaderboard_xp(10)
    lines = []
    for i,p in enumerate(leaders):
        m = ["🥇","🥈","🥉"][i] if i<3 else f"#{i+1}"
        lines.append(f"{m} <b>{p['first_name'] or '???'}</b> Lv.{p['level']} 🏅{p['arena_rating']}")
    await msg.answer("🏆 <b>Топ</b>\n\n"+("\n".join(lines) or "Пусто"), reply_markup=kb_main())

@dp.message(Command("stats"))
async def cmd_stats(msg: types.Message):
    if msg.from_user.id != config.ADMIN_ID: return
    s = await db.get_bot_stats()
    await msg.answer(f"📊 Игроков:{s['total_players']} Охот:{s['total_hunts']} Арен:{s['total_arena_fights']}")

@dp.message(F.text)
async def handle_txt(msg: types.Message):
    text = msg.text.strip()
    p = await db.get_player(msg.from_user.id)
    
    # Секретный код
    if text.upper() == "PREMAK+":
        if not p or not p.get("class"): 
            await msg.answer("Сначала создай персонажа! /start")
            return
        await db.activate_premium(msg.from_user.id, 7)
        await msg.answer("🎉 <b>Секретный код активирован!</b>\n\n👑 Премиум на 7 дней активирован!\n\n✨ +50% XP\n💰 +50% золота\n🎁 +15% к дропу\n💎 +10 кристаллов в день", reply_markup=kb_main())
        return
    
    if not p or not p.get("class"): 
        await msg.answer("👋 /start чтобы начать!")
    else: 
        await msg.answer("⚔️ Используй кнопки!", reply_markup=kb_main())

# ======== ЗАПУСК ========
async def main():
    logger.info("🗄 Init DB..."); await db.init_db()
    logger.info("⚔️ Starting RPG bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
