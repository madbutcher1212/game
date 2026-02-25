const API_URL = 'https://game-production-10ea.up.railway.app';

const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const AVATARS = {
    'male_free': {
        name: 'Мужской',
        url: 'https://raw.githubusercontent.com/madbutcher1212/game/main/static/avatars/male_free.png',
        price: 0
    },
    'female_free': {
        name: 'Женский',
        url: 'https://raw.githubusercontent.com/madbutcher1212/game/main/static/avatars/female_free.png',
        price: 0
    },
    'male_premium': {
        name: 'Лорд',
        url: 'https://raw.githubusercontent.com/madbutcher1212/game/main/static/avatars/male_premium.png',
        price: 25000
    },
    'female_premium': {
        name: 'Леди',
        url: 'https://raw.githubusercontent.com/madbutcher1212/game/main/static/avatars/female_premium.png',
        price: 25000
    }
};

let userData = {
    id: null,
    username: '',
    game_login: '',
    avatar: 'male_free',
    owned_avatars: ['male_free', 'female_free'],
    gold: 100,
    wood: 50,
    food: 50,
    stone: 0,
    level: 1,
    population_current: 10,
    population_max: 20,
    lastCollection: Date.now()
};

let buildings = [
    { id: 'house', level: 1 },
    { id: 'farm', level: 1 },
    { id: 'lumber', level: 1 }
];

const TOWN_HALL_INCOME = {1:5,2:10,3:20,4:45,5:100};

const TOWN_HALL_UPGRADE_COST = {
    2: {gold:50,wood:100,stone:0},
    3: {gold:500,wood:400,stone:0},
    4: {gold:2000,wood:1200,stone:250},
    5: {gold:10000,wood:6000,stone:2500}
};

const BUILDINGS_CONFIG = {
    'house': {
        name: 'Жилой район', icon: '🏘️', section: 'social', maxLevel: 5,
        baseCost: {gold:50,wood:20,stone:0},
        upgradeCosts: [
            {gold:50,wood:100,stone:50},
            {gold:250,wood:300,stone:125},
            {gold:1500,wood:1000,stone:400},
            {gold:7200,wood:5300,stone:2450}
        ],
        populationBonus: [20,20,40,100,250]
    },
    'tavern': {
        name: 'Корчма', icon: '🍺', section: 'social', maxLevel: 5,
        baseCost: {gold:100,wood:100,stone:25},
        upgradeCosts: [
            {gold:250,wood:250,stone:100},
            {gold:900,wood:900,stone:400},
            {gold:1800,wood:1800,stone:800},
            {gold:8000,wood:4000,stone:2500}
        ],
        income: [
            {gold:3, food: -3, populationGrowth: 1},
            {gold:6, food: -5, populationGrowth: 2},
            {gold:15, food: -12, populationGrowth: 3},
            {gold:30, food: -22, populationGrowth: 4},
            {gold:70, food: -50, populationGrowth: 5}
        ],
        requiredTownHall: [2,3,4,5,5]
    },
    'bath': {
        name: 'Купели', icon: '💧', section: 'social', maxLevel: 5,
        baseCost: {gold:100,wood:100,stone:25},
        upgradeCosts: [
            {gold:250,wood:250,stone:100},
            {gold:900,wood:900,stone:400},
            {gold:1800,wood:1800,stone:800},
            {gold:8000,wood:4000,stone:2500}
        ],
        income: [
            {gold:2, populationGrowth: 1},
            {gold:4, populationGrowth: 2},
            {gold:10, populationGrowth: 2},
            {gold:20, populationGrowth: 3},
            {gold:50, populationGrowth: 3}
        ],
        requiredTownHall: [3,4,4,5,5]
    },
    'farm': {
        name: 'Ферма', icon: '🌾', section: 'economic', maxLevel: 5,
        baseCost: {gold:30,wood:40,stone:0},
        upgradeCosts: [
            {gold:50,wood:100,stone:0},
            {gold:250,wood:300,stone:0},
            {gold:1000,wood:1000,stone:150},
            {gold:5200,wood:6300,stone:2450}
        ],
        income: [
            {food:10},{food:25},{food:60},{food:120},{food:260}
        ]
    },
    'lumber': {
        name: 'Лесопилка', icon: '🪵', section: 'economic', maxLevel: 5,
        baseCost: {gold:40,wood:30,stone:0},
        upgradeCosts: [
            {gold:50,wood:100,stone:0},
            {gold:350,wood:200,stone:50},
            {gold:1300,wood:900,stone:550},
            {gold:7000,wood:4500,stone:3500}
        ],
        income: [
            {wood:10},{wood:20},{wood:40},{wood:100},{wood:200}
        ]
    },
    'quarry': {
        name: 'Каменоломня', icon: '⛰️', section: 'economic', maxLevel: 5,
        baseCost: {gold:20,wood:80,stone:0},
        upgradeCosts: [
            {gold:50,wood:150,stone:0},
            {gold:250,wood:350,stone:100},
            {gold:1000,wood:1700,stone:150},
            {gold:6200,wood:7300,stone:1450}
        ],
        income: [
            {stone:5},{stone:15},{stone:35},{stone:80},{stone:160}
        ]
    }
};

