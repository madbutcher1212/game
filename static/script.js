const API_URL = 'https://game-production-10ea.up.railway.app';

const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const AVATARS = {
    'male_free': {
        name: 'Мужской',
        url: 'https://raw.githubusercontent.com/madbutcher1212/game/main/static/avatars/male_free.png',
        price: 0,
        category: 'free'
    },
    'female_free': {
        name: 'Женский',
        url: 'https://raw.githubusercontent.com/madbutcher1212/game/main/static/avatars/female_free.png',
        price: 0,
        category: 'free'
    },
    'male_premium': {
        name: 'Лорд',
        url: 'https://raw.githubusercontent.com/madbutcher1212/game/main/static/avatars/male_premium.png',
        price: 25000,
        category: 'premium'
    },
    'female_premium': {
        name: 'Леди',
        url: 'https://raw.githubusercontent.com/madbutcher1212/game/main/static/avatars/female_premium.png',
        price: 25000,
        category: 'premium'
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
            {food:10},
            {food:25},
            {food:60},
            {food:120},
            {food:260}
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
            {wood:10},
            {wood:20},
            {wood:40},
            {wood:100},
            {wood:200}
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
            {stone:5},
            {stone:15},
            {stone:35},
            {stone:80},
            {stone:160}
        ]
    }
};

let currentTab = 'city';
const COLLECTION_INTERVAL = 60 * 60 * 1000;

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'м';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'к';
    }
    return num.toString();
}

function showExactValue(resource) {
    let value, name;
    switch(resource) {
        case 'gold':
            value = userData.gold;
            name = 'Золото';
            break;
        case 'wood':
            value = userData.wood;
            name = 'Древесина';
            break;
        case 'stone':
            value = userData.stone;
            name = 'Камень';
            break;
        case 'food':
            value = userData.food;
            name = 'Еда';
            break;
        case 'population':
            value = `${userData.population_current}/${userData.population_max}`;
            name = 'Население';
            showToast(`${name}: ${value}`);
            return;
    }
    showToast(`${name}: ${value}`);
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.display = 'block';
    setTimeout(() => toast.style.display = 'none', 2000);
}

function updateAvatar() {
    const avatarImg = document.getElementById('avatarImg');
    const avatarPlaceholder = document.getElementById('avatarPlaceholder');
    
    if (userData.avatar && AVATARS[userData.avatar] && AVATARS[userData.avatar].url) {
        avatarImg.src = AVATARS[userData.avatar].url;
        avatarImg.style.display = 'block';
        avatarPlaceholder.style.display = 'none';
    } else {
        const letter = userData.game_login ? userData.game_login.charAt(0).toUpperCase() : '👤';
        avatarPlaceholder.textContent = letter;
        avatarPlaceholder.style.display = 'block';
        avatarImg.style.display = 'none';
    }
}

function updateUserInfo() {
    let displayName = userData.game_login || 'Игрок';
    if (displayName.length > 12) displayName = displayName.substring(0,12);
    document.getElementById('userName').textContent = displayName;
    document.getElementById('userLogin').textContent = '@' + (userData.username || 'username');
    document.getElementById('levelBadge').textContent = userData.level;
    document.getElementById('userTelegramId').textContent = userData.id || '—';
    updateAvatar();
}

function getBuildingLevel(buildingId) {
    const b = buildings.find(b => b.id === buildingId);
    return b ? b.level : 0;
}

function getBuildingIncome(buildingId, level) {
    if (buildingId === 'townhall') return {gold: TOWN_HALL_INCOME[level] || 0};
    const config = BUILDINGS_CONFIG[buildingId];
    if (!config || level === 0 || !config.income) return {};
    return config.income[level-1] || {};
}

function getUpgradeCost(buildingId, currentLevel) {
    if (buildingId === 'townhall') {
        return TOWN_HALL_UPGRADE_COST[currentLevel+1] || {gold:0,wood:0,stone:0};
    }
    const config = BUILDINGS_CONFIG[buildingId];
    if (!config || currentLevel >= config.maxLevel) return {gold:0,wood:0,stone:0};
    return config.upgradeCosts[currentLevel-1];
}

