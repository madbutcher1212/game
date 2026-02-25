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

BOT_TOKEN = "8596066162:AAEm2DSAFhKemedKC8rT4RfFY4fjUhVBCvI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# ================================

TOWN_HALL_INCOME = {1:5, 2:10, 3:20, 4:45, 5:100}

TOWN_HALL_UPGRADE_COST = {
    2: {"gold": 50, "wood": 100, "stone": 0},
    3: {"gold": 500, "wood": 400, "stone": 0},
    4: {"gold": 2000, "wood": 1200, "stone": 250},
    5: {"gold": 10000, "wood": 6000, "stone": 2500}
}

BUILDINGS_CONFIG = {
    "house": {
        "name": "Жилой район", "icon": "🏘️", "section": "social", "max_level": 5,
        "base_cost": {"gold": 50, "wood": 20, "stone": 0},
        "upgrade_costs": [
            {"gold": 50, "wood": 100, "stone": 50},
            {"gold": 250, "wood": 300, "stone": 125},
            {"gold": 1500, "wood": 1000, "stone": 400},
            {"gold": 7200, "wood": 5300, "stone": 2450}
        ],
        "population_bonus": [20, 20, 40, 100, 250]
    },
    "tavern": {
        "name": "Корчма", "icon": "🍺", "section": "social", "max_level": 5,
        "base_cost": {"gold": 100, "wood": 100, "stone": 25},
        "upgrade_costs": [
            {"gold": 250, "wood": 250, "stone": 100},
            {"gold": 900, "wood": 900, "stone": 400},
            {"gold": 1800, "wood": 1800, "stone": 800},
            {"gold": 8000, "wood": 4000, "stone": 2500}
        ],
        "income": [
            {"gold": 3, "food": -3, "populationGrowth": 1},
            {"gold": 6, "food": -5, "populationGrowth": 2},
            {"gold": 15, "food": -12, "populationGrowth": 3},
            {"gold": 30, "food": -22, "populationGrowth": 4},
            {"gold": 70, "food": -50, "populationGrowth": 5}
        ],
        "requiredTownHall": [2, 3, 4, 5, 5]
    },
    "bath": {
        "name": "Купели", "icon": "💧", "section": "social", "max_level": 5,
        "base_cost": {"gold": 100, "wood": 100, "stone": 25},
        "upgrade_costs": [
            {"gold": 250, "wood": 250, "stone": 100},
            {"gold": 900, "wood": 900, "stone": 400},
            {"gold": 1800, "wood": 1800, "stone": 800},
            {"gold": 8000, "wood": 4000, "stone": 2500}
        ],
        "income": [
            {"gold": 2, "populationGrowth": 1},
            {"gold": 4, "populationGrowth": 2},
            {"gold": 10, "populationGrowth": 2},
            {"gold": 20, "populationGrowth": 3},
            {"gold": 50, "populationGrowth": 3}
        ],
        "requiredTownHall": [3, 4, 4, 5, 5]
    },
    "farm": {
        "name": "Ферма", "icon": "🌾", "section": "economic", "max_level": 5,
        "base_cost": {"gold": 30, "wood": 40, "stone": 0},
        "upgrade_costs": [
            {"gold": 50, "wood": 100, "stone": 0},
            {"gold": 250, "wood": 300, "stone": 0},
            {"gold": 1000, "wood": 1000, "stone": 150},
            {"gold": 5200, "wood": 6300, "stone": 2450}
        ],
        "income": [
            {"food": 10}, {"food": 25}, {"food": 60}, {"food": 120}, {"food": 260}
        ]
    },
    "lumber": {
        "name": "Лесопилка", "icon": "🪵", "section": "economic", "max_level": 5,
        "base_cost": {"gold": 40, "wood": 30, "stone": 0},
        "upgrade_costs": [
            {"gold": 50, "wood": 100, "stone": 0},
            {"gold": 350, "wood": 200, "stone": 50},
            {"gold": 1300, "wood": 900, "stone": 550},
            {"gold": 7000, "wood": 4500, "stone": 3500}
        ],
        "income": [
            {"wood": 10}, {"wood": 20}, {"wood": 40}, {"wood": 100}, {"wood": 200}
        ]
    },
    "quarry": {
        "name": "Каменоломня", "icon": "⛰️", "section": "economic", "max_level": 5,
        "base_cost": {"gold": 20, "wood": 80, "stone": 0},
        "upgrade_costs": [
            {"gold": 50, "wood": 150, "stone": 0},
            {"gold": 250, "wood": 350, "stone": 100},
            {"gold": 1000, "wood": 1700, "stone": 150},
            {"gold": 6200, "wood": 7300, "stone": 1450}
        ],
        "income": [
            {"stone": 5}, {"stone": 15}, {"stone": 35}, {"stone": 80}, {"stone": 160}
        ]
    }
}