const COLLECTION_INTERVAL = 60 * 60 * 1000;
let currentTab = 'city';

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'м';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'к';
    return num.toString();
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.display = 'block';
    setTimeout(() => toast.style.display = 'none', 2000);
}

function showExactValue(resource) {
    const values = {
        gold: userData.gold,
        wood: userData.wood,
        stone: userData.stone,
        food: userData.food,
        population: `${userData.population_current}/${userData.population_max}`
    };
    const names = {gold:'Золото', wood:'Древесина', stone:'Камень', food:'Еда', population:'Население'};
    showToast(`${names[resource]}: ${values[resource]}`);
}

function updateAvatar() {
    const img = document.getElementById('avatarImg');
    const placeholder = document.getElementById('avatarPlaceholder');
    const avatar = AVATARS[userData.avatar];
    
    if (avatar && avatar.url) {
        img.src = avatar.url;
        img.style.display = 'block';
        placeholder.style.display = 'none';
    } else {
        placeholder.textContent = userData.game_login?.charAt(0).toUpperCase() || '👤';
        placeholder.style.display = 'block';
        img.style.display = 'none';
    }
}

function updateUserInfo() {
    let name = userData.game_login || 'Игрок';
    if (name.length > 12) name = name.substring(0,12);
    document.getElementById('userName').textContent = name;
    document.getElementById('userLogin').textContent = '@' + (userData.username || 'username');
    document.getElementById('levelBadge').textContent = userData.level;
    document.getElementById('userTelegramId').textContent = userData.id || '—';
    updateAvatar();
}

function getBuildingLevel(id) {
    return buildings.find(b => b.id === id)?.level || 0;
}

function calculateHourlyIncome() {
    let income = {
        gold: TOWN_HALL_INCOME[userData.level] || 0,
        wood: 0, food: 0, stone: 0, populationGrowth: 0
    };
    
    buildings.forEach(b => {
        const config = BUILDINGS_CONFIG[b.id];
        if (!config?.income) return;
        const inc = config.income[b.level - 1];
        if (inc) {
            income.gold += inc.gold || 0;
            income.wood += inc.wood || 0;
            income.food += inc.food || 0;
            income.stone += inc.stone || 0;
            income.populationGrowth += inc.populationGrowth || 0;
        }
    });
    
    return income;
}

function updateResourcesDisplay() {
    const income = calculateHourlyIncome();
    
    document.getElementById('goldDisplay').textContent = formatNumber(userData.gold);
    document.getElementById('goldIncome').textContent = `+${formatNumber(income.gold)}/ч`;
    
    document.getElementById('woodDisplay').textContent = formatNumber(userData.wood);
    document.getElementById('woodIncome').textContent = `+${formatNumber(income.wood)}/ч`;
    
    document.getElementById('stoneDisplay').textContent = formatNumber(userData.stone);
    document.getElementById('stoneIncome').textContent = `+${formatNumber(income.stone)}/ч`;
    
    const foodProd = income.food;
    const foodCons = userData.population_current;
    const foodBal = foodProd - foodCons;
    
    document.getElementById('foodDisplay').textContent = formatNumber(userData.food);
    document.getElementById('foodIncome').textContent = 
        foodBal > 0 ? `+${formatNumber(foodBal)}/ч` : foodBal < 0 ? `${formatNumber(foodBal)}/ч` : '0/ч';
    document.getElementById('foodIncome').className = foodBal < 0 ? 'resource-income-negative' : 'resource-income';
    
    document.getElementById('populationDisplay').textContent = 
        `${userData.population_current}/${userData.population_max}`;
    
    const canGrow = userData.food > 0 || foodProd >= foodCons;
    const totalGrowth = canGrow ? 3 + income.populationGrowth : 0;
    document.getElementById('populationGrowth').textContent = totalGrowth > 0 ? `+${totalGrowth}/ч` : '⚠️';
}

