# How to Setup ClipStream Bot (For Streamers)

So you want to clip your YouTube stream and send it to Discord automatically? Follow these simple steps.

## Prerequisite: Setup Nightbot
If you haven't used Nightbot before:
1.  Go to [nightbot.tv](https://nightbot.tv) and **Login with YouTube**.
2.  Click the blue **"Join Channel"** button (top right dashboard).
3.  **Make Nightbot a Moderator:**
    *   Go to your [YouTube Studio](https://studio.youtube.com).
    *   Settings -> Community.
    *   Paste this URL into "Moderators": `https://www.youtube.com/channel/UCSvjQsqFweU1KyBCMC3c0yA` (This is Nightbot).
    *   Click Save.

## Step 1: Get Your Discord Webhook
We need a "mailbox" to send the clips to.
1.  Open **Discord** on your PC.
2.  Go to your server and **Right-click** the text channel where you want clips to appear (e.g., `#clips`).
3.  Click **Edit Channel** (the gear icon ⚙️).
4.  Click **Integrations** (on the left menu).
5.  Click **Webhooks**.
6.  Click **New Webhook**.
7.  Name it "ClipBot" and click **Copy Webhook URL**.

## Step 2: Connect Your Channel
**First, find your Channel ID (It starts with "UC").**
1.  Go to [YouTube Advanced Settings](https://www.youtube.com/account_advanced).
2.  Copy the **Channel ID** (e.g., `UC12345...`).

**Now connect it:**
1.  Go to our signup page: [clipdash.in](https://clipdash.in)
2.  Enter your **Email**.
3.  Paste your **Channel ID** (or the full link `youtube.com/channel/UC...`).
4.  Paste the **Discord Webhook URL**.
5.  Click **Connect Channel**.

## Step 3: Add to Nightbot
1.  After connecting, you will see a **Green Box** with a command.
2.  **Copy that entire command.**
3.  Go to your [Nightbot Dashboard](https://nightbot.tv/dashboard).
4.  Go to **Commands** -> **Custom**.
5.  Click **Add Command**.
6.  **Command:** `!clip`
7.  **Message:** Paste the code you copied.
8.  Click **Submit**.

**DONE!**
Go to your chat and type `!clip` (or `!clip epic fail`) to test it!
