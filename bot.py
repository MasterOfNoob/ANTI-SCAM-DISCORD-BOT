import discord
import requests
import json
import base64
import os
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- CONFIGURATION ---
# Get tokens from environment variables for security
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
# This key can be for the default service or your custom service.
SERVICE_API_KEY = os.getenv('SERVICE_API_KEY')

# Check if the tokens were loaded successfully
if not DISCORD_TOKEN or not SERVICE_API_KEY:
    print("Error: Discord or Service API key not found. Please check your .env file.")
    exit()

# The ID of the channel where you want to log the scam attempts.
# Set to None if you want logs to be sent to the same channel where the message was posted.
LOG_CHANNEL_ID = PLACEHOLDER # Example: 1406617797320249368

# The bot's operational mode:
# - "all-channels": The bot monitors all channels it has access to.
# - "multi-channel": The bot only monitors channels in the TARGET_CHANNELS list.
MODE = "all-channels"

# A list of channel IDs to monitor if MODE is set to "multi-channel".
# You can get a channel ID by right-clicking the channel in Discord and selecting "Copy ID".
TARGET_CHANNELS = [
    # Example: 123456789012345678, # Example: General Chat Channel
    # Example: 987654321098765432  # Example: Memes Channel
]

# Exceptions: A list of IDs the bot should ignore.
# Add the IDs of channels, users, or roles that should be exempt from scam checks.
EXCEPTIONS = {
    "channels": [], # Add channel IDs here
    "users": [],    # Add user IDs here
    "roles": []     # Add role IDs here
}

# The API URL for the internal image analysis service.
ANALYSIS_SERVICE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
HEADERS = {'Content-Type': 'application/json'}

# The specific criteria used to identify various scam images based on known patterns.
# Add or remove prompts from this list to customize scam detection.
SCAM_PROMPTS = [
    "Does this image contain a URL for a gambling site or a site offering a free game currency, such as 'GERMESBET.COM'?",
    "Does this image offer a free gift, free Discord Nitro, or a special offer that looks too good to be true?",
    "Is there a QR code in this image that asks for a login or promises a free item?",
    "Does this image contain text encouraging a user to click a suspicious link to get free money or items?",
    "Is this image a phishing scam, such as one impersonating a legitimate service like Discord, Steam, or a game?"
]

# --- BOT SETUP ---
# Enable necessary intents for the bot to function properly
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
intents.messages = True
intents.guilds = True # Required for role checking
client = discord.Client(intents=intents)

# --- HELPER FUNCTIONS ---
def get_image_as_base64(image_url):
    """
    Downloads an image from a URL and converts it to a base64-encoded string.
    """
    try:
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        # Open image with PIL to handle various formats and get data as jpeg
        with Image.open(BytesIO(image_response.content)) as img:
            with BytesIO() as output_buffer:
                img.save(output_buffer, format="JPEG")
                image_bytes = output_buffer.getvalue()

        return base64.b64encode(image_bytes).decode('utf-8')

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

async def check_image_for_scam(image_url):
    """
    Checks if an image is a known scam using the Gemini API and multiple prompts.
    """
    try:
        image_data = get_image_as_base64(image_url)
        if not image_data:
            return False

        # Iterate through the list of scam prompts
        for prompt in SCAM_PROMPTS:
            request_data = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ]
            }

            response = requests.post(f"{ANALYSIS_SERVICE_URL}?key={SERVICE_API_KEY}",
                                     headers=HEADERS,
                                     data=json.dumps(request_data))
            response.raise_for_status()

            # Check if the Gemini API response indicates a scam
            api_response = response.json()
            response_text = api_response['candidates'][0]['content']['parts'][0]['text']

            # If the response confirms the prompt, it's a scam.
            if "yes" in response_text.lower() or "scam" in response_text.lower():
                return True

        return False  # Return False if none of the prompts detect a scam
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"Failed to parse API response: {e}")
        return False

# --- DISCORD BOT EVENTS ---
# This event runs when the bot is ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')
    print('Bot is ready to detect scams.')

# This event runs whenever a message is sent in a channel the bot can see
@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Check for exceptions before doing any processing
    if message.channel.id in EXCEPTIONS["channels"] or message.author.id in EXCEPTIONS["users"]:
        return

    # Check for excepted roles
    if hasattr(message.author, 'roles'):
        author_role_ids = [role.id for role in message.author.roles]
        if any(role_id in EXCEPTIONS["roles"] for role_id in author_role_ids):
            return

    # Check the operational mode
    if MODE == "multi-channel" and message.channel.id not in TARGET_CHANNELS:
        return

    # Process only messages with attachments
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type.startswith('image/'):
                print(f"Checking image from {message.author}: {attachment.url}")
                
                # Check if the image is a known scam.
                is_scam = await check_image_for_scam(attachment.url)
                
                if is_scam:
                    print(f"Scam image detected from {message.author}. Deleting message.")
                    try:
                        file_to_send = await attachment.to_file()
                        
                        # Determine where to send the log message
                        if LOG_CHANNEL_ID:
                            log_channel = client.get_channel(LOG_CHANNEL_ID)
                            if log_channel:
                                print(f"Sending log message to channel: {log_channel.name}")
                                await log_channel.send(
                                    f"⚠️ **Warning:** Scam image detected from user **{message.author}** (`{message.author.id}`).",
                                    file=file_to_send
                                )
                            else:
                                print(f"Error: Log channel with ID {LOG_CHANNEL_ID} not found.")
                        else:
                            print(f"Sending warning message to channel: {message.channel.name}")
                            await message.channel.send(
                                f"⚠️ **Warning:** Scam image detected and deleted from {message.author.mention}.",
                                file=file_to_send
                            )
                            
                        await message.delete()
                        print("Message deleted successfully.")
                    except discord.Forbidden:
                        print("Error: The bot does not have permission to delete messages or send messages in this channel.")
                    except discord.NotFound:
                        print("Error: The message or log channel was not found.")
                    return  # Exit after finding and deleting the scam image.

# --- RUN THE BOT ---
client.run(DISCORD_TOKEN)