function updateTownHallDisplay() {
    const income = TOWN_HALL_INCOME[userData.level] || 0;
    document.getElementById('townHallIncome').textContent = `+${income} 🪙/ч`;
    document.getElementById('townHallLevel').textContent = userData.level;
    document.getElementById('townHallLevelBadge').textContent = userData.level;
    
    if (userData.level < 5) {
        const cost = TOWN_HALL_UPGRADE_COST[userData.level + 1];
        document.getElementById('townHallNext').innerHTML = 
            `⬆️ Улучшить (🪙${cost.gold} 🪵${cost.wood}${cost.stone ? ` ⛰️${cost.stone}` : ''})`;
    } else {
        document.getElementById('townHallNext').textContent = '🏆 Макс. уровень';
    }
}

function updateTimer() {
    const now = Date.now();
    const timePassed = now - userData.lastCollection;
    const timeLeft = Math.max(0, COLLECTION_INTERVAL - timePassed);
    
    if (timeLeft <= 0) {
        document.getElementById('timerDisplay').textContent = 'Готово!';
        document.getElementById('timerProgress').style.width = '100%';
    } else {
        const minutes = Math.floor(timeLeft / 60000);
        const seconds = Math.floor((timeLeft % 60000) / 1000);
        document.getElementById('timerDisplay').textContent = 
            `${minutes.toString().padStart(2,'0')}:${seconds.toString().padStart(2,'0')}`;
        document.getElementById('timerProgress').style.width = 
            `${(COLLECTION_INTERVAL - timeLeft) / COLLECTION_INTERVAL * 100}%`;
    }
}

async function checkAutoCollection() {
    if (Date.now() - userData.lastCollection >= COLLECTION_INTERVAL) {
        await performAction('collect', {});
    }
}

function canUpgrade(buildingId, currentLevel) {
    if (buildingId === 'townhall') {
        if (userData.level >= 5) return false;
        const cost = TOWN_HALL_UPGRADE_COST[userData.level + 1];
        return userData.gold >= cost.gold && userData.wood >= cost.wood && userData.stone >= cost.stone;
    }
    
    const config = BUILDINGS_CONFIG[buildingId];
    if (!config) return false;
    
    if (currentLevel === 0) {
        const cost = config.baseCost;
        return userData.level >= (config.requiredTownHall?.[0] || 1) &&
               userData.gold >= cost.gold && userData.wood >= cost.wood && userData.stone >= cost.stone;
    }
    
    if (currentLevel >= config.maxLevel) return false;
    if (userData.level < (config.requiredTownHall?.[currentLevel] || currentLevel + 1)) return false;
    
    const cost = config.upgradeCosts[currentLevel - 1];
    return userData.gold >= cost.gold && userData.wood >= cost.wood && userData.stone >= cost.stone;
}

function generateBuildingCardHTML(id) {
    const config = BUILDINGS_CONFIG[id];
    if (!config) return '';
    
    const level = getBuildingLevel(id);
    let statusClass = '', statusBadge = '', bonusText = '';
    
    if (id === 'house' && level > 0) {
        const total = config.populationBonus.slice(0, level).reduce((a,b) => a + b, 0);
        bonusText = `<div class="building-income">👥 +${total} лимит</div>`;
    }
    
    if (level === 0) {
        if (userData.level < (config.requiredTownHall?.[0] || 1)) {
            statusClass = 'locked';
            statusBadge = `<span class="building-status locked">🔒 Требуется ратуша ${config.requiredTownHall[0]}</span>`;
        } else {
            statusClass = 'unavailable';
            statusBadge = '<span class="building-status">🚫 Не построено</span>';
        }
    } else {
        statusClass = 'available';
        statusBadge = `<span class="building-status built">🏗️ Ур. ${level}</span>`;
    }
    
    const current = config.income?.[level - 1] || {};
    let incomeText = '';
    if (level > 0 && Object.keys(current).length) {
        const parts = [];
        if (current.gold) parts.push(`🪙+${current.gold}`);
        if (current.wood) parts.push(`🪵+${current.wood}`);
        if (current.stone) parts.push(`⛰️+${current.stone}`);
        if (current.food) parts.push(current.food > 0 ? `🌾+${current.food}` : `🌾${current.food}`);
        if (current.populationGrowth) parts.push(`👥+${current.populationGrowth}`);
        incomeText = `<div class="building-income">📊 Доход: ${parts.join(' ')}/ч</div>`;
    }
    
    let upgradeBtn = '';
    if (level > 0 && level < config.maxLevel && canUpgrade(id, level)) {
        const cost = config.upgradeCosts[level - 1];
        upgradeBtn = `<button class="building-upgrade-btn" onclick="upgradeBuilding('${id}')">Улучшить до Ур.${level+1} (🪙${cost.gold} 🪵${cost.wood}${cost.stone ? ` ⛰️${cost.stone}` : ''})</button>`;
    } else if (level === 0 && canUpgrade(id, 0)) {
        const cost = config.baseCost;
        upgradeBtn = `<button class="building-upgrade-btn" onclick="buildBuilding('${id}')">Построить (🪙${cost.gold} 🪵${cost.wood}${cost.stone ? ` ⛰️${cost.stone}` : ''})</button>`;
    }
    
    return `
        <div class="building-card ${statusClass}">
            <div class="building-icon">${config.icon}</div>
            <div class="building-info">
                <div class="building-header">
                    <span class="building-name">${config.name}</span>
                    ${statusBadge}
                </div>
                ${bonusText}
                ${incomeText}
                ${upgradeBtn}
            </div>
        </div>
    `;
}