def verify_telegram_data(init_data: str):
    try:
        parsed_data = parse_qs(init_data)
        if 'hash' not in parsed_data:
            return None
        
        data_check_pairs = []
        for key in sorted(parsed_data.keys()):
            if key != 'hash':
                data_check_pairs.append(f"{key}={parsed_data[key][0]}")
        
        data_check_string = "\n".join(data_check_pairs)
        received_hash = parsed_data['hash'][0]
        
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if expected_hash != received_hash:
            return None
        
        if 'user' in parsed_data:
            return json.loads(parsed_data['user'][0])
        return None
    except:
        return None

def calculate_building_upgrade_cost(building_id, current_level):
    config = BUILDINGS_CONFIG.get(building_id)
    if not config or current_level >= config["max_level"]:
        return {"gold": 0, "wood": 0, "stone": 0}
    return config["upgrade_costs"][current_level - 1]

def calculate_population_max(buildings):
    max_pop = 10
    for b in buildings:
        if b["id"] == "house":
            config = BUILDINGS_CONFIG["house"]
            for i in range(b["level"]):
                max_pop += config["population_bonus"][i]
            break
    return max_pop

def calculate_hourly_income_and_growth(buildings, town_hall_level, current_population, max_population, current_food):
    income = {"gold": TOWN_HALL_INCOME.get(town_hall_level, 0), "wood": 0, "food": 0, "stone": 0}
    
    for b in buildings:
        config = BUILDINGS_CONFIG.get(b["id"])
        if not config or b["level"] == 0 or not config.get("income"):
            continue
        inc = config["income"][b["level"] - 1]
        for resource, value in inc.items():
            if resource in income:
                income[resource] += value
    
    food_prod = income["food"]
    food_needed = current_population
    food_left = food_prod - food_needed
    pop_growth = 0
    
    if food_left >= 0:
        income["food"] = food_left
        potential = 3
        if current_population + potential <= max_population:
            pop_growth = potential
        else:
            pop_growth = max_population - current_population
    else:
        total_food = current_food + food_prod
        if total_food >= food_needed:
            income["food"] = total_food - food_needed
        else:
            income["food"] = 0
    
    return income, pop_growth

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth', methods=['POST'])
def auth():
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
        result = supabase.table("players").select("*").eq("telegram_id", telegram_id).execute()
        now = int(time.time() * 1000)
        
        if result.data and len(result.data) > 0:
            player = result.data[0]
            
            buildings = []
            if player.get('buildings'):
                try:
                    buildings = json.loads(player.get('buildings'))
                except:
                    buildings = []
            
            owned_avatars = player.get('owned_avatars', '["male_free","female_free"]')
            if isinstance(owned_avatars, str):
                try:
                    owned_avatars = json.loads(owned_avatars)
                except:
                    owned_avatars = ['male_free', 'female_free']
            
            max_pop = calculate_population_max(buildings)
            supabase.table("players").update({'last_collection': now, 'population_max': max_pop}).eq('id', player['id']).execute()
            
            return jsonify({
                'success': True,
                'user': {
                    'id': player.get('telegram_id'),
                    'username': player.get('username', ''),
                    'game_login': player.get('game_login', ''),
                    'avatar': player.get('avatar', 'male_free'),
                    'owned_avatars': owned_avatars,
                    'gold': player.get('gold', 100),
                    'wood': player.get('wood', 50),
                    'food': player.get('food', 50),
                    'stone': player.get('stone', 0),
                    'level': player.get('level', 1),
                    'population_current': player.get('population_current', 10),
                    'population_max': max_pop,
                    'lastCollection': now
                },
                'buildings': buildings,
                'config': BUILDINGS_CONFIG
            })
        else:
            initial_buildings = [
                {"id": "house", "level": 1},
                {"id": "farm", "level": 1},
                {"id": "lumber", "level": 1}
            ]
            max_pop = calculate_population_max(initial_buildings)
            
            new_player = {
                'telegram_id': telegram_id,
                'username': username,
                'game_login': '',
                'avatar': 'male_free',
                'owned_avatars': json.dumps(['male_free', 'female_free']),
                'gold': 100,
                'wood': 50,
                'food': 50,
                'stone': 0,
                'level': 1,
                'population_current': 10,
                'population_max': max_pop,
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
                    'avatar': 'male_free',
                    'owned_avatars': ['male_free', 'female_free'],
                    'gold': 100,
                    'wood': 50,
                    'food': 50,
                    'stone': 0,
                    'level': 1,
                    'population_current': 10,
                    'population_max': max_pop,
                    'lastCollection': now
                },
                'buildings': initial_buildings,
                'config': BUILDINGS_CONFIG
            })
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/action', methods=['POST'])
def game_action():
    data = request.json
    init_data = data.get('initData', '')
    action_type = data.get('action')
    action_data = data.get('data', {})
    
    telegram_user = verify_telegram_data(init_data)
    if not telegram_user:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    telegram_id = str(telegram_user['id'])
    
    try:
        result = supabase.table("players").select("*").eq("telegram_id", telegram_id).execute()
        if not result.data:
            return jsonify({'success': False, 'error': 'Player not found'}), 404
        
        player = result.data[0]
        player_id = player['id']
        
        gold = player['gold']
        wood = player['wood']
        food = player['food']
        stone = player['stone']
        level = player['level']
        population_current = player.get('population_current', 10)
        population_max = player.get('population_max', 20)
        game_login = player.get('game_login', '')
        avatar = player.get('avatar', 'male_free')
        
        owned_avatars = player.get('owned_avatars', '["male_free","female_free"]')
        if isinstance(owned_avatars, str):
            try:
                owned_avatars = json.loads(owned_avatars)
            except:
                owned_avatars = ['male_free', 'female_free']
        
        buildings = []
        if player.get('buildings'):
            try:
                buildings = json.loads(player.get('buildings'))
            except:
                buildings = []
        
        last_collection = player.get('last_collection', int(time.time() * 1000))
        response_data = {'success': True}
        
        # ===== СБОР РЕСУРСОВ =====
        if action_type == 'collect':
            now = int(time.time() * 1000)
            time_passed = now - last_collection
            hours_passed = time_passed / (60 * 60 * 1000)
            
            if hours_passed > 0:
                total_gold = 0
                total_wood = 0
                total_food = 0
                total_stone = 0
                total_pop = 0
                
                current_pop = population_current
                current_food = food
                
                for _ in range(int(hours_passed)):
                    inc, growth = calculate_hourly_income_and_growth(buildings, level, current_pop, population_max, current_food)
                    total_gold += inc["gold"]
                    total_wood += inc["wood"]
                    total_food += inc["food"]
                    total_stone += inc["stone"]
                    total_pop += growth
                    current_pop += growth
                    current_food += inc["food"]
                
                gold += total_gold
                wood += total_wood
                food += total_food
                stone += total_stone
                population_current = min(current_pop, population_max)
                last_collection = now
                
                supabase.table("players").update({
                    'gold': gold, 'wood': wood, 'food': food, 'stone': stone,
                    'population_current': population_current, 'last_collection': last_collection
                }).eq('id', player_id).execute()
            
            response_data['state'] = {
                'gold': gold, 'wood': wood, 'food': food, 'stone': stone,
                'level': level, 'population_current': population_current, 'population_max': population_max,
                'game_login': game_login, 'avatar': avatar, 'owned_avatars': owned_avatars,
                'buildings': buildings, 'lastCollection': last_collection
            }
        
        # ===== ПОСТРОЙКА =====
        elif action_type == 'build':
            building_id = action_data.get('building_id')
            if building_id not in BUILDINGS_CONFIG:
                return jsonify({'success': False, 'error': 'Unknown building'})
            
            if any(b['id'] == building_id for b in buildings):
                return jsonify({'success': False, 'error': 'Building already exists'})
            
            cost = BUILDINGS_CONFIG[building_id]["base_cost"]
            if gold < cost['gold'] or wood < cost['wood'] or stone < cost['stone']:
                return jsonify({'success': False, 'error': 'Not enough resources'})
            
            gold -= cost['gold']
            wood -= cost['wood']
            stone -= cost['stone']
            
            buildings.append({"id": building_id, "level": 1})
            population_max = calculate_population_max(buildings)
            
            supabase.table("players").update({
                'gold': gold, 'wood': wood, 'stone': stone,
                'buildings': json.dumps(buildings), 'population_max': population_max
            }).eq('id', player_id).execute()
            
            response_data['state'] = {
                'gold': gold, 'wood': wood, 'food': food, 'stone': stone,
                'level': level, 'population_current': population_current, 'population_max': population_max,
                'game_login': game_login, 'avatar': avatar, 'owned_avatars': owned_avatars,
                'buildings': buildings, 'lastCollection': last_collection
            }
        
        # ===== УЛУЧШЕНИЕ =====
        elif action_type == 'upgrade':
            building_id = action_data.get('building_id')
            building = next((b for b in buildings if b['id'] == building_id), None)
            if not building:
                return jsonify({'success': False, 'error': 'Building not found'})
            
            current_level = building['level']
            config = BUILDINGS_CONFIG[building_id]
            
            if current_level >= config["max_level"]:
                return jsonify({'success': False, 'error': 'Max level reached'})
            
            if level < (config.get('requiredTownHall', [current_level + 1])[current_level] or current_level + 1):
                return jsonify({'success': False, 'error': f'Требуется уровень {current_level + 1}'})
            
            cost = calculate_building_upgrade_cost(building_id, current_level)
            if gold < cost['gold'] or wood < cost['wood'] or stone < cost['stone']:
                return jsonify({'success': False, 'error': 'Not enough resources'})
            
            gold -= cost['gold']
            wood -= cost['wood']
            stone -= cost['stone']
            building['level'] = current_level + 1
            population_max = calculate_population_max(buildings)
            
            supabase.table("players").update({
                'gold': gold, 'wood': wood, 'stone': stone,
                'buildings': json.dumps(buildings), 'population_max': population_max
            }).eq('id', player_id).execute()
            
            response_data['state'] = {
                'gold': gold, 'wood': wood, 'food': food, 'stone': stone,
                'level': level, 'population_current': population_current, 'population_max': population_max,
                'game_login': game_login, 'avatar': avatar, 'owned_avatars': owned_avatars,
                'buildings': buildings, 'lastCollection': last_collection
            }
        
        # ===== УЛУЧШЕНИЕ РАТУШИ =====
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
            
            supabase.table("players").update({'gold': gold, 'wood': wood, 'stone': stone, 'level': level}).eq('id', player_id).execute()
            
            response_data['state'] = {
                'gold': gold, 'wood': wood, 'food': food, 'stone': stone,
                'level': level, 'population_current': population_current, 'population_max': population_max,
                'game_login': game_login, 'avatar': avatar, 'owned_avatars': owned_avatars,
                'buildings': buildings, 'lastCollection': last_collection
            }
        
        # ===== СМЕНА ИМЕНИ (ПРИ РЕГИСТРАЦИИ) =====
        elif action_type == 'set_login':
            new_login = action_data.get('game_login', '').strip()
            if not new_login:
                return jsonify({'success': False, 'error': 'Login cannot be empty'})
            if len(new_login) > 12:
                new_login = new_login[:12]
            
            supabase.table("players").update({'game_login': new_login}).eq('id', player_id).execute()
            
            response_data['state'] = {
                'game_login': new_login,
                'gold': gold,
                'wood': wood,
                'food': food,
                'stone': stone,
                'level': level,
                'population_current': population_current,
                'population_max': population_max,
                'avatar': avatar,
                'owned_avatars': owned_avatars,
                'buildings': buildings,
                'lastCollection': last_collection
            }
        
        # ===== ПЛАТНАЯ СМЕНА ИМЕНИ =====
        elif action_type == 'change_name_paid':
            new_name = action_data.get('game_login', '').strip()
            price = 5000
            if not new_name:
                return jsonify({'success': False, 'error': 'Name cannot be empty'})
            if len(new_name) > 12:
                new_name = new_name[:12]
            if gold < price:
                return jsonify({'success': False, 'error': 'Not enough gold'})
            
            gold -= price
            supabase.table("players").update({'game_login': new_name, 'gold': gold}).eq('id', player_id).execute()
            
            response_data['state'] = {
                'game_login': new_name,
                'gold': gold, 'wood': wood, 'food': food, 'stone': stone,
                'level': level, 'population_current': population_current, 'population_max': population_max,
                'avatar': avatar, 'owned_avatars': owned_avatars,
                'buildings': buildings, 'lastCollection': last_collection
            }
        
        # ===== ПОКУПКА АВАТАРА =====
        elif action_type == 'buy_avatar':
            new_avatar = action_data.get('avatar', '')
            price = action_data.get('price', 0)
            
            if new_avatar in owned_avatars:
                return jsonify({'success': False, 'error': 'Already owned'})
            if gold < price:
                return jsonify({'success': False, 'error': 'Not enough gold'})
            
            gold -= price
            owned_avatars.append(new_avatar)
            supabase.table("players").update({
                'gold': gold,
                'owned_avatars': json.dumps(owned_avatars)
            }).eq('id', player_id).execute()
            
            response_data['state'] = {
                'gold': gold, 'wood': wood, 'food': food, 'stone': stone,
                'level': level, 'population_current': population_current, 'population_max': population_max,
                'game_login': game_login, 'avatar': avatar, 'owned_avatars': owned_avatars,
                'buildings': buildings, 'lastCollection': last_collection
            }
        
        # ===== ВЫБОР АВАТАРА =====
        elif action_type == 'select_avatar':
            new_avatar = action_data.get('avatar', '')
            if new_avatar not in owned_avatars:
                return jsonify({'success': False, 'error': 'Avatar not owned'})
            
            supabase.table("players").update({'avatar': new_avatar}).eq('id', player_id).execute()
            
            response_data['state'] = {
                'avatar': new_avatar,
                'gold': gold, 'wood': wood, 'food': food, 'stone': stone,
                'level': level, 'population_current': population_current, 'population_max': population_max,
                'game_login': game_login, 'owned_avatars': owned_avatars,
                'buildings': buildings, 'lastCollection': last_collection
            }
        
        else:
            return jsonify({'success': False, 'error': 'Unknown action'})
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Action error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clan/create', methods=['POST'])
def create_clan():
    return jsonify({'success': True})

@app.route('/api/clans/top', methods=['GET'])
def top_clans():
    try:
        result = supabase.table("players").select("*").order('gold', desc=True).limit(10).execute()
        return jsonify({'players': result.data})
    except:
        return jsonify({'players': []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


