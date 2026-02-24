from flask import Flask, request, jsonify, render_template
from supabase import create_client, Client
import os
import json
import hmac
import hashlib
from urllib.parse import parse_qs
from datetime import datetime

app = Flask(__name__)

# ========== НАСТРОЙКИ ==========
SUPABASE_URL = "https://xevwktdwyioyantuqntb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhldndrdGR3eWlveWFudHVxbnRiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE4ODI2NTAsImV4cCI6MjA4NzQ1ODY1MH0.jC8jqGBv_yrbYg_x4XQradxxbkDtsXsQ9EBT0Iabed4"

# Токен твоего бота (из @BotFather)
BOT_TOKEN = "8596066162:AAEm2DSAFhKemedKC8rT4RfFY4fjUhVBCvI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# ================================

# Конфиг зданий (единый источник правды на сервере)
BUILDINGS_CONFIG = {
    'house': {
        'name': '🏠 Дом',
        'icon': '🏠',
        'cost_gold': 50,
        'cost_wood': 20,
        'cost_stone': 0,
        'cost_food': 0,
        'gold_prod': 0,
        'wood_prod': 0,
        'food_prod': 0,
        'stone_prod': 0,
        'population': 2
    },
    'farm': {
        'name': '🌾 Ферма',
        'icon': '🌾',
        'cost_gold': 30,
        'cost_wood': 40,
        'cost_stone': 0,
        'cost_food': 0,
        'gold_prod': 0,
        'wood_prod': 0,
        'food_prod': 8,      # Ферма даёт 8 пищи
        'stone_prod': 0,
        'population': 0
    },
    'lumber': {
        'name': '🪵 Лесопилка',
        'icon': '🪵',
        'cost_gold': 40,
        'cost_wood': 30,
        'cost_stone': 0,
        'cost_food': 0,
        'gold_prod': 0,
        'wood_prod': 4,
        'food_prod': 0,
        'stone_prod': 0,
        'population': 1
    },
    'quarry': {  # НОВОЕ: Каменоломня
        'name': '⛰️ Каменоломня',
        'icon': '⛰️',
        'cost_gold': 60,
        'cost_wood': 40,
        'cost_stone': 0,
        'cost_food': 0,
        'gold_prod': 0,
        'wood_prod': 0,
        'food_prod': 0,
        'stone_prod': 3,      # Даёт 3 камня
        'population': 1
    },
    'market': {
        'name': '🏪 Рынок',
        'icon': '🏪',
        'cost_gold': 80,
        'cost_wood': 60,
        'cost_stone': 20,
        'cost_food': 0,
        'gold_prod': 10,
        'wood_prod': 2,
        'food_prod': 0,
        'stone_prod': 0,
        'population': 2
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
        else:
            print("❌ Нет данных пользователя в initData")
            return None
        
    except Exception as e:
        print(f"❌ Ошибка при проверке данных: {e}")
        return None

@app.route('/')
def index():
    print("➡️ Главная страница загружена")
    return render_template('index.html')

@app.route('/api/auth', methods=['POST'])
def auth():
    """Авторизация пользователя"""
    print("➡️ Получен запрос /api/auth")
    
    data = request.json
    init_data = data.get('initData', '')
    
    if not init_data:
        return jsonify({'success': False, 'error': 'No initData'}), 400
    
    telegram_user = verify_telegram_data(init_data)
    
    if not telegram_user:
        return jsonify({'success': False, 'error': 'Invalid Telegram data'}), 401
    
    telegram_id = str(telegram_user['id'])
    username = telegram_user.get('username', '')
    
    print(f"👤 Авторизация пользователя: {telegram_id}, @{username}")
    
    try:
        result = supabase.table("players") \
            .select("*") \
            .eq("telegram_id", telegram_id) \
            .execute()
        
        if result.data and len(result.data) > 0:
            player = result.data[0]
            print(f"✅ Игрок найден в Supabase: {player.get('game_login')}")
            
            buildings = []
            if player.get('buildings'):
                try:
                    buildings = json.loads(player.get('buildings'))
                except:
                    buildings = []
            
            return jsonify({
                'success': True,
                'user': {
                    'id': player.get('telegram_id'),
                    'username': player.get('username', ''),
                    'game_login': player.get('game_login', ''),
                    'gold': player.get('gold', 100),
                    'wood': player.get('wood', 50),
                    'food': player.get('food', 50),     # НОВОЕ
                    'stone': player.get('stone', 0),    # НОВОЕ
                    'level': player.get('level', 1)
                },
                'buildings': buildings,
                'config': BUILDINGS_CONFIG
            })
        else:
            print(f"👤 Создаем нового игрока с telegram_id {telegram_id}")
            
            new_player = {
                'telegram_id': telegram_id,
                'username': username,
                'game_login': '',
                'gold': 100,
                'wood': 50,
                'food': 50,      # НОВОЕ: начальная пища
                'stone': 0,       # НОВОЕ: начальный камень
                'level': 1,
                'buildings': json.dumps([])
            }
            
            insert_result = supabase.table("players") \
                .insert(new_player) \
                .execute()
            
            print(f"✅ Новый игрок создан")
            
            return jsonify({
                'success': True,
                'user': {
                    'id': telegram_id,
                    'username': username,
                    'game_login': '',
                    'gold': 100,
                    'wood': 50,
                    'food': 50,    # НОВОЕ
                    'stone': 0,     # НОВОЕ
                    'level': 1
                },
                'buildings': [],
                'config': BUILDINGS_CONFIG
            })
            
    except Exception as e:
        print(f"❌ Ошибка при работе с Supabase: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/action', methods=['POST'])
def game_action():
    """Выполнение игрового действия"""
    print("➡️ Получен запрос /api/action")
    
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
        
        # Текущие ресурсы (включая новые)
        gold = player['gold']
        wood = player['wood']
        food = player.get('food', 50)      # НОВОЕ: получаем из БД
        stone = player.get('stone', 0)      # НОВОЕ: получаем из БД
        level = player['level']
        
        buildings = []
        if player.get('buildings'):
            try:
                buildings = json.loads(player.get('buildings'))
            except:
                buildings = []
        
        buildings_dict = {}
        for b in buildings:
            buildings_dict[b['id']] = b['count']
        
        response_data = {'success': True}
        
        if action_type == 'build':
            building_id = action_data.get('building_id')
            
            if building_id not in BUILDINGS_CONFIG:
                return jsonify({'success': False, 'error': 'Unknown building'})
            
            config = BUILDINGS_CONFIG[building_id]
            
            # Проверяем все ресурсы
            if gold < config['cost_gold'] or \
               wood < config['cost_wood'] or \
               food < config['cost_food'] or \
               stone < config['cost_stone']:
                return jsonify({'success': False, 'error': 'Not enough resources'})
            
            # Списываем ресурсы
            gold -= config['cost_gold']
            wood -= config['cost_wood']
            food -= config['cost_food']
            stone -= config['cost_stone']
            
            # Увеличиваем счётчик построек
            current_count = buildings_dict.get(building_id, 0)
            buildings_dict[building_id] = current_count + 1
            
            # Пересчитываем уровень
            total_buildings = sum(buildings_dict.values())
            new_level = total_buildings // 5 + 1
            
            # Преобразуем обратно в список
            new_buildings = []
            for bid, count in buildings_dict.items():
                new_buildings.append({'id': bid, 'count': count})
            
            # Сохраняем в БД (включая новые ресурсы)
            supabase.table("players") \
                .update({
                    'gold': gold,
                    'wood': wood,
                    'food': food,      # НОВОЕ
                    'stone': stone,    # НОВОЕ
                    'level': new_level,
                    'buildings': json.dumps(new_buildings)
                }) \
                .eq('id', player_id) \
                .execute()
            
            print(f"✅ Построено {building_id}")
            
            response_data['state'] = {
                'gold': gold,
                'wood': wood,
                'food': food,      # НОВОЕ
                'stone': stone,    # НОВОЕ
                'level': new_level,
                'buildings': new_buildings
            }
            
        elif action_type == 'collect':
            # Сбор ресурсов (включая пищу и камень)
            gold_income = 0
            wood_income = 0
            food_income = 0    # НОВОЕ
            stone_income = 0   # НОВОЕ
            
            for bid, count in buildings_dict.items():
                if bid in BUILDINGS_CONFIG:
                    config = BUILDINGS_CONFIG[bid]
                    gold_income += config['gold_prod'] * count
                    wood_income += config['wood_prod'] * count
                    food_income += config['food_prod'] * count     # НОВОЕ
                    stone_income += config['stone_prod'] * count   # НОВОЕ
            
            # Базовый доход от уровня
            gold_income += level * 2
            wood_income += level * 1
            food_income += level * 1      # НОВОЕ: +1 пищи за уровень
            stone_income += level * 0      # Камень только с каменоломен
            
            gold += gold_income
            wood += wood_income
            food += food_income            # НОВОЕ
            stone += stone_income          # НОВОЕ
            
            # Сохраняем в БД
            supabase.table("players") \
                .update({
                    'gold': gold,
                    'wood': wood,
                    'food': food,      # НОВОЕ
                    'stone': stone     # НОВОЕ
                }) \
                .eq('id', player_id) \
                .execute()
            
            print(f"✅ Собрано: +{gold_income}💰, +{wood_income}🪵, +{food_income}🌾, +{stone_income}⛰️")
            
            response_data['state'] = {
                'gold': gold,
                'wood': wood,
                'food': food,      # НОВОЕ
                'stone': stone,    # НОВОЕ
                'level': level,
                'buildings': buildings
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
                'food': food,      # НОВОЕ
                'stone': stone,    # НОВОЕ
                'level': level,
                'buildings': buildings
            }
        
        else:
            return jsonify({'success': False, 'error': 'Unknown action'})
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении действия: {e}")
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
    print(f"🚀 Сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
