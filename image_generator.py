"""
🎨 Генератор пиксельных изображений для игры
Поддержка разных API: Replicate, Stability AI, DALL-E
"""
import os
import aiohttp
import logging
from typing import Optional
from config_rpg import IMAGE_API_TYPE, IMAGE_API_KEY, IMAGE_API_URL, GENERATE_IMAGES

logger = logging.getLogger(__name__)

# Промпты для пиксельного стиля
PIXEL_STYLE = ", pixel art, 8-bit style, retro game graphics, sprite, low resolution, game asset"

async def generate_item_image(item_name: str, item_type: str, rarity: str) -> Optional[str]:
    """
    Генерирует пиксельное изображение для предмета
    Возвращает URL изображения или None
    """
    prompt = f"{item_name}, {item_type}, {rarity} rarity, fantasy game item{PIXEL_STYLE}"
    return await generate_image(prompt, f"item_{item_name}_{rarity}")

async def generate_character_image(class_name: str, race_name: str) -> Optional[str]:
    """
    Генерирует пиксельное изображение персонажа
    """
    prompt = f"{race_name} {class_name}, fantasy RPG character, portrait{PIXEL_STYLE}"
    return await generate_image(prompt, f"char_{class_name}_{race_name}")

async def generate_monster_image(monster_name: str, emoji: str = "") -> Optional[str]:
    """
    Генерирует пиксельное изображение монстра
    """
    prompt = f"{monster_name} monster, fantasy creature{PIXEL_STYLE}"
    return await generate_image(prompt, f"monster_{monster_name}")

async def generate_image(prompt: str, seed: str = "") -> Optional[str]:
    """
    Универсальная функция генерации изображения
    Поддерживает разные API
    """
    if not IMAGE_API_KEY:
        logger.warning("IMAGE_API_KEY не установлен, пропускаем генерацию")
        return None
    
    try:
        if IMAGE_API_TYPE == "replicate":
            return await _generate_replicate(prompt)
        elif IMAGE_API_TYPE == "stability":
            return await _generate_stability(prompt)
        elif IMAGE_API_TYPE == "dalle":
            return await _generate_dalle(prompt)
        elif IMAGE_API_TYPE == "local":
            return await _generate_local(prompt)
        else:
            logger.warning(f"Неизвестный тип API: {IMAGE_API_TYPE}")
            return None
    except Exception as e:
        logger.error(f"Ошибка генерации изображения: {e}")
        return None

async def _generate_replicate(prompt: str) -> Optional[str]:
    """Генерация через Replicate API (Stable Diffusion)"""
    try:
        import replicate
        output = replicate.run(
            "stability-ai/stable-diffusion:db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf",
            input={
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, realistic, photograph",
                "width": 512,
                "height": 512,
                "num_outputs": 1,
            }
        )
        if output and len(output) > 0:
            return output[0]
    except ImportError:
        logger.error("replicate не установлен. Установите: pip install replicate")
    except Exception as e:
        logger.error(f"Ошибка Replicate API: {e}")
    return None

async def _generate_stability(prompt: str) -> Optional[str]:
    """Генерация через Stability AI API"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {IMAGE_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "width": 512,
                "height": 512,
                "style_preset": "digital-art"
            }
            async with session.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers=headers,
                json=data
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("artifacts") and len(result["artifacts"]) > 0:
                        # Сохраняем в base64 или возвращаем URL
                        import base64
                        image_data = result["artifacts"][0]["base64"]
                        # Можно загрузить на хостинг или вернуть base64
                        return f"data:image/png;base64,{image_data}"
    except Exception as e:
        logger.error(f"Ошибка Stability AI: {e}")
    return None

async def _generate_dalle(prompt: str) -> Optional[str]:
    """Генерация через DALL-E API"""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=IMAGE_API_KEY)
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        if response.data and len(response.data) > 0:
            return response.data[0].url
    except ImportError:
        logger.error("openai не установлен. Установите: pip install openai")
    except Exception as e:
        logger.error(f"Ошибка DALL-E API: {e}")
    return None

async def _generate_local(prompt: str) -> Optional[str]:
    """Генерация через локальный сервер (например, локальный Stable Diffusion)"""
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, realistic",
                "width": 512,
                "height": 512,
                "steps": 20,
            }
            async with session.post(
                f"{IMAGE_API_URL}/api/v1/generate",
                json=data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("image_url") or result.get("url")
    except Exception as e:
        logger.error(f"Ошибка локального API: {e}")
    return None

async def upload_image_to_telegram(bot, image_url: str) -> Optional[str]:
    """
    Загружает изображение в Telegram и возвращает file_id
    Можно использовать для кеширования
    """
    try:
        # Если это base64, нужно декодировать
        if image_url.startswith("data:image"):
            # Пропускаем, используем URL напрямую
            return image_url
        
        # Если это URL, можно загрузить как файл
        # Но проще использовать URL напрямую
        return image_url
    except Exception as e:
        logger.error(f"Ошибка загрузки в Telegram: {e}")
        return None

def get_item_image_prompt(item: dict) -> str:
    """Генерирует промпт для предмета"""
    item_type_names = {
        "weapon": "sword or weapon",
        "armor": "armor or chestplate",
        "helmet": "helmet",
        "gloves": "gloves",
        "boots": "boots",
        "ring": "ring",
        "amulet": "amulet",
        "cloak": "cloak",
        "accessory": "accessory item"
    }
    type_name = item_type_names.get(item.get("item_type", "item"), "item")
    rarity_names = {
        "common": "simple",
        "uncommon": "uncommon",
        "rare": "rare",
        "epic": "epic",
        "legendary": "legendary"
    }
    rarity_desc = rarity_names.get(item.get("rarity", "common"), "simple")
    return f"{item.get('name', 'item')}, {type_name}, {rarity_desc} quality{PIXEL_STYLE}"