function updateCityUI() {
    updateResourcesDisplay();
    updateTownHallDisplay();
    
    document.getElementById('socialBuildings').innerHTML = 
        generateBuildingCardHTML('house') + 
        generateBuildingCardHTML('tavern') + 
        generateBuildingCardHTML('bath');
    
    document.getElementById('economicBuildings').innerHTML = 
        generateBuildingCardHTML('farm') + 
        generateBuildingCardHTML('lumber') + 
        generateBuildingCardHTML('quarry');
}

function updateSettingsUI() {
    const section = document.getElementById('avatarSection');
    if (!section) return;
    
    section.innerHTML = `
        <h4>🖼️ Аватар</h4>
        <div style="display: flex; align-items: center; gap: 15px;">
            <img src="${AVATARS[userData.avatar].url}" style="width:60px; height:60px; border-radius:50%; border:3px solid #667eea;">
            <div>
                <div style="font-weight:bold;">${AVATARS[userData.avatar].name}</div>
                <button class="building-upgrade-btn" onclick="openAvatarSelector()">Сменить аватар</button>
            </div>
        </div>
    `;
}

function openAvatarSelector() {
    const overlay = document.createElement('div');
    overlay.className = 'avatar-selector-overlay';
    overlay.innerHTML = `
        <div class="avatar-selector">
            <h3>Выберите аватар</h3>
            <div class="avatar-grid" id="selectorAvatarGrid"></div>
            <button class="building-upgrade-btn" onclick="this.remove()">Закрыть</button>
        </div>
    `;
    
    const grid = overlay.querySelector('#selectorAvatarGrid');
    Object.keys(AVATARS).forEach(key => {
        const a = AVATARS[key];
        const owned = userData.owned_avatars.includes(key);
        const selected = userData.avatar === key;
        
        const div = document.createElement('div');
        div.className = `avatar-option ${selected ? 'selected' : ''}`;
        div.innerHTML = `
            <img src="${a.url}" class="avatar-option-img">
            <div class="avatar-option-name">${a.name}</div>
            ${!owned ? `<div class="avatar-option-price">${a.price} 🪙</div>` : ''}
            <button class="building-upgrade-btn" onclick="${owned ? `selectAvatar('${key}')` : `buyAvatar('${key}')`}">
                ${owned ? (selected ? 'Выбран' : 'Выбрать') : 'Купить'}
            </button>
        `;
        grid.appendChild(div);
    });
    
    document.body.appendChild(overlay);
}

async function buyAvatar(key) {
    const a = AVATARS[key];
    if (!a) return;
    if (userData.gold < a.price) {
        showToast('❌ Не хватает монет');
        return;
    }
    await performAction('buy_avatar', { avatar: key, price: a.price });
}

async function selectAvatar(key) {
    if (!userData.owned_avatars.includes(key)) {
        showToast('❌ Сначала купите этот аватар');
        return;
    }
    await performAction('select_avatar', { avatar: key });
}

async function upgradeTownHall() {
    if (userData.level >= 5) {
        showToast('🏛️ Максимальный уровень');
        return;
    }
    if (!canUpgrade('townhall', userData.level)) {
        showToast('❌ Не хватает ресурсов');
        return;
    }
    await performAction('upgrade_level', {});
}

async function buildBuilding(id) {
    if (buildings.find(b => b.id === id)) {
        showToast('❌ Здание уже построено');
        return;
    }
    await performAction('build', { building_id: id });
}