function isTownHallLevelEnough(buildingId, targetLevel) {
    if (buildingId === 'townhall') return true;
    const config = BUILDINGS_CONFIG[buildingId];
    if (!config || !config.requiredTownHall) return true;
    return userData.level >= config.requiredTownHall[targetLevel - 1];
}

function calculateHourlyIncome() {
    let income = {
        gold: TOWN_HALL_INCOME[userData.level] || 0,
        wood: 0,
        food: 0,
        stone: 0,
        populationGrowth: 0
    };
    
    buildings.forEach(b => {
        const config = BUILDINGS_CONFIG[b.id];
        if (!config || !config.income) return;
        
        const levelIncome = config.income[b.level - 1];
        income.gold += levelIncome.gold || 0;
        income.wood += levelIncome.wood || 0;
        income.food += levelIncome.food || 0;
        income.stone += levelIncome.stone || 0;
        income.populationGrowth += levelIncome.populationGrowth || 0;
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
    
    const foodProduction = income.food;
    const foodConsumption = userData.population_current;
    const foodBalance = foodProduction - foodConsumption;
    
    document.getElementById('foodDisplay').textContent = formatNumber(userData.food);
    
    if (foodBalance > 0) {
        document.getElementById('foodIncome').textContent = `+${formatNumber(foodBalance)}/ч`;
        document.getElementById('foodIncome').className = 'resource-income';
    } else if (foodBalance < 0) {
        document.getElementById('foodIncome').textContent = `${formatNumber(foodBalance)}/ч`;
        document.getElementById('foodIncome').className = 'resource-income-negative';
    } else {
        document.getElementById('foodIncome').textContent = `0/ч`;
        document.getElementById('foodIncome').className = 'resource-income';
    }
    
    document.getElementById('populationDisplay').textContent = 
        `${userData.population_current}/${userData.population_max}`;
    
    const canGrow = userData.food > 0 || foodProduction >= foodConsumption;
    const totalGrowth = canGrow ? 3 + income.populationGrowth : 0;
    document.getElementById('populationGrowth').textContent = totalGrowth > 0 ? `+${totalGrowth}/ч` : '⚠️';
}

function updateTownHallDisplay() {
    const currentIncome = TOWN_HALL_INCOME[userData.level] || 0;
    document.getElementById('townHallIncome').textContent = `+${currentIncome} 🪙/ч`;
    document.getElementById('townHallLevel').textContent = userData.level;
    document.getElementById('townHallLevelBadge').textContent = userData.level;
    
    if (userData.level < 5) {
        const cost = getUpgradeCost('townhall', userData.level);
        document.getElementById('townHallNext').innerHTML = 
            `⬆️ Улучшить (🪙${cost.gold} 🪵${cost.wood}${cost.stone>0 ? ` ⛰️${cost.stone}`:''})`;
    } else {
        document.getElementById('townHallNext').textContent = '🏆 Макс. уровень';
    }
}

function openAvatarSelector() {
    const overlay = document.createElement('div');
    overlay.className = 'avatar-selector-overlay';
    overlay.innerHTML = `
        <div class="avatar-selector">
            <h3>Выберите аватар</h3>
            <div class="avatar-grid" id="selectorAvatarGrid"></div>
            <button class="building-upgrade-btn" onclick="this.closest('.avatar-selector-overlay').remove()">Закрыть</button>
        </div>
    `;
    
    const grid = overlay.querySelector('#selectorAvatarGrid');
    Object.keys(AVATARS).forEach(key => {
        const a = AVATARS[key];
        const isOwned = userData.owned_avatars.includes(key);
        const isSelected = userData.avatar === key;
        
        let buttonHtml = '';
        if (!isOwned) {
            buttonHtml = `<button class="building-upgrade-btn" onclick="buyAvatar('${key}')">Купить за ${a.price} 🪙</button>`;
        } else if (!isSelected) {
            buttonHtml = `<button class="building-upgrade-btn" onclick="selectAvatar('${key}')">Выбрать</button>`;
        } else {
            buttonHtml = `<button class="building-upgrade-btn" disabled style="background: #4CAF50;">Выбран</button>`;
        }
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = `avatar-option ${isSelected ? 'selected' : ''}`;
        avatarDiv.innerHTML = `
            <img src="${a.url}" class="avatar-option-img">
            <div class="avatar-option-name">${a.name}</div>
            ${!isOwned ? `<div class="avatar-option-price">${a.price} 🪙</div>` : ''}
            ${buttonHtml}
        `;
        grid.appendChild(avatarDiv);
    });
    
    document.body.appendChild(overlay);
}

async function buyAvatar(avatarKey) {
    const avatar = AVATARS[avatarKey];
    if (!avatar) return;
    
    if (userData.gold < avatar.price) {
        showToast('❌ Не хватает монет');
        return;
    }
    
    await performAction('buy_avatar', { avatar: avatarKey, price: avatar.price });
}

async function selectAvatar(avatarKey) {
    if (!userData.owned_avatars.includes(avatarKey)) {
        showToast('❌ Сначала купите этот аватар');
        return;
    }
    
    if (userData.avatar === avatarKey) {
        showToast('✅ Это уже ваш аватар');
        return;
    }
    
    await performAction('select_avatar', { avatar: avatarKey });
}

function updateSettingsUI() {
    const avatarSection = document.getElementById('avatarSection');
    if (avatarSection) {
        avatarSection.innerHTML = `
            <h4 style="margin-bottom: 10px;">🖼️ Аватар</h4>
            <div style="display: flex; align-items: center; gap: 15px;">
                <img src="${AVATARS[userData.avatar].url}" style="width: 60px; height: 60px; border-radius: 50%; border: 3px solid #667eea; object-fit: cover;">
                <div>
                    <div style="font-weight: bold;">${AVATARS[userData.avatar].name}</div>
                    <button class="building-upgrade-btn" onclick="openAvatarSelector()" style="margin-top: 5px;">Сменить аватар</button>
                </div>
            </div>
        `;
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
        const minutes = Math.floor(timeLeft/60000);
        const seconds = Math.floor((timeLeft%60000)/1000);
        document.getElementById('timerDisplay').textContent = 
            `${minutes.toString().padStart(2,'0')}:${seconds.toString().padStart(2,'0')}`;
        const progress = ((COLLECTION_INTERVAL-timeLeft)/COLLECTION_INTERVAL)*100;
        document.getElementById('timerProgress').style.width = `${progress}%`;
    }
}

async function checkAutoCollection() {
    const now = Date.now();
    if (now - userData.lastCollection >= COLLECTION_INTERVAL) {
        await performAction('collect', {});
    }
}

function canUpgrade(buildingId, currentLevel) {
    if (buildingId === 'townhall') {
        if (userData.level >= 5) return false;
        const cost = getUpgradeCost(buildingId, currentLevel);
        return userData.gold >= cost.gold && userData.wood >= cost.wood && userData.stone >= cost.stone;
    }
    
    const config = BUILDINGS_CONFIG[buildingId];
    if (!config) return false;
    
    if (currentLevel === 0) {
        const cost = config.baseCost;
        return isTownHallLevelEnough(buildingId, 1) && 
               userData.gold >= cost.gold && 
               userData.wood >= cost.wood && 
               userData.stone >= cost.stone;
    }
    
    if (currentLevel >= config.maxLevel) return false;
    if (!isTownHallLevelEnough(buildingId, currentLevel + 1)) return false;
    
    const cost = getUpgradeCost(buildingId, currentLevel);
    return userData.gold >= cost.gold && 
           userData.wood >= cost.wood && 
           userData.stone >= cost.stone;
}

function generateBuildingCardHTML(buildingId) {
    const config = BUILDINGS_CONFIG[buildingId];
    if (!config) return '';
    
    const level = getBuildingLevel(buildingId);
    
    let statusClass = '';
    let statusBadge = '';
    let bonusText = '';
    
    if (buildingId === 'house' && level > 0) {
        const totalBonus = config.populationBonus.slice(0, level).reduce((a,b)=>a+b,0);
        bonusText = `<div class="building-income">👥 +${totalBonus} лимит</div>`;
    }
    
    if (level === 0) {
        if (!isTownHallLevelEnough(buildingId, 1)) {
            statusClass = 'locked';
            const reqLevel = config.requiredTownHall ? config.requiredTownHall[0] : 1;
            statusBadge = `<span class="building-status locked">🔒 Требуется ратуша ${reqLevel}</span>`;
        } else {
            statusClass = 'unavailable';
            statusBadge = '<span class="building-status">🚫 Не построено</span>';
        }
    } else {
        statusClass = 'available';
        statusBadge = `<span class="building-status built">🏗️ Ур. ${level}</span>`;
    }
    
    const currentIncome = getBuildingIncome(buildingId, level);
    let incomeText = '';
    if (level > 0 && Object.keys(currentIncome).length > 0) {
        let parts = [];
        if (currentIncome.gold) parts.push(`🪙+${currentIncome.gold}`);
        if (currentIncome.wood) parts.push(`🪵+${currentIncome.wood}`);
        if (currentIncome.stone) parts.push(`⛰️+${currentIncome.stone}`);
        if (currentIncome.food) {
            if (currentIncome.food > 0) parts.push(`🌾+${currentIncome.food}`);
            else if (currentIncome.food < 0) parts.push(`🌾${currentIncome.food}`);
        }
        if (currentIncome.populationGrowth) parts.push(`👥+${currentIncome.populationGrowth}`);
        if (parts.length > 0) {
            incomeText = `<div class="building-income">📊 Доход: ${parts.join(' ')}/ч</div>`;
        }
    }
    
    let nextIncomeText = '';
    let upgradeBtn = '';
    
    if (level > 0 && level < config.maxLevel) {
        const nextIncome = config.income[level];
        const cost = getUpgradeCost(buildingId, level);
        const canUpgradeNow = canUpgrade(buildingId, level);
        
        let parts = [];
        if (nextIncome.gold) parts.push(`🪙+${nextIncome.gold}`);
        if (nextIncome.wood) parts.push(`🪵+${nextIncome.wood}`);
        if (nextIncome.stone) parts.push(`⛰️+${nextIncome.stone}`);
        if (nextIncome.food) {
            if (nextIncome.food > 0) parts.push(`🌾+${nextIncome.food}`);
            else if (nextIncome.food < 0) parts.push(`🌾${nextIncome.food}`);
        }
        if (nextIncome.populationGrowth) parts.push(`👥+${nextIncome.populationGrowth}`);
        
        if (parts.length > 0) {
            nextIncomeText = `<div class="building-next-income">📈 Ур.${level+1}: ${parts.join(' ')}/ч</div>`;
        }
        
        let reqText = '';
        if (!isTownHallLevelEnough(buildingId, level + 1)) {
            const reqLevel = config.requiredTownHall ? config.requiredTownHall[level] : level + 1;
            reqText = ` (треб. ратуша ${reqLevel})`;
        }
        
        let btnClass = canUpgradeNow ? 'building-upgrade-btn available' : 'building-upgrade-btn unavailable';
        
        upgradeBtn = `
            <button class="${btnClass}" onclick="upgradeBuilding('${buildingId}')" 
                    ${!canUpgradeNow ? 'disabled' : ''}>
                Улучшить до Ур.${level+1}${reqText} (🪙${cost.gold} 🪵${cost.wood}${cost.stone>0?` ⛰️${cost.stone}`:''})
            </button>
        `;
    } else if (level === 0 && isTownHallLevelEnough(buildingId, 1)) {
        const cost = config.baseCost;
        const canBuildNow = userData.gold >= cost.gold && 
                           userData.wood >= cost.wood && 
                           userData.stone >= cost.stone;
        
        let btnClass = canBuildNow ? 'building-upgrade-btn available' : 'building-upgrade-btn unavailable';
        
        upgradeBtn = `
            <button class="${btnClass}" onclick="buildBuilding('${buildingId}')" 
                    ${!canBuildNow ? 'disabled' : ''}>
                Построить (🪙${cost.gold} 🪵${cost.wood}${cost.stone>0?` ⛰️${cost.stone}`:''})
            </button>
        `;
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
                ${nextIncomeText}
                ${upgradeBtn}
            </div>
        </div>
    `;
}

function updateCityUI() {
    updateResourcesDisplay();
    updateTownHallDisplay();
    
    let socialHtml = '';
    socialHtml += generateBuildingCardHTML('house');
    socialHtml += generateBuildingCardHTML('tavern');
    socialHtml += generateBuildingCardHTML('bath');
    document.getElementById('socialBuildings').innerHTML = socialHtml;
    
    let economicHtml = '';
    economicHtml += generateBuildingCardHTML('farm');
    economicHtml += generateBuildingCardHTML('lumber');
    economicHtml += generateBuildingCardHTML('quarry');
    document.getElementById('economicBuildings').innerHTML = economicHtml;
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

async function buildBuilding(buildingId) {
    const existing = buildings.find(b => b.id === buildingId);
    if (existing) {
        showToast('❌ Здание уже построено');
        return;
    }
    const config = BUILDINGS_CONFIG[buildingId];
    if (!config) return;
    if (userData.gold < config.baseCost.gold || 
        userData.wood < config.baseCost.wood || 
        userData.stone < config.baseCost.stone) {
        showToast('❌ Не хватает ресурсов');
        return;
    }
    await performAction('build', {building_id: buildingId});
}

async function upgradeBuilding(buildingId) {
    const building = buildings.find(b => b.id === buildingId);
    if (!building) {
        await buildBuilding(buildingId);
        return;
    }
    if (!canUpgrade(buildingId, building.level)) {
        showToast('❌ Не хватает ресурсов или требуется выше уровень');
        return;
    }
    await performAction('upgrade', {building_id: buildingId});
}

async function performAction(action, data = {}) {
    try {
        const response = await fetch(`${API_URL}/api/action`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({initData: tg.initData, action, data})
        });
        const result = await response.json();
        
        if (result.success) {
            if (result.state) {
                if (result.state.gold !== undefined) userData.gold = result.state.gold;
                if (result.state.wood !== undefined) userData.wood = result.state.wood;
                if (result.state.food !== undefined) userData.food = result.state.food;
                if (result.state.stone !== undefined) userData.stone = result.state.stone;
                if (result.state.level !== undefined) userData.level = result.state.level;
                if (result.state.population_current !== undefined) userData.population_current = result.state.population_current;
                if (result.state.population_max !== undefined) userData.population_max = result.state.population_max;
                if (result.state.lastCollection !== undefined) userData.lastCollection = result.state.lastCollection;
                if (result.state.game_login !== undefined) {
                    userData.game_login = result.state.game_login;
                    updateUserInfo();
                }
                if (result.state.avatar !== undefined) {
                    userData.avatar = result.state.avatar;
                    updateAvatar();
                    updateSettingsUI();
                }
                if (result.state.owned_avatars !== undefined) {
                    userData.owned_avatars = result.state.owned_avatars;
                }
                if (result.state.buildings) buildings = result.state.buildings;
                updateCityUI();
                updateSettingsUI();
                
                if (action === 'build') showToast('✅ Построено!');
                if (action === 'upgrade') showToast('✅ Улучшено!');
                if (action === 'upgrade_level') showToast('🏛️ Ратуша улучшена!');
                if (action === 'buy_avatar') {
                    showToast('✅ Аватар куплен!');
                }
                if (action === 'select_avatar') showToast('✅ Аватар выбран!');
                if (action === 'change_name_paid') showToast('✅ Имя изменено!');
            }
            return true;
        } else {
            showToast(`❌ ${result.error || 'Ошибка'}`);
            return false;
        }
    } catch (error) {
        showToast('❌ Ошибка соединения');
        return false;
    }
}

async function login() {
    try {
        const response = await fetch(`${API_URL}/api/auth`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({initData: tg.initData})
        });
        const data = await response.json();
        
        if (data.success) {
            userData.id = data.user.id;
            userData.username = data.user.username;
            userData.game_login = data.user.game_login || '';
            userData.avatar = data.user.avatar || 'male_free';
            userData.owned_avatars = data.user.owned_avatars || ['male_free', 'female_free'];
            userData.gold = data.user.gold;
            userData.wood = data.user.wood;
            userData.food = data.user.food;
            userData.stone = data.user.stone;
            userData.level = data.user.level;
            userData.population_current = data.user.population_current || 10;
            userData.population_max = data.user.population_max || 20;
            userData.lastCollection = data.user.lastCollection || Date.now();
            
            buildings = data.buildings || [
                {id:'house', level:1},
                {id:'farm', level:1},
                {id:'lumber', level:1}
            ];
            
            updateUserInfo();
            updateCityUI();
            
            if (!userData.game_login || userData.game_login === '') {
                document.getElementById('loginOverlay').style.display = 'flex';
            } else {
                document.getElementById('loginOverlay').style.display = 'none';
            }
        }
    } catch (error) {
        showToast('⚠️ Ошибка загрузки');
    }
}

async function saveGameLogin() {
    const loginInput = document.getElementById('newLogin');
    let newLogin = loginInput.value.trim();
    if (!newLogin) {
        showToast('❌ Введите имя');
        return;
    }
    if (newLogin.length > 12) newLogin = newLogin.substring(0,12);
    const success = await performAction('set_login', {game_login: newLogin});
    if (success) {
        document.getElementById('loginOverlay').style.display = 'none';
        showToast(`✅ Добро пожаловать, ${newLogin}!`);
    }
}

async function changeNamePaid() {
    const nameInput = document.getElementById('newNameInput');
    let newName = nameInput.value.trim();
    
    if (!newName) {
        showToast('❌ Введите имя');
        return;
    }
    
    if (newName.length > 12) {
        newName = newName.substring(0, 12);
    }
    
    if (userData.gold < 5000) {
        showToast('❌ Не хватает монет');
        return;
    }
    
    await performAction('change_name_paid', { game_login: newName });
}

function switchTab(tabId) {
    currentTab = tabId;
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabId);
    });
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.add('hidden');
    });
    document.getElementById(`tab${tabId.charAt(0).toUpperCase()+tabId.slice(1)}`).classList.remove('hidden');
    
    if (tabId === 'settings') {
        updateSettingsUI();
    }
}

async function createClan() { showToast('🚧 В разработке'); }

async function showTopClans() {
    try {
        const response = await fetch(`${API_URL}/api/clans/top`);
        const data = await response.json();
        let html = '<h4 style="margin-bottom:10px;">🏆 Топ игроков</h4>';
        if (!data.players || data.players.length === 0) {
            html += '<p style="color:#666;">Пока нет игроков</p>';
        } else {
            data.players.forEach((p,i) => {
                html += `<div style="padding:8px; margin:5px 0; background:white; border-radius:8px; display:flex; justify-content:space-between;">
                    <span><b>${i+1}.</b> ${p.game_login || 'Без имени'}</span>
                    <span>🪙${p.gold}</span>
                </div>`;
            });
        }
        document.getElementById('topClans').innerHTML = html;
    } catch { showToast('❌ Ошибка'); }
}

document.addEventListener('DOMContentLoaded', () => {
    login();
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    document.getElementById('createClanBtn').addEventListener('click', createClan);
    document.getElementById('topClansBtn').addEventListener('click', showTopClans);
    document.getElementById('confirmLogin').addEventListener('click', saveGameLogin);
    document.getElementById('changeNameWithPriceBtn').addEventListener('click', changeNamePaid);
    setInterval(() => { updateTimer(); checkAutoCollection(); }, 1000);
    switchTab('city');
});
