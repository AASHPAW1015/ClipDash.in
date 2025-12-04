# ClipStream Bot - The Master Guide

This is the "Bible" for the ClipStream Bot. It contains everything you need to install, run, fix, and use the bot.

---

## 📚 Table of Contents
1.  [Server Installation (From Zero to Hero)](#part-1-server-installation)
2.  [Troubleshooting & Fixes](#part-2-troubleshooting)
3.  [User Guide (For Streamers)](#part-3-user-guide)

---

## PART 1: SERVER INSTALLATION
*(Adapted from Ultimate Home Server Guide)*

### 1. Physical Prep (The USB)
1.  Download **Ubuntu 24.04 LTS** from ubuntu.com.
2.  Download **BalenaEtcher**.
3.  Flash the Ubuntu ISO to your USB drive.

### 2. Installing the OS
1.  Plug USB into Server PC.
2.  Boot from USB (Spam F2/F12/Del).
3.  Install Ubuntu (Erase disk, create user "server").
4.  Remove USB and reboot.

### 3. Setting up the Environment
Open Terminal on the Server and run:
```bash
# 1. Update System
sudo apt update && sudo apt upgrade -y

# 2. Install Tools
sudo apt install python3-pip python3-venv git nginx -y
```

### 4. Cloning the Code
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/clipstream-bot.git
cd clipstream-bot
```

### 5. Installing the Bot
**Crucial:** You must create a NEW virtual environment on the server. The one from Mac won't work.
```bash
# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn uvloop httptools
```

### 6. Secrets Setup
You need to recreate your secrets file on the server.
```bash
nano .env
# Paste your .env content (API Keys, etc.)
# Save with Ctrl+X -> Y -> Enter
```
*Also upload your `firebase_credentials.json` if it's not in the repo.*

### 7. Cloudflare Tunnel (Public Access)
```bash
# 1. Install Cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && sudo dpkg -i cloudflared.deb

# 2. Login
cloudflared tunnel login

# 3. Create Tunnel
cloudflared tunnel create clip-server

# 4. Route DNS
cloudflared tunnel route dns clip-server clipdash.in
cloudflared tunnel route dns clip-server www.clipdash.in

# 5. Run it
cloudflared tunnel run --url http://localhost:8000 clip-server
```

### 8. SSH Access (Remote Management)
To manage your server from anywhere without a VPN:

**On the Server:**
1.  Create `~/.cloudflared/config.yml`:
    ```yaml
    tunnel: YOUR_TUNNEL_ID
    credentials-file: /home/clipdash/.cloudflared/YOUR_TUNNEL_ID.json
    ingress:
      - hostname: ssh.clipdash.in
        service: ssh://127.0.0.1:22
      - hostname: clipdash.in
        service: http://127.0.0.1:8000
      - hostname: www.clipdash.in
        service: http://127.0.0.1:8000
      - service: http_status:404
    ```
2.  Run with config: `cloudflared tunnel run clip-final`

**On your Laptop (Client):**
1.  Edit `~/.ssh/config`:
    ```text
    Host ssh.clipdash.in
        User clipdash
        ProxyCommand /opt/homebrew/bin/cloudflared access ssh --hostname %h
    ```
2.  Connect: `ssh clipdash@ssh.clipdash.in`

### 8. Nginx Setup (Serving the Website)
```bash
# 1. Move Signup Page
sudo mkdir -p /var/www/html
sudo cp signup.html /var/www/html/index.html

# 2. Configure Nginx
sudo nano /etc/nginx/sites-available/default
# (Paste the Nginx config provided in the original guide)

# 3. Restart
sudo systemctl restart nginx
```

---

## PART 2: TROUBLESHOOTING

### 1. "Quota Exceeded" (Hot Switch)
If YouTube API limits are hit:
1.  Open `.env`: `nano .env`
2.  Change `YOUTUBE_API_KEY`.
3.  Restart: `sudo systemctl restart clipstream`

### 2. "Address already in use"
If the server won't start:
```bash
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### 3. Site not loading?
- Check if `uvicorn` is running.
- Check if `cloudflared` is running.
- Check `sudo systemctl status nginx`.

---

## PART 3: USER GUIDE

### 1. Setup Nightbot
- Add Nightbot as a moderator in your YouTube Studio.

### 2. Get Discord Webhook
- Discord Channel Settings -> Integrations -> Webhooks -> Copy URL.

### 3. Sign Up
- Go to `https://www.clipdash.in`.
- Enter your details.
- Copy the generated command.

### 4. Add Command
- Go to Nightbot Dashboard -> Commands -> Custom -> Add Command.
- Command: `!clip`
- Message: (Paste the code).
- Userlevel: Everyone.

### 5. Usage
- Type `!clip` in YouTube Chat.
- Type `!clip Title of the clip` to add a title.

--------------------------------------------------------------------------------

## ⚖️ License

**Copyright © 2025 ClipDash.in (Aashpaw). All Rights Reserved.**

This project is proprietary software. Unauthorized copying, modification, distribution, or use for commercial purposes is strictly prohibited.
See the [LICENSE](LICENSE) file for details.