async function upgradeBuilding(id) {
    const b = buildings.find(b => b.id === id);
    if (!b) {
        await buildBuilding(id);
        return;
    }
    if (!canUpgrade(id, b.level)) {
        showToast('❌ Не хватает ресурсов');
        return;
    }
    await performAction('upgrade', { building_id: id });
}

async function performAction(action, data) {
    try {
        const res = await fetch(`${API_URL}/api/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initData: tg.initData, action, data })
        });
        const result = await res.json();
        
        if (result.success && result.state) {
            Object.assign(userData, result.state);
            if (result.state.buildings) buildings = result.state.buildings;
            if (result.state.game_login) updateUserInfo();
            if (result.state.avatar) updateAvatar();
            updateCityUI();
            updateSettingsUI();
            
            const messages = {
                build: '✅ Построено!',
                upgrade: '✅ Улучшено!',
                upgrade_level: '🏛️ Ратуша улучшена!',
                buy_avatar: '✅ Аватар куплен!',
                select_avatar: '✅ Аватар выбран!',
                change_name_paid: '✅ Имя изменено!'
            };
            if (messages[action]) showToast(messages[action]);
            return true;
        }
        showToast(`❌ ${result.error || 'Ошибка'}`);
        return false;
    } catch {
        showToast('❌ Ошибка соединения');
        return false;
    }
}

async function login() {
    try {
        const res = await fetch(`${API_URL}/api/auth`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initData: tg.initData })
        });
        const data = await res.json();
        
        if (data.success) {
            Object.assign(userData, data.user);
            buildings = data.buildings || buildings;
            updateUserInfo();
            updateCityUI();
            
            // КЛЮЧЕВОЕ МЕСТО - проверка на показ окна регистрации
            if (!userData.game_login || userData.game_login === '' || userData.game_login === 'EMPTY') {
                document.getElementById('loginOverlay').style.display = 'flex';
            } else {
                document.getElementById('loginOverlay').style.display = 'none';
            }
        }
    } catch {
        showToast('⚠️ Ошибка загрузки');
    }
}

async function saveGameLogin() {
    const input = document.getElementById('newLogin');
    let name = input.value.trim();
    if (!name) {
        showToast('❌ Введите имя');
        return;
    }
    if (name.length > 12) name = name.substring(0,12);
    
    if (await performAction('set_login', { game_login: name })) {
        document.getElementById('loginOverlay').style.display = 'none';
        showToast(`✅ Добро пожаловать, ${name}!`);
    }
}

async function changeNamePaid() {
    const input = document.getElementById('newNameInput');
    let name = input.value.trim();
    if (!name) {
        showToast('❌ Введите имя');
        return;
    }
    if (name.length > 12) name = name.substring(0,12);
    if (userData.gold < 5000) {
        showToast('❌ Не хватает монет');
        return;
    }
    await performAction('change_name_paid', { game_login: name });
}

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab').forEach(t => 
        t.classList.toggle('active', t.dataset.tab === tab));
    document.querySelectorAll('.tab-pane').forEach(p => 
        p.classList.toggle('hidden', !p.id.includes(tab.charAt(0).toUpperCase() + tab.slice(1))));
    
    if (tab === 'settings') updateSettingsUI();
}

async function createClan() { showToast('🚧 В разработке'); }

async function showTopClans() {
    try {
        const res = await fetch(`${API_URL}/api/clans/top`);
        const data = await res.json();
        let html = '<h4>🏆 Топ игроков</h4>';
        if (!data.players?.length) {
            html += '<p>Пока нет игроков</p>';
        } else {
            data.players.forEach((p,i) => {
                html += `<div><b>${i+1}.</b> ${p.game_login || 'Без имени'} 🪙${p.gold}</div>`;
            });
        }
        document.getElementById('topClans').innerHTML = html;
    } catch {
        showToast('❌ Ошибка');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    login();
    document.querySelectorAll('.tab').forEach(t => 
        t.addEventListener('click', () => switchTab(t.dataset.tab)));
    document.getElementById('createClanBtn')?.addEventListener('click', createClan);
    document.getElementById('topClansBtn')?.addEventListener('click', showTopClans);
    document.getElementById('confirmLogin')?.addEventListener('click', saveGameLogin);
    document.getElementById('changeNameWithPriceBtn')?.addEventListener('click', changeNamePaid);
    
    setInterval(() => {
        updateTimer();
        checkAutoCollection();
    }, 1000);
    
    switchTab('city');
});
