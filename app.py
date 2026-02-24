from flask import Flask, request, jsonify, render_template
import requests
import os
import json

app = Flask(__name__)

# Настройки Sheety - ВСТАВЬТЕ СВОИ ДАННЫЕ
SHEETY_URL = "https://api.sheety.co/3c7a64d22736a2e2d72dfc25150c8cd8/citybuilderdb"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth', methods=['POST'])
def auth():
    """Вход в игру"""
    data = request.json
    init_data = data.get('initData', '')
    
    # Для теста используем тестового пользователя
    # В реальной игре нужно будет расшифровать init_data из Telegram
    telegram_id = 123456789
    username = "test_user"
    
    # Проверяем, есть ли пользователь в Sheety
    try:
        response = requests.get(f"{SHEETY_URL}/players")
        players = response.json().get('players', [])
        
        # Ищем игрока
        player = None
        for p in players:
            if p.get('telegramId') == telegram_id:
                player = p
                break
        
        if not player:
            # Создаем нового
            new_player = {
                'player': {
                    'telegramId': telegram_id,
                    'username': username,
                    'gold': 100,
                    'wood': 50,
                    'level': 1
                }
            }
            create_response = requests.post(f"{SHEETY_URL}/players", json=new_player)
            player = create_response.json().get('player', new_player['player'])
    except Exception as e:
        print(f"Sheety error: {e}")
        # Если Sheety не работает, возвращаем тестовые данные
        return jsonify({
            'success': True,
            'user': {
                'id': telegram_id,
                'username': username,
                'gold': 100,
                'wood': 50,
                'level': 1
            }
        })
    
    return jsonify({
        'success': True,
        'user': {
            'id': player.get('telegramId'),
            'username': player.get('username'),
            'gold': player.get('gold', 100),
            'wood': player.get('wood', 50),
            'level': player.get('level', 1)
        }
    })

@app.route('/api/save', methods=['POST'])
def save():
    """Сохранение прогресса"""
    data = request.json
    telegram_id = data.get('telegram_id')
    gold = data.get('gold')
    wood = data.get('wood')
    
    try:
        # Ищем игрока
        response = requests.get(f"{SHEETY_URL}/players")
        players = response.json().get('players', [])
        
        for p in players:
            if p.get('telegramId') == telegram_id:
                # Обновляем
                update_data = {
                    'player': {
                        'gold': gold,
                        'wood': wood
                    }
                }
                requests.put(f"{SHEETY_URL}/players/{p['id']}", json=update_data)
                break
    except Exception as e:
        print(f"Save error: {e}")
    
    return jsonify({'success': True})

@app.route('/api/clans/top', methods=['GET'])
def top_clans():
    """Топ кланов"""
    try:
        response = requests.get(f"{SHEETY_URL}/clans")
        clans = response.json().get('clans', [])
        # Сортируем по уровню
        sorted_clans = sorted(clans, key=lambda x: x.get('level', 1), reverse=True)[:10]
    except:
        sorted_clans = []
    
    return jsonify({'clans': sorted_clans})

@app.route('/api/clan/create', methods=['POST'])
def create_clan():
    """Создание клана"""
    data = request.json
    name = data.get('name')
    tag = data.get('tag')
    leader_id = data.get('leader_id')
    
    try:
        new_clan = {
            'clan': {
                'name': name,
                'tag': tag,
                'level': 1,
                'members': 1
            }
        }
        response = requests.post(f"{SHEETY_URL}/clans", json=new_clan)
        clan = response.json().get('clan', {})
        
        # Обновляем игрока
        players_response = requests.get(f"{SHEETY_URL}/players")
        players = players_response.json().get('players', [])
        for p in players:
            if p.get('telegramId') == leader_id:
                update_data = {'player': {'clanId': clan.get('id')}}
                requests.put(f"{SHEETY_URL}/players/{p['id']}", json=update_data)
                break
                
        return jsonify({'success': True, 'clan': clan})
    except Exception as e:
        print(f"Create clan error: {e}")
        return jsonify({'success': False})

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
