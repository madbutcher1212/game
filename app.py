from flask import Flask, request, jsonify, render_template
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)

# ========== ВАШ КЛЮЧ ==========
SHEETY_URL = "https://api.sheety.co/3c7a64d22736a2e2d72dfc25150c8cd8/citybuilderdb"
# ===============================

@app.route('/')
def index():
    print("➡️ Главная страница загружена")
    return render_template('index.html')

@app.route('/api/auth', methods=['POST'])
def auth():
    print("➡️ Получен запрос /api/auth")
    
    data = request.json
    telegram_id = 123456789  # В реальности брать из initData
    
    try:
        # Проверяем Sheety
        print(f"🔍 Проверяем Sheety: {SHEETY_URL}/players")
        response = requests.get(f"{SHEETY_URL}/players")
        print(f"📊 Sheety ответ при авторизации: статус {response.status_code}")
        
        if response.status_code == 200:
            players = response.json().get('players', [])
            print(f"👥 Найдено игроков в базе: {len(players)}")
            
            # Ищем игрока
            for p in players:
                if p.get('telegram_id') == telegram_id:
                    print(f"✅ Игрок найден в базе: {p.get('game_login')}")
                    return jsonify({
                        'success': True,
                        'user': {
                            'id': p.get('telegram_id'),
                            'game_login': p.get('game_login', ''),
                            'gold': p.get('gold', 100),
                            'wood': p.get('wood', 50),
                            'level': p.get('level', 1)
                        }
                    })
            
            print(f"👤 Игрок не найден, будет создан при сохранении")
    except Exception as e:
        print(f"❌ Ошибка при проверке Sheety: {e}")
    
    # Возвращаем нового игрока
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
    
    print(f"\n📦 ПОЛУЧЕНЫ ДАННЫЕ ДЛЯ СОХРАНЕНИЯ:")
    print(f"   telegram_id: {telegram_id}")
    print(f"   game_login: {game_login}")
    print(f"   gold: {gold}")
    print(f"   wood: {wood}")
    print(f"   level: {level}")
    print(f"   buildings: {buildings}")
    
    try:
        # Получаем список игроков из Sheety
        print(f"🔍 Запрашиваем список игроков из Sheety...")
        response = requests.get(f"{SHEETY_URL}/players")
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            players = response.json().get('players', [])
            print(f"👥 Получено игроков из Sheety: {len(players)}")
            
            # Ищем игрока
            found = False
            for p in players:
                if p.get('telegram_id') == telegram_id:
                    found = True
                    player_id = p['id']
                    print(f"✅ Игрок найден! ID в Sheety: {player_id}")
                    
                    # Подготавливаем данные для обновления
                    update_data = {
                        'player': {
                            'game_login': game_login,
                            'gold': gold,
                            'wood': wood,
                            'level': level,
                            'buildings': json.dumps(buildings)
                        }
                    }
                    print(f"📤 Отправляем данные в Sheety: {update_data}")
                    
                    # Отправляем запрос на обновление
                    update_response = requests.put(f"{SHEETY_URL}/players/{player_id}", json=update_data)
                    print(f"📥 Ответ от Sheety при обновлении: статус {update_response.status_code}")
                    
                    if update_response.status_code == 200:
                        print(f"✅ Данные успешно обновлены в Sheety!")
                        print(f"📋 Ответ: {update_response.json()}")
                    else:
                        print(f"❌ Ошибка при обновлении: {update_response.text}")
                    break
            
            if not found:
                print(f"👤 Игрок не найден, создаем нового...")
                
                # Создаем нового игрока
                new_player = {
                    'player': {
                        'telegram_id': telegram_id,
                        'game_login': game_login,
                        'gold': gold,
                        'wood': wood,
                        'level': level,
                        'buildings': json.dumps(buildings)
                    }
                }
                print(f"📤 Отправляем данные для создания: {new_player}")
                
                create_response = requests.post(f"{SHEETY_URL}/players", json=new_player)
                print(f"📥 Ответ от Sheety при создании: статус {create_response.status_code}")
                
                if create_response.status_code == 200:
                    print(f"✅ Новый игрок успешно создан в Sheety!")
                    print(f"📋 Ответ: {create_response.json()}")
                else:
                    print(f"❌ Ошибка при создании: {create_response.text}")
        else:
            print(f"❌ Не удалось получить список игроков. Статус: {response.status_code}")
            print(f"📋 Текст ошибки: {response.text}")
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при работе с Sheety: {e}")
        import traceback
        traceback.print_exc()
    
    print("✅ Запрос на сохранение обработан\n")
    return jsonify({'success': True})

@app.route('/api/clan/create', methods=['POST'])
def create_clan():
    return jsonify({'success': True})

@app.route('/api/clans/top', methods=['GET'])
def top_clans():
    return jsonify({'clans': []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

