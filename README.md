Discord Scam-Detecting Bot 🤖

This Python-based Discord bot uses the Gemini API to detect and automatically delete scam images in real-time. It's designed to be highly customizable and easy to integrate into your existing bot.
✨ Features

    Intelligent Scam Detection: Uses the Gemini API to analyze images for common scam patterns.

    Customizable Prompts: A list of prompts allows you to define what constitutes a scam, making it easy to adapt to new threats.

    Real-time Deletion: Instantly deletes scam messages and sends a warning to the channel where the message was posted.

    Flexible Modes: Choose between monitoring all channels or a specific list of channels.

    Exceptions: Define channels, users, and roles that are exempt from the scam detection process.

🛠️ Prerequisites

Before you begin, ensure you have:

    Python 3.8 or higher installed.

    A Discord bot token.

    A Google Gemini API key.

🚀 Setup & Installation
Step 1: Get Your API Keys

    Discord Bot Token: Create a new application on the Discord Developer Portal, turn it into a bot, and copy your token.

    Google Gemini API Key: Visit the Google AI Studio to get your API key.

Step 2: Project Setup

Create a new directory for your bot and set up a virtual environment (recommended).

mkdir discord-scam-bot
cd discord-scam-bot
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Step 3: Create the .env File

Create a file named .env in your project's root directory. This file will securely store your API keys.

DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN_HERE"
SERVICE_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY_HERE"

Step 4: Install Dependencies

Install the required Python libraries using pip:

pip install discord.py python-dotenv requests Pillow

Step 5: Configure the bot.py Script

Open bot.py and customize the variables at the top of the file to fit your needs:

    MODE: Change this to "all-channels" or "multi-channel" to control the bot's scope.

    TARGET_CHANNELS: If using "multi-channel" mode, add the IDs of the channels you want the bot to monitor.

    EXCEPTIONS: Add the IDs of channels, users, or roles that should be ignored.

    SCAM_PROMPTS: Modify the list of strings to change what the bot looks for in images.

Step 6: Run the Bot

Execute the script from your terminal to start the bot:

python3 bot.py

🔄 How to Integrate into an Existing Bot

If you already have a bot running, you can easily integrate this functionality by copying the core logic.

    Add Imports: Ensure your main bot file has the necessary imports at the top:

    import requests
    import json
    import base64
    from io import BytesIO
    from PIL import Image

    Copy Configuration: Copy the SCAM_PROMPTS, MODE, TARGET_CHANNELS, and EXCEPTIONS dictionaries and the ANALYSIS_SERVICE_URL/HEADERS variables from bot.py into your bot's script.

    Copy Helper Functions: Copy the get_image_as_base64 and check_image_for_scam functions. Place them anywhere in your script outside of your event listeners.

    Merge on_message Logic: This is the most important step. Do not create a second on_message function. Instead, merge the scam detection logic into your existing on_message event listener.

    Find your current on_message function, and add the scam-checking code block inside it. Make sure the checks for message.author == client.user and message.attachments are handled correctly before the scam-checking logic is executed. The final structure should look similar to this:

    @client.event
    async def on_message(message):
        # Your existing message handling logic goes here

        # --- START OF SCAM DETECTION LOGIC ---
        if message.author == client.user:
            return

        # Check for exceptions
        if message.channel.id in EXCEPTIONS["channels"] or message.author.id in EXCEPTIONS["users"]:
            return

        # ... (rest of the logic from the provided bot.py on_message function)

        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.startswith('image/'):
                    # ... (rest of the scam checking logic)
                    is_scam = await check_image_for_scam(attachment.url)
                    if is_scam:
                        # ... (deletion and warning message logic)
                        pass

        # Any of your other message-related logic can go here

    Review and Test: Carefully review the merged code to ensure all variables and functions are correctly referenced. Run your bot and test the scam detection functionality with test images to ensure everything is working as expected.