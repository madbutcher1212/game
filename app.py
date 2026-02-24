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
    1: 5,
    2: 10,
    3: 20,
    4: 45,
    5: 100
}

# Стоимость улучшения ратуши
TOWN_HALL_UPGRADE_COST = {
    2: {"gold": 50, "wood": 100, "stone": 0},
    3: {"gold": 500, "wood": 400, "stone": 0},
    4: {"gold": 2000, "wood": 1200, "stone": 250},
    5: {"gold": 10000, "wood": 6000, "stone": 2500}
}

# Конфиг зданий
BUILDINGS_CONFIG = {
    "house": {
        "name": "Жилой район",
        "icon": "🏘️",
        "section": "social",
        "max_level": 5,
        "base_cost": {"gold": 50, "wood": 20, "stone": 0},  # 1 уровень уже построен
        "upgrade_costs": [
            {"gold": 50, "wood": 100, "stone": 50},     # 1->2
            {"gold": 250, "wood": 300, "stone": 125},   # 2->3
            {"gold": 1500, "wood": 1000, "stone": 400}, # 3->4
            {"gold": 7200, "wood": 5300, "stone": 2450} # 4->5
        ],
        "population_bonus": [20, 20, 40, 100, 250]  # Бонус за каждый уровень
    },
    "farm": {
        "name": "Ферма",
        "icon": "🌾",
        "section": "economic",
        "max_level": 5,
        "base_cost": {"gold": 30, "wood": 40, "stone": 0},  # 1 уровень уже построен
        "upgrade_costs": [
            {"gold": 50, "wood": 100, "stone": 0},     # 1->2
            {"gold": 250, "wood": 300, "stone": 0},    # 2->3
            {"gold": 1000, "wood": 1000, "stone": 150},# 3->4
            {"gold": 5200, "wood": 6300, "stone": 2450}# 4->5
        ],
        "income": [
            {"food": 10},   # 1 ур
            {"food": 25},   # 2 ур
            {"food": 60},   # 3 ур
            {"food": 120},  # 4 ур
            {"food": 260}   # 5 ур
        ]
    },
    "lumber": {
        "name": "Лесопилка",
        "icon": "🪵",
        "section": "economic",
        "max_level": 5,
        "base_cost": {"gold": 40, "wood": 30, "stone": 0},  # 1 уровень уже построен
        "upgrade_costs": [
            {"gold": 50, "wood": 100, "stone": 0},     # 1->2
            {"gold": 350, "wood": 200, "stone": 50},   # 2->3
            {"gold": 1300, "wood": 900, "stone": 550}, # 3->4
            {"gold": 7000, "wood": 4500, "stone": 3500}# 4->5
        ],
        "income": [
            {"wood": 10},   # 1 ур
            {"wood": 20},   # 2 ур
            {"wood": 40},   # 3 ур
            {"wood": 100},  # 4 ур
            {"wood": 200}   # 5 ур
        ]
    },
    "quarry": {
        "name": "Каменоломня",
        "icon": "⛰️",
        "section": "economic",
        "max_level": 5,
        "base_cost": {"gold": 20, "wood": 80, "stone": 0},  # 1 уровень нужно строить
        "upgrade_costs": [
            {"gold": 50, "wood": 150, "stone": 0},     # 1->2
            {"gold": 250, "wood": 350, "stone": 100},  # 2->3
            {"gold": 1000, "wood": 1700, "stone": 150},# 3->4
            {"gold": 6200, "wood": 7300, "stone": 1450}# 4->5
        ],
        "income": [
            {"stone": 5},   # 1 ур
            {"stone": 15},  # 2 ур
            {"stone": 35},  # 3 ур
            {"stone": 80},  # 4 ур
            {"stone": 160}  # 5 ур
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
            for i in range(house_level):
                max_pop += config["population_bonus"][i]
            break
    
    return max_pop

def calculate_hourly_income_and_growth(buildings, town_hall_level, current_population, max_population, current_food):
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
        count = 1  # Всегда 1, здание одно
        
        config = BUILDINGS_CONFIG.get(building_id)
        if not config or level == 0 or not config.get("income"):
            continue
            
        level_income = config["income"][level - 1]
        for resource, value in level_income.items():
            if resource in income:
                income[resource] += value  # Умножение на count убрано
    
    # Расчет потребления еды
    food_production = income["food"]
    food_consumption = current_population  # Каждый житель ест 1 еды
    food_balance = food_production - food_consumption
    
    if food_balance >= 0:
        # Еды хватает или есть избыток
        income["food"] = food_balance  # Остаток еды
        population_growth = 3
        if current_population + population_growth <= max_population:
            population_growth_result = population_growth
        else:
            population_growth_result = max_population - current_population
    else:
        # Еды не хватает, смотрим запасы
        needed_food = abs(food_balance)  # Сколько еды не хватает
        
        if current_food >= needed_food:
            # Можем покрыть из запасов
            income["food"] = 0  # Вся произведенная еда ушла на прокорм
            # Запасы уменьшатся позже при обновлении
            population_growth_result = 3
            if current_population + population_growth_result <= max_population:
                population_growth_result = population_growth_result
            else:
                population_growth_result = max_population - current_population
        else:
            # Запасов не хватает
            income["food"] = 0
            population_growth_result = 0  # Рост останавливается
    
    return income, population_growth_result

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
            now = int(time.time() * 1000)
            time_passed = now - last_collection
            hours_passed = time_passed / (60 * 60 * 1000)
            
            if hours_passed > 0:
                total_gold_gain = 0
                total_wood_gain = 0
                total_food_gain = 0
                total_stone_gain = 0
                total_population_gain = 0
                
                current_pop = population_current
                current_food_stock = food
                
                for hour in range(int(hours_passed)):
                    income, growth = calculate_hourly_income_and_growth(
                        buildings, level, current_pop, population_max, current_food_stock
                    )
                    total_gold_gain += income["gold"]
                    total_wood_gain += income["wood"]
                    total_food_gain += income["food"]
                    total_stone_gain += income["stone"]
                    total_population_gain += growth
                    
                    current_pop += growth
                    current_food_stock += income["food"]  # Обновляем запасы еды
                
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

