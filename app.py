from flask import Flask, request, jsonify, render_template
from supabase import create_client, Client
import os
import json
from datetime import datetime

app = Flask(__name__)

# ========== НАСТРОЙКИ SUPABASE ==========
SUPABASE_URL = "https://xevwktdwyioyantuqntb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhldndrdGR3eWlveWFudHVxbnRiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE4ODI2NTAsImV4cCI6MjA4NzQ1ODY1MH0.jC8jqGBv_yrbYg_x4XQradxxbkDtsXsQ9EBT0Iabed4"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# ========================================

@app.route('/')
def index():
    print("➡️ Главная страница загружена")
    return render_template('index.html')

@app.route('/api/auth', methods=['POST'])
def auth():
    """Авторизация пользователя"""
    print("➡️ Получен запрос /api/auth")
    
    data = request.json
    # В реальном проекте telegram_id берется из initData
    telegram_id = "123456789"
    
    try:
        # Ищем пользователя в Supabase
        result = supabase.table("players") \
            .select("*") \
            .eq("telegram_id", telegram_id) \
            .execute()
        
        if result.data and len(result.data) > 0:
            # Пользователь найден
            player = result.data[0]
            print(f"✅ Игрок найден: {player.get('game_login')}")
            
            # Загружаем постройки из JSON
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
                    'game_login': player.get('game_login', ''),
                    'gold': player.get('gold', 100),
                    'wood': player.get('wood', 50),
                    'level': player.get('level', 1)
                },
                'buildings': buildings
            })
        else:
            print(f"👤 Новый игрок с telegram_id {telegram_id}")
            return jsonify({
                'success': True,
                'user': {
                    'id': telegram_id,
                    'game_login': '',
                    'gold': 100,
                    'wood': 50,
                    'level': 1
                },
                'buildings': []
            })
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        return jsonify({
            'success': True,
            'user': {
                'id': telegram_id,
                'game_login': '',
                'gold': 100,
                'wood': 50,
                'level': 1
            },
            'buildings': []
        })

@app.route('/api/save', methods=['POST'])
def save():
    """Сохранение прогресса"""
    data = request.json
    telegram_id = data.get('telegram_id')
    game_login = data.get('game_login', '')
    gold = data.get('gold')
    wood = data.get('wood')
    level = data.get('level', 1)
    buildings = data.get('buildings', [])
    
    print(f"\n📦 СОХРАНЯЕМ В SUPABASE:")
    print(f"   telegram_id: {telegram_id}")
    print(f"   game_login: {game_login}")
    print(f"   gold: {gold}")
    print(f"   wood: {wood}")
    print(f"   level: {level}")
    print(f"   buildings: {len(buildings)} построек")
    
    if not telegram_id:
        return jsonify({'success': False, 'error': 'No telegram_id'})
    
    try:
        # Преобразуем buildings в JSON строку
        buildings_json = json.dumps(buildings, ensure_ascii=False)
        
        # Проверяем, есть ли уже такой игрок
        result = supabase.table("players") \
            .select("*") \
            .eq("telegram_id", telegram_id) \
            .execute()
        
        if result.data and len(result.data) > 0:
            # Обновляем существующего
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
            print(f"✅ Данные обновлены для игрока {player_id}")
        else:
            # Создаем нового
            insert_result = supabase.table("players") \
                .insert({
                    'telegram_id': telegram_id,
                    'game_login': game_login,
                    'gold': gold,
                    'wood': wood,
                    'level': level,
                    'buildings': buildings_json
                }) \
                .execute()
            print(f"✅ Новый игрок создан")
            
    except Exception as e:
        print(f"❌ Ошибка сохранения в Supabase: {e}")
    
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
