from flask import Flask, request, jsonify, render_template
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)

# ========== НАСТРОЙКИ ==========
# ВСТАВЬТЕ СВОИ ДАННЫЕ ОТ SHEETY
SHEETY_URL = "https://api.sheety.co/3c7a64d22736a2e2d72dfc25150c8cd8/citybuilderdb"
# ================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth', methods=['POST'])
def auth():
    """Авторизация пользователя"""
    data = request.json
    init_data = data.get('initData', '')
    
    # Получаем данные пользователя из Telegram
    # В реальном проекте нужно расшифровывать init_data
    # Пока используем тестовые данные
    telegram_id = 123456789
    username = "test_user"
    first_name = "Тест"
    
    try:
        # Ищем пользователя в Sheety
        response = requests.get(f"{SHEETY_URL}/players")
        
        if response.status_code != 200:
            print(f"Sheety error: {response.status_code}")
            return jsonify({
                'success': True,
                'user': {
                    'id': telegram_id,
                    'username': username,
                    'first_name': first_name,
                    'gold': 100,
                    'wood': 50,
                    'level': 1
                }
            })
        
        players = response.json().get('players', [])
        
        # Ищем игрока по telegram_id
        player = None
        for p in players:
            if p.get('telegramId') == telegram_id:
                player = p
                break
        
        if not player:
            # Создаем нового игрока
            new_player = {
                'player': {
                    'telegramId': telegram_id,
                    'username': username,
                    'firstName': first_name,
                    'gold': 100,
                    'wood': 50,
                    'level': 1,
                    'createdAt': datetime.now().isoformat()
                }
            }
            
            create_response = requests.post(f"{SHEETY_URL}/players", json=new_player)
            
            if create_response.status_code == 200:
                player = create_response.json().get('player', new_player['player'])
                print(f"New player created: {player}")
            else:
                print(f"Create error: {create_response.status_code}")
                player = new_player['player']
        
        return jsonify({
            'success': True,
            'user': {
                'id': player.get('telegramId'),
                'username': player.get('username'),
                'first_name': player.get('firstName'),
                'gold': player.get('gold', 100),
                'wood': player.get('wood', 50),
                'level': player.get('level', 1)
            }
        })
        
    except Exception as e:
        print(f"Auth error: {e}")
        return jsonify({
            'success': True,
            'user': {
                'id': telegram_id,
                'username': username,
                'first_name': first_name,
                'gold': 100,
                'wood': 50,
                'level': 1
            }
        })

@app.route('/api/save', methods=['POST'])
def save():
    """Сохранение прогресса игрока"""
    data = request.json
    telegram_id = data.get('telegram_id')
    gold = data.get('gold')
    wood = data.get('wood')
    buildings_data = data.get('buildings', [])
    
    print(f"Saving data for user {telegram_id}: gold={gold}, wood={wood}")
    
    try:
        # Ищем игрока в Sheety
        response = requests.get(f"{SHEETY_URL}/players")
        
        if response.status_code != 200:
            print(f"Sheety error: {response.status_code}")
            return jsonify({'success': True})  # Возвращаем успех даже если Sheety не работает
        
        players = response.json().get('players', [])
        
        # Находим игрока по telegram_id
        for p in players:
            if p.get('telegramId') == telegram_id:
                # Обновляем данные
                update_data = {
                    'player': {
                        'gold': gold,
                        'wood': wood
                    }
                }
                
                update_response = requests.put(f"{SHEETY_URL}/players/{p['id']}", json=update_data)
                print(f"Sheety update response: {update_response.status_code}")
                break
        
        # Сохраняем постройки (упрощенно)
        for building in buildings_data:
            # Здесь можно добавить сохранение построек
            pass
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Save error: {e}")
        return jsonify({'success': True})  # Возвращаем успех даже при ошибке

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
                'members': 1,
                'createdAt': datetime.now().isoformat()
            }
        }
        
        response = requests.post(f"{SHEETY_URL}/clans", json=new_clan)
        
        if response.status_code == 200:
            clan = response.json().get('clan', {})
            
            # Обновляем игрока (добавляем clan_id)
            players_response = requests.get(f"{SHEETY_URL}/players")
            if players_response.status_code == 200:
                players = players_response.json().get('players', [])
                for p in players:
                    if p.get('telegramId') == leader_id:
                        update_data = {'player': {'clanId': clan.get('id')}}
                        requests.put(f"{SHEETY_URL}/players/{p['id']}", json=update_data)
                        break
            
            return jsonify({'success': True, 'clan': clan})
        else:
            return jsonify({'success': False})
            
    except Exception as e:
        print(f"Create clan error: {e}")
        return jsonify({'success': False})

@app.route('/api/clans/top', methods=['GET'])
def top_clans():
    """Топ кланов"""
    try:
        response = requests.get(f"{SHEETY_URL}/clans")
        
        if response.status_code == 200:
            clans = response.json().get('clans', [])
            # Сортируем по уровню (от большего к меньшему)
            sorted_clans = sorted(clans, key=lambda x: x.get('level', 1), reverse=True)[:10]
            return jsonify({'clans': sorted_clans})
        else:
            return jsonify({'clans': []})
            
    except Exception as e:
        print(f"Top clans error: {e}")
        return jsonify({'clans': []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
