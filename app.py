from flask import Flask, request, jsonify, render_template
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)

# ========== ВАШ URL ИЗ SHEETY ==========
SHEETY_URL = "https://api.sheety.co/ваш_ключ/cityBuilderDb"
# ========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth', methods=['POST'])
def auth():
    """Авторизация пользователя"""
    data = request.json
    telegram_id = 123456789  # В реальности брать из initData
    
    try:
        # Ищем пользователя
        response = requests.get(f"{SHEETY_URL}/players")
        
        if response.status_code == 200:
            players = response.json().get('players', [])
            
            # Ищем по telegram_id
            player = None
            for p in players:
                if p.get('telegram_id') == telegram_id:  # <-- здесь telegram_id
                    player = p
                    break
            
            if player:
                # Возвращаем данные существующего игрока
                return jsonify({
                    'success': True,
                    'user': {
                        'id': player.get('telegram_id'),
                        'game_login': player.get('game_login', ''),  # <-- здесь game_login
                        'gold': player.get('gold', 100),
                        'wood': player.get('wood', 50),
                        'level': player.get('level', 1)
                    }
                })
            else:
                # Создаем нового
                return jsonify({
                    'success': True,
                    'user': {
                        'id': telegram_id,
                        'game_login': '',
                        'gold': 100,
                        'wood': 50,
                        'level': 1
                    }
                })
    except Exception as e:
        print(f"Auth error: {e}")
    
    # Если ошибка - возвращаем тестовые данные
    return jsonify({
        'success': True,
        'user': {
            'id': telegram_id,
            'game_login': '',
            'gold': 100,
            'wood': 50,
            'level': 1
        }
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
    
    print(f"💾 Сохраняем: telegram_id={telegram_id}, game_login={game_login}, gold={gold}, wood={wood}")
    
    try:
        # Получаем список игроков
        response = requests.get(f"{SHEETY_URL}/players")
        
        if response.status_code == 200:
            players = response.json().get('players', [])
            
            # Ищем игрока
            found = False
            for p in players:
                if p.get('telegram_id') == telegram_id:  # <-- ищем по telegram_id
                    found = True
                    player_id = p['id']
                    
                    # Обновляем
                    update_data = {
                        'player': {
                            'game_login': game_login,  # <-- game_login
                            'gold': gold,
                            'wood': wood,
                            'level': level,
                            'buildings': json.dumps(buildings)
                        }
                    }
                    
                    update_response = requests.put(f"{SHEETY_URL}/players/{player_id}", json=update_data)
                    print(f"✅ Обновлено, статус: {update_response.status_code}")
                    break
            
            if not found:
                # Создаем нового
                new_player = {
                    'player': {
                        'telegram_id': telegram_id,  # <-- telegram_id
                        'game_login': game_login,    # <-- game_login
                        'gold': gold,
                        'wood': wood,
                        'level': level,
                        'buildings': json.dumps(buildings)
                    }
                }
                
                create_response = requests.post(f"{SHEETY_URL}/players", json=new_player)
                print(f"✅ Создано, статус: {create_response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
    
    return jsonify({'success': True})

@app.route('/api/clan/create', methods=['POST'])
def create_clan():
    return jsonify({'success': True})

@app.route('/api/clans/top', methods=['GET'])
def top_clans():
    return jsonify({'clans': []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
