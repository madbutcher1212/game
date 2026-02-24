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

# Доход ратуши по уровням
TOWN_HALL_INCOME = {
    1: 5, 2: 10, 3: 25, 4: 50, 5: 100
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
        "upgrade_costs": [
            {"gold": 80, "wood": 40, "stone": 0},    # 1->2
            {"gold": 200, "wood": 100, "stone": 0},  # 2->3
            {"gold": 550, "wood": 240, "stone": 0},  # 3->4
            {"gold": 1500, "wood": 520, "stone": 0}  # 4->5
        ],
        "population_bonus": [20, 20, 40, 100, 250]  # Бонус за каждый уровень
    },
    "farm": {
        "name": "Ферма",
        "icon": "🌾",
        "section": "economic",
        "max_level": 5,
        "base_cost": {"gold": 30, "wood": 40, "stone": 0},
        "upgrade_costs": [
            {"gold": 60, "wood": 80, "stone": 0},    # 1->2
            {"gold": 120, "wood": 160, "stone": 0},  # 2->3
            {"gold": 240, "wood": 320, "stone": 0},  # 3->4
            {"gold": 480, "wood": 640, "stone": 0}   # 4->5
        ],
        "income": [
            {"food": 10},
            {"food": 20},
            {"food": 35},
            {"food": 55},
            {"food": 80}
        ]
    },
    "lumber": {
        "name": "Лесопилка",
        "icon": "🪵",
        "section": "economic",
        "max_level": 5,
        "base_cost": {"gold": 40, "wood": 30, "stone": 0},
        "upgrade_costs": [
            {"gold": 80, "wood": 60, "stone": 0},    # 1->2
            {"gold": 160, "wood": 120, "stone": 0},  # 2->3
            {"gold": 320, "wood": 240, "stone": 0},  # 3->4
            {"gold": 640, "wood": 480, "stone": 0}   # 4->5
        ],
        "income": [
            {"wood": 10},
            {"wood": 20},
            {"wood": 35},
            {"wood": 55},
            {"wood": 80}
        ]
    },
    "quarry": {
        "name": "Каменоломня",
        "icon": "⛰️",
        "section": "economic",
        "max_level": 5,
        "base_cost": {"gold": 60, "wood": 40, "stone": 0},
        "upgrade_costs": [
            {"gold": 120, "wood": 80, "stone": 20},    # 1->2
            {"gold": 240, "wood": 160, "stone": 50},   # 2->3
            {"gold": 480, "wood": 320, "stone": 120},  # 3->4
            {"gold": 960, "wood": 640, "stone": 250}   # 4->5
        ],
        "income": [
            {"stone": 3},
            {"stone": 7},
            {"stone": 12},
            {"stone": 18},
            {"stone": 25}
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

def calculate_building_upgrade_cost(building_id, current_level):
    """Рассчитывает стоимость улучшения здания"""
    config = BUILDINGS_CONFIG.get(building_id)
    if not config or current_level >= config["max_level"]:
        return {"gold": 0, "wood": 0, "stone": 0}
    
    # Используем upgrade_costs если есть, иначе рассчитываем по base_cost
    if "upgrade_costs" in config:
        return config["upgrade_costs"][current_level - 1]
    else:
        multiplier = current_level + 1
        return {
            "gold": config["base_cost"]["gold"] * multiplier,
            "wood": config["base_cost"]["wood"] * multiplier,
            "stone": config["base_cost"]["stone"] * multiplier
        }

def calculate_population_max(buildings):
    """Рассчитывает максимальное население"""
    max_pop = 10  # База
    
    for b in buildings:
        if b["id"] == "house":
            house_level = b["level"]
            config = BUILDINGS_CONFIG["house"]
            # Суммируем бонусы за все уровни
            for i in range(house_level):
                max_pop += config["population_bonus"][i]
            break
    
    return max_pop

def calculate_hourly_income_and_growth(buildings, town_hall_level, current_population, max_population):
    """Рассчитывает доход и рост населения"""
    # Базовый доход от ратуши
    income = {
        "gold": TOWN_HALL_INCOME.get(town_hall_level, 0),
        "wood": 0,
        "food": 0,
        "stone": 0
    }
    
    # Доход от зданий
    for b in buildings:
        building_id = b["id"]
        level = b["level"]
        count = b.get("count", 1)
        
        config = BUILDINGS_CONFIG.get(building_id)
        if not config or level == 0 or not config.get("income"):
            continue
            
        level_income = config["income"][level - 1]
        for resource, value in level_income.items():
            if resource in income:
                income[resource] += value * count
    
    # Расчет роста населения
    food_production = income["food"]
    food_needed = current_population
    
    population_growth = 0
    if food_production >= food_needed:
        # Еды хватает
        food_left = food_production - food_needed
        income["food"] = food_left
        
        # Рост населения
        potential_growth = 3
        new_population = current_population + potential_growth
        if new_population <= max_population:
            population_growth = potential_growth
        else:
            population_growth = max_population - current_population
    else:
        # Еды не хватает - вся еда уходит на прокорм
        income["food"] = 0
        population_growth = 0
    
    return income, population_growth

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
        result = supabase.table("players") \
            .select("*") \
            .eq("telegram_id", telegram_id) \
            .execute()
        
        now = int(time.time() * 1000)
        
        if result.data and len(result.data) > 0:
            player = result.data[0]
            
            buildings = []
            if player.get('buildings'):
                try:
                    buildings = json.loads(player.get('buildings'))
                    if not isinstance(buildings, list):
                        buildings = []
                except:
                    buildings = []
            
            # Пересчитываем max_population на всякий случай
            max_population = calculate_population_max(buildings)
            
            supabase.table("players") \
                .update({
                    'last_collection': now,
                    'population_max': max_population
                }) \
                .eq('id', player['id']) \
                .execute()
            
            return jsonify({
                'success': True,
                'user': {
                    'id': player.get('telegram_id'),
                    'username': player.get('username', ''),
                    'game_login': player.get('game_login', ''),
                    'gold': player.get('gold', 100),
                    'wood': player.get('wood', 50),
                    'food': player.get('food', 50),
                    'stone': player.get('stone', 0),
                    'level': player.get('level', 1),
                    'population_current': player.get('population_current', 10),
                    'population_max': max_population,
                    'lastCollection': now
                },
                'buildings': buildings,
                'config': BUILDINGS_CONFIG
            })
        else:
            initial_buildings = [
                {"id": "house", "count": 1, "level": 1},
                {"id": "farm", "count": 1, "level": 1},
                {"id": "lumber", "count": 1, "level": 1}
            ]
            
            max_population = calculate_population_max(initial_buildings)
            
            new_player = {
                'telegram_id': telegram_id,
                'username': username,
                'game_login': '',
                'gold': 100,
                'wood': 50,
                'food': 50,
                'stone': 0,
                'level': 1,
                'population_current': 10,
                'population_max': max_population,
                'buildings': json.dumps(initial_buildings),
                'last_collection': now
            }
            
            supabase.table("players").insert(new_player).execute()
            
            return jsonify({
                'success': True,
                'user': {
                    'id': telegram_id,
                    'username': username,
                    'game_login': '',
                    'gold': 100,
                    'wood': 50,
                    'food': 50,
                    'stone': 0,
                    'level': 1,
                    'population_current': 10,
                    'population_max': max_population,
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
        food = player['food']
        stone = player['stone']
        level = player['level']
        population_current = player.get('population_current', 10)
        population_max = player.get('population_max', 20)
        game_login = player.get('game_login', '')
        
        buildings = []
        if player.get('buildings'):
            try:
                buildings = json.loads(player.get('buildings'))
                if not isinstance(buildings, list):
                    buildings = []
            except:
                buildings = []
        
        last_collection = player.get('last_collection', int(time.time() * 1000))
        
        response_data = {'success': True}
        
        if action_type == 'collect':
            # Сбор ресурсов и рост населения
            now = int(time.time() * 1000)
            time_passed = now - last_collection
            hours_passed = time_passed / (60 * 60 * 1000)
            
            if hours_passed > 0:
                # Считаем доход с учетом населения
                total_gold_gain = 0
                total_wood_gain = 0
                total_food_gain = 0
                total_stone_gain = 0
                total_population_gain = 0
                
                # Симулируем каждый час
                current_pop = population_current
                for _ in range(int(hours_passed)):
                    income, growth = calculate_hourly_income_and_growth(
                        buildings, level, current_pop, population_max
                    )
                    total_gold_gain += income["gold"]
                    total_wood_gain += income["wood"]
                    total_food_gain += income["food"]
                    total_stone_gain += income["stone"]
                    total_population_gain += growth
                    current_pop += growth
                
                gold += total_gold_gain
                wood += total_wood_gain
                food += total_food_gain
                stone += total_stone_gain
                population_current = min(current_pop, population_max)
                last_collection = now
                
                supabase.table("players") \
                    .update({
                        'gold': gold,
                        'wood': wood,
                        'food': food,
                        'stone': stone,
                        'population_current': population_current,
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
                'population_current': population_current,
                'population_max': population_max,
                'game_login': game_login,
                'buildings': buildings,
                'lastCollection': last_collection
            }
            
        elif action_type == 'build':
            building_id = action_data.get('building_id')
            
            if building_id not in BUILDINGS_CONFIG:
                return jsonify({'success': False, 'error': 'Unknown building'})
            
            # Проверяем, нет ли уже такого здания
            existing = None
            for b in buildings:
                if b['id'] == building_id:
                    existing = b
                    break
            
            if existing:
                return jsonify({'success': False, 'error': 'Building already exists'})
            
            cost = BUILDINGS_CONFIG[building_id]["base_cost"]
            if gold < cost['gold'] or wood < cost['wood']:
                return jsonify({'success': False, 'error': 'Not enough resources'})
            
            gold -= cost['gold']
            wood -= cost['wood']
            
            buildings.append({
                "id": building_id,
                "count": 1,
                "level": 1
            })
            
            # Пересчитываем макс население
            population_max = calculate_population_max(buildings)
            
            supabase.table("players") \
                .update({
                    'gold': gold,
                    'wood': wood,
                    'buildings': json.dumps(buildings),
                    'population_max': population_max
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
                'population_current': population_current,
                'population_max': population_max,
                'game_login': game_login,
                'buildings': buildings,
                'lastCollection': last_collection
            }
            
        elif action_type == 'upgrade':
            building_id = action_data.get('building_id')
            
            building = None
            for b in buildings:
                if b['id'] == building_id:
                    building = b
                    break
            
            if not building:
                return jsonify({'success': False, 'error': 'Building not found'})
            
            current_level = building['level']
            config = BUILDINGS_CONFIG[building_id]
            
            if current_level >= config["max_level"]:
                return jsonify({'success': False, 'error': 'Max level reached'})
            
            if level < current_level + 1:
                return jsonify({'success': False, 'error': f'Требуется уровень {current_level + 1}'})
            
            cost = calculate_building_upgrade_cost(building_id, current_level)
            
            if gold < cost['gold'] or wood < cost['wood'] or stone < cost['stone']:
                return jsonify({'success': False, 'error': 'Not enough resources'})
            
            gold -= cost['gold']
            wood -= cost['wood']
            stone -= cost['stone']
            
            building['level'] = current_level + 1
            
            # Пересчитываем макс население
            population_max = calculate_population_max(buildings)
            
            supabase.table("players") \
                .update({
                    'gold': gold,
                    'wood': wood,
                    'stone': stone,
                    'buildings': json.dumps(buildings),
                    'population_max': population_max
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
                'population_current': population_current,
                'population_max': population_max,
                'game_login': game_login,
                'buildings': buildings,
                'lastCollection': last_collection
            }
            
        elif action_type == 'upgrade_level':
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
                'population_current': population_current,
                'population_max': population_max,
                'game_login': game_login,
                'buildings': buildings,
                'lastCollection': last_collection
            }
            
        elif action_type == 'set_login':
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
                'population_current': population_current,
                'population_max': population_max,
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
