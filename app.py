from flask import Flask, request, jsonify, render_template
from supabase import create_client, Client
import os
import json
import hmac
import hashlib
from urllib.parse import parse_qs
from datetime import datetime
import time

app = Flask(__name__)

# ========== НАСТРОЙКИ ==========
SUPABASE_URL = "https://xevwktdwyioyantuqntb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhldndrdGR3eWlveWFudHVxbnRiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE4ODI2NTAsImV4cCI6MjA4NzQ1ODY1MH0.jC8jqGBv_yrbYg_x4XQradxxbkDtsXsQ9EBT0Iabed4"

# Токен твоего бота
BOT_TOKEN = "8596066162:AAEm2DSAFhKemedKC8rT4RfFY4fjUhVBCvI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# ================================

# Доход ратуши по уровням (уровень игрока = уровень ратуши)
TOWN_HALL_INCOME = {
    1: 5,
    2: 10,
    3: 25,
    4: 50,
    5: 100
}

# Стоимость улучшения уровня игрока (ратуши)
TOWN_HALL_UPGRADE_COST = {
    2: {"gold": 50, "wood": 20, "stone": 0},
    3: {"gold": 300, "wood": 100, "stone": 30},
    4: {"gold": 1000, "wood": 250, "stone": 100},
    5: {"gold": 5000, "wood": 1000, "stone": 400}
}

# Конфиг зданий
BUILDINGS_CONFIG = {
    "house": {
        "name": "Жилой район",
        "icon": "🏘️",
        "section": "social",
        "max_level": 5,
        "base_cost": {"gold": 50, "wood": 20, "stone": 0},
        "income": [
            {"gold": 0, "wood": 0, "food": 0, "stone": 0},  # 1 ур
            {"gold": 0, "wood": 0, "food": 0, "stone": 0},  # 2 ур
            {"gold": 0, "wood": 0, "food": 0, "stone": 0},  # 3 ур
            {"gold": 0, "wood": 0, "food": 0, "stone": 0},  # 4 ур
            {"gold": 0, "wood": 0, "food": 0, "stone": 0}   # 5 ур
        ]
    },
    "farm": {
        "name": "Ферма",
        "icon": "🌾",
        "section": "economic",
        "max_level": 5,
        "base_cost": {"gold": 30, "wood": 40, "stone": 0},
        "income": [
            {"food": 10},  # 1 ур
            {"food": 20},  # 2 ур
            {"food": 35},  # 3 ур
            {"food": 55},  # 4 ур
            {"food": 80}   # 5 ур
        ]
    },
    "lumber": {
        "name": "Лесопилка",
        "icon": "🪵",
        "section": "economic",
        "max_level": 5,
        "base_cost": {"gold": 40, "wood": 30, "stone": 0},
        "income": [
            {"wood": 10},  # 1 ур
            {"wood": 20},  # 2 ур
            {"wood": 35},  # 3 ур
            {"wood": 55},  # 4 ур
            {"wood": 80}   # 5 ур
        ]
    },
    "quarry": {
        "name": "Каменоломня",
        "icon": "⛰️",
        "section": "economic",
        "max_level": 5,
        "base_cost": {"gold": 60, "wood": 40, "stone": 0},
        "income": [
            {"stone": 3},   # 1 ур
            {"stone": 7},   # 2 ур
            {"stone": 12},  # 3 ур
            {"stone": 18},  # 4 ур
            {"stone": 25}   # 5 ур
        ]
    }
}

def verify_telegram_data(init_data: str):
    """Проверяет подпись Telegram Init Data"""
    try:
        parsed_data = parse_qs(init_data)
        
        if 'hash' not in parsed_data:
            print("❌ Нет hash в данных")
            return None
        
        data_check_pairs = []
        for key in sorted(parsed_data.keys()):
            if key != 'hash':
                data_check_pairs.append(f"{key}={parsed_data[key][0]}")
        
        data_check_string = "\n".join(data_check_pairs)
        received_hash = parsed_data['hash'][0]
        
        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if expected_hash != received_hash:
            print("❌ Неверная подпись данных")
            return None
        
        if 'user' in parsed_data:
            user_data = json.loads(parsed_data['user'][0])
            print(f"✅ Данные проверены, пользователь: {user_data.get('id')}")
            return user_data
        
        return None
        
    except Exception as e:
        print(f"❌ Ошибка при проверке данных: {e}")
        return None

