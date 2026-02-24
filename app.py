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

def verify_telegram_data(init_data: str):
    """Проверяет подпись Telegram Init Data и возвращает данные пользователя"""
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
    """Авторизация пользователя по данным из Telegram"""
    print("➡️ Получен запрос /api/auth")
    
    data = request.json
    init_data = data.get('initData', '')
    
    if not init_data:
        print("❌ Нет initData в запросе")
        return jsonify({'success': False, 'error': 'No initData'}), 400
    
    telegram_user = verify_telegram_data(init_data)
    
    if not telegram_user:
        print("❌ Не удалось проверить данные Telegram")
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
                    'level': player.get('level', 1)
                },
                'buildings': buildings
            })
        else:
            print(f"👤 Создаем нового игрока с telegram_id {telegram_id}")
            
            new_player = {
                'telegram_id': telegram_id,
                'username': username,
                'game_login': '',
                'gold': 100,
                'wood': 50,
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
                    'level': 1
                },
                'buildings': []
            })
            
    except Exception as e:
        print(f"❌ Ошибка при работе с Supabase: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/save', methods=['POST'])
def save():
    """Сохранение прогресса игрока"""
    data = request.json
    telegram_id = data.get('telegram_id')
    game_login = data.get('game_login', '')
    gold = data.get('gold')
    wood = data.get('wood')
    level = data.get('level', 1)
    buildings = data.get('buildings', [])
    
    if not telegram_id:
        return jsonify({'success': False, 'error': 'No telegram_id'}), 400
    
    if telegram_id == "123456":
        print("⚠️ Попытка сохранить тестовый ID, игнорируем")
        return jsonify({'success': True})
    
    print(f"\n📦 СОХРАНЯЕМ В SUPABASE:")
    print(f"   telegram_id: {telegram_id}")
    print(f"   game_login: {game_login}")
    print(f"   gold: {gold}")
    print(f"   wood: {wood}")
    print(f"   level: {level}")
    print(f"   buildings: {len(buildings)} построек")
    
    try:
        buildings_json = json.dumps(buildings, ensure_ascii=False)
        
        result = supabase.table("players") \
            .select("*") \
            .eq("telegram_id", telegram_id) \
            .execute()
        
        if result.data and len(result.data) > 0:
            player_id = result.data[0]['id']
            update_result = supabase.table("players") \
                .update({
                    'game_login': game_login,
                    'gold': gold,
                    'wood': wood,
                    'level': level,
                    'buildings': buildings_json
                }) \
                .eq('id', player_id) \
                .execute()
            print(f"✅ Данные обновлены в Supabase для игрока {player_id}")
        else:
            new_player = {
                'telegram_id': telegram_id,
                'game_login': game_login,
                'gold': gold,
                'wood': wood,
                'level': level,
                'buildings': buildings_json
            }
            insert_result = supabase.table("players") \
                .insert(new_player) \
                .execute()
            print(f"✅ Новый игрок создан в Supabase")
            
    except Exception as e:
        print(f"❌ Ошибка сохранения в Supabase: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': True})

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




