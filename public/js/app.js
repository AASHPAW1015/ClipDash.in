// DOM Elements
const connectForm = document.getElementById('connectForm');
const connectBtn = document.getElementById('connectBtn');
const successState = document.getElementById('successState');
const nightbotCommand = document.getElementById('nightbotCommand');
const copyBtn = document.getElementById('copyBtn');
const resetBtn = document.getElementById('resetBtn');

// Modal Elements
const modal = document.getElementById('instructionsModal');
const openBtn = document.getElementById('openInstructionsBtn');
const closeBtn = document.querySelector('.close-btn');

// --- Helper Functions ---

/**
 * Extracts Channel ID from a full YouTube URL or returns the ID if provided directly.
 */
function extractChannelId(input) {
    if (!input) return null;
    // Regex for UC channel ID (e.g. UCxxxxxxxxxxxxxxxxxxxx)
    const match = input.match(/(UC[\w-]{22})/);
    return match ? match[1] : input;
}

/**
 * Validate standard Discord Webhook URL structure
 */
function isValidWebhook(url) {
    return url.includes('discord.com/api/webhooks/');
}

// --- Logic ---

connectForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // UI Loading State
    const originalBtnText = connectBtn.innerHTML;
    connectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
    connectBtn.disabled = true;

    try {
        const email = document.getElementById('emailInput').value;
        const channelInput = document.getElementById('channelUrl').value;
        const webhookUrl = document.getElementById('webhookUrl').value;

        // Validation
        const channelId = extractChannelId(channelInput);
        if (!channelId || !channelId.startsWith('UC')) {
            throw new Error('Invalid YouTube Channel ID. It must start with "UC".');
        }

        if (!isValidWebhook(webhookUrl)) {
            throw new Error('Invalid Discord Webhook URL.');
        }

        // API Call
        const response = await fetch('/webhook/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                youtubeChannelUrl: `https://www.youtube.com/channel/${channelId}`,
                discordWebhookUrl: webhookUrl
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Connection failed.');
        }

        // Success!
        showSuccess(channelId);

    } catch (error) {
        alert(error.message);
    } finally {
        // Reset Button
        connectBtn.innerHTML = originalBtnText;
        connectBtn.disabled = false;
    }
});

function showSuccess(channelId) {
    // Hide form, show success
    connectForm.style.display = 'none';
    successState.classList.remove('hidden');

    // Construct Command
    // We use the same URL structure as before
    const command = `$(urlfetch https://clipdash.in/webhook/clip?channel_id=${channelId}&user=$(user)&message=$(querystring))`;
    nightbotCommand.textContent = command;
}

resetBtn.addEventListener('click', () => {
    connectForm.reset();
    connectForm.style.display = 'block';
    successState.classList.add('hidden');
});

// Clipboard
copyBtn.addEventListener('click', () => {
    const text = nightbotCommand.textContent;
    navigator.clipboard.writeText(text).then(() => {
        const originalIcon = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(() => {
            copyBtn.innerHTML = originalIcon;
        }, 2000);
    });
});

// --- Modal Logic ---

openBtn.addEventListener('click', () => {
    modal.style.display = 'block';
});

closeBtn.addEventListener('click', () => {
    modal.style.display = 'none';
});

// Close if clicked outside
window.addEventListener('click', (e) => {
    if (e.target == modal) {
        modal.style.display = 'none';
    }
});

// --- Parallax Effect (Optimized) ---
let lastScrollY = window.scrollY;
let ticking = false;

function updateParallax() {
    const scrollY = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrollPercent = scrollY / docHeight;

    const layerBack = document.querySelector('.layer-back');
    const layerFront = document.querySelector('.layer-front');
    const container = document.querySelector('.parallax-container');

    // 1. Smooth Movement
    if (layerBack) {
        // Back moves slower
        layerBack.style.transform = `translate3d(0, ${scrollY * 0.3}px, 0)`;
    }

    if (layerFront) {
        // Front moves faster
        layerFront.style.transform = `translate3d(0, -${scrollY * 0.2}px, 0)`;
    }

    // 2. Wrap scroll % logic (Fade after 67%)
    if (container) {
        if (scrollPercent > 0.67) {
            // Calculate fade: 1.0 at 0.67 -> 0.2 at 1.0
            const opacity = 1 - ((scrollPercent - 0.67) * 3);
            container.style.opacity = Math.max(0, opacity);
        } else {
            container.style.opacity = 1;
        }
    }

    ticking = false;
}

document.addEventListener('scroll', () => {
    lastScrollY = window.scrollY;
    if (!ticking) {
        window.requestAnimationFrame(updateParallax);
        ticking = true;
    }
});