def calculate_building_cost(building_id, level):
    """Рассчитывает стоимость улучшения здания"""
    config = BUILDINGS_CONFIG.get(building_id)
    if not config:
        return {"gold": 0, "wood": 0, "stone": 0}
    
    multiplier = level + 1
    return {
        "gold": config["base_cost"]["gold"] * multiplier,
        "wood": config["base_cost"]["wood"] * multiplier,
        "stone": config["base_cost"]["stone"] * multiplier
    }

def calculate_hourly_income(buildings, town_hall_level):
    """Рассчитывает общий доход в час"""
    income = {
        "gold": TOWN_HALL_INCOME.get(town_hall_level, 0),
        "wood": 0,
        "food": 0,
        "stone": 0
    }
    
    for b in buildings:
        building_id = b["id"]
        level = b["level"]
        count = b.get("count", 1)
        
        config = BUILDINGS_CONFIG.get(building_id)
        if not config or level == 0:
            continue
            
        level_income = config["income"][level - 1]
        for resource, value in level_income.items():
            if resource in income:
                income[resource] += value * count
    
    return income

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth', methods=['POST'])
def auth():
    """Авторизация пользователя"""
    data = request.json
    init_data = data.get('initData', '')
    
    if not init_data:
        return jsonify({'success': False, 'error': 'No initData'}), 400
    
    telegram_user = verify_telegram_data(init_data)
    if not telegram_user:
        return jsonify({'success': False, 'error': 'Invalid Telegram data'}), 401
    
    telegram_id = str(telegram_user['id'])
    username = telegram_user.get('username', '')
    
    try:
        # Ищем пользователя
        result = supabase.table("players") \
            .select("*") \
            .eq("telegram_id", telegram_id) \
            .execute()
        
        now = int(time.time() * 1000)
        
        if result.data and len(result.data) > 0:
            # Пользователь НАЙДЕН - загружаем его данные
            player = result.data[0]
            
            # Загружаем постройки
            buildings = []
            if player.get('buildings'):
                try:
                    buildings = json.loads(player.get('buildings'))
                    if not isinstance(buildings, list):
                        buildings = []
                except:
                    buildings = []
            
            # Обновляем время последнего входа
            supabase.table("players") \
                .update({'last_collection': now}) \
                .eq('id', player['id']) \
                .execute()
            
            # ВАЖНО: проверяем, есть ли у игрока game_login
            game_login = player.get('game_login', '')
            
            return jsonify({
                'success': True,
                'user': {
                    'id': player.get('telegram_id'),
                    'username': player.get('username', ''),
                    'game_login': game_login,  # Отправляем сохраненное имя
                    'gold': player.get('gold', 100),
                    'wood': player.get('wood', 50),
                    'food': player.get('food', 50),
                    'stone': player.get('stone', 0),
                    'level': player.get('level', 1),
                    'lastCollection': now
                },
                'buildings': buildings,
                'config': BUILDINGS_CONFIG
            })
        else:
            # Создаем НОВОГО игрока
            initial_buildings = [
                {"id": "house", "count": 1, "level": 1},
                {"id": "farm", "count": 1, "level": 1},
                {"id": "lumber", "count": 1, "level": 1}
            ]
            
            new_player = {
                'telegram_id': telegram_id,
                'username': username,
                'game_login': '',  # Пустое имя для нового игрока
                'gold': 100,
                'wood': 50,
                'food': 50,
                'stone': 0,
                'level': 1,
                'buildings': json.dumps(initial_buildings),
                'last_collection': now
            }
            
            supabase.table("players").insert(new_player).execute()
            
            return jsonify({
                'success': True,
                'user': {
                    'id': telegram_id,
                    'username': username,
                    'game_login': '',  # Пустое имя = показать окно
                    'gold': 100,
                    'wood': 50,
                    'food': 50,
                    'stone': 0,
                    'level': 1,
                    'lastCollection': now
                },
                'buildings': initial_buildings,
                'config': BUILDINGS_CONFIG
            })
            
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
@app.route('/api/action', methods=['POST'])
def game_action():
    """Выполнение игрового действия"""
    data = request.json
    init_data = data.get('initData', '')
    action_type = data.get('action')
    action_data = data.get('data', {})
    
    telegram_user = verify_telegram_data(init_data)
    if not telegram_user:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    telegram_id = str(telegram_user['id'])
    
    try:
        # Получаем игрока
        result = supabase.table("players") \
            .select("*") \
            .eq("telegram_id", telegram_id) \
            .execute()
        
        if not result.data:
            return jsonify({'success': False, 'error': 'Player not found'}), 404
        
        player = result.data[0]
        player_id = player['id']
        
        # Текущие данные
        gold = player['gold']
        wood = player['wood']
        food = player.get('food', 50)
        stone = player.get('stone', 0)
        level = player['level']  # уровень игрока = уровень ратуши
        game_login = player.get('game_login', '')
        
        # Загружаем постройки
        buildings = []
        if player.get('buildings'):
            try:
                buildings = json.loads(player.get('buildings'))
                if not isinstance(buildings, list):
                    buildings = []
            except:
                buildings = []
        
        # Получаем время последнего сбора
        last_collection = player.get('last_collection')
        if last_collection is None:
            last_collection = int(time.time() * 1000)
        
        response_data = {'success': True}
        
        # Обработка действий
        if action_type == 'collect':
            # Сбор ресурсов
            now = int(time.time() * 1000)
            time_passed = now - last_collection
            hours_passed = time_passed / (60 * 60 * 1000)
            
            if hours_passed > 0:
                income = calculate_hourly_income(buildings, level)
                
                gold += int(income["gold"] * hours_passed)
                wood += int(income["wood"] * hours_passed)
                food += int(income["food"] * hours_passed)
                stone += int(income["stone"] * hours_passed)
                
                last_collection = now
                
                # Сохраняем
                supabase.table("players") \
                    .update({
                        'gold': gold,
                        'wood': wood,
                        'food': food,
                        'stone': stone,
                        'last_collection': last_collection
                    }) \
                    .eq('id', player_id) \
                    .execute()
            
            response_data['state'] = {
                'gold': gold,
                'wood': wood,
                'food': food,
                'stone': stone,
                'level': level,
                'game_login': game_login,
                'buildings': buildings,
                'lastCollection': last_collection
            }
            
        elif action_type == 'build':
            # Постройка нового здания
            building_id = action_data.get('building_id')
            
            if building_id not in BUILDINGS_CONFIG:
                return jsonify({'success': False, 'error': 'Unknown building'})
            
            # Проверяем, есть ли уже такое здание
            existing = None
            for b in buildings:
                if b['id'] == building_id:
                    existing = b
                    break
            
            if existing:
                return jsonify({'success': False, 'error': 'Building already exists'})
            
            # Проверяем ресурсы
            cost = BUILDINGS_CONFIG[building_id]["base_cost"]
            if gold < cost['gold'] or wood < cost['wood']:
                return jsonify({'success': False, 'error': 'Not enough resources'})
            
            # Списываем ресурсы
            gold -= cost['gold']
            wood -= cost['wood']
            
            # Добавляем здание 1 уровня
            buildings.append({
                "id": building_id,
                "count": 1,
                "level": 1
            })
            
            # Сохраняем
            supabase.table("players") \
                .update({
                    'gold': gold,
                    'wood': wood,
                    'buildings': json.dumps(buildings)
                }) \
                .eq('id', player_id) \
                .execute()
            
            print(f"✅ Построено {building_id}")
            
            response_data['state'] = {
                'gold': gold,
                'wood': wood,
                'food': food,
                'stone': stone,
                'level': level,
                'game_login': game_login,
                'buildings': buildings,
                'lastCollection': last_collection
            }
            
        elif action_type == 'upgrade':
            # Улучшение здания
            building_id = action_data.get('building_id')
            
            # Находим здание
            building = None
            for b in buildings:
                if b['id'] == building_id:
                    building = b
                    break
            
            if not building:
                return jsonify({'success': False, 'error': 'Building not found'})
            
            current_level = building['level']
            
            if current_level >= BUILDINGS_CONFIG[building_id]["max_level"]:
                return jsonify({'success': False, 'error': 'Max level reached'})
            
            # Проверяем уровень игрока (ратуши) для следующего уровня здания
            if level < current_level + 1:
                return jsonify({'success': False, 'error': f'Требуется уровень {current_level + 1}'})
            
            # Рассчитываем стоимость
            cost = calculate_building_cost(building_id, current_level)
            
            if gold < cost['gold'] or wood < cost['wood'] or stone < cost['stone']:
                return jsonify({'success': False, 'error': 'Not enough resources'})
            
            # Списываем ресурсы
            gold -= cost['gold']
            wood -= cost['wood']
            stone -= cost['stone']
            
            # Увеличиваем уровень
            building['level'] = current_level + 1
            
            # Сохраняем
            supabase.table("players") \
                .update({
                    'gold': gold,
                    'wood': wood,
                    'stone': stone,
                    'buildings': json.dumps(buildings)
                }) \
                .eq('id', player_id) \
                .execute()
            
            print(f"✅ Улучшено {building_id} до уровня {current_level + 1}")
            
            response_data['state'] = {
                'gold': gold,
                'wood': wood,
                'food': food,
                'stone': stone,
                'level': level,
                'game_login': game_login,
                'buildings': buildings,
                'lastCollection': last_collection
            }
            
        elif action_type == 'upgrade_level':
            # Улучшение уровня игрока (ратуши)
            if level >= 5:
                return jsonify({'success': False, 'error': 'Максимальный уровень'})
            
            cost = TOWN_HALL_UPGRADE_COST.get(level + 1, {})
            
            if gold < cost.get('gold', 0) or wood < cost.get('wood', 0) or stone < cost.get('stone', 0):
                return jsonify({'success': False, 'error': 'Not enough resources'})
            
            gold -= cost.get('gold', 0)
            wood -= cost.get('wood', 0)
            stone -= cost.get('stone', 0)
            level += 1
            
            supabase.table("players") \
                .update({
                    'gold': gold,
                    'wood': wood,
                    'stone': stone,
                    'level': level
                }) \
                .eq('id', player_id) \
                .execute()
            
            print(f"✅ Уровень повышен до {level}")
            
            response_data['state'] = {
                'gold': gold,
                'wood': wood,
                'food': food,
                'stone': stone,
                'level': level,
                'game_login': game_login,
                'buildings': buildings,
                'lastCollection': last_collection
            }
            
        elif action_type == 'set_login':
            # Установка имени
            new_login = action_data.get('game_login', '').strip()
            
            if not new_login:
                return jsonify({'success': False, 'error': 'Login cannot be empty'})
            
            supabase.table("players") \
                .update({'game_login': new_login}) \
                .eq('id', player_id) \
                .execute()
            
            print(f"✅ Имя изменено на: {new_login}")
            
            response_data['state'] = {
                'game_login': new_login,
                'gold': gold,
                'wood': wood,
                'food': food,
                'stone': stone,
                'level': level,
                'buildings': buildings,
                'lastCollection': last_collection
            }
        
        else:
            return jsonify({'success': False, 'error': 'Unknown action'})
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Ошибка действия: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clan/create', methods=['POST'])
def create_clan():
    return jsonify({'success': True})

@app.route('/api/clans/top', methods=['GET'])
def top_clans():
    try:
        result = supabase.table("players") \
            .select("*") \
            .order('gold', desc=True) \
            .limit(10) \
            .execute()
        return jsonify({'players': result.data})
    except:
        return jsonify({'players': []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


