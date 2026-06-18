# Bot Configuration
import discord

# Colors for embeds
class Colors:
    PRIMARY = discord.Color.from_rgb(88, 101, 242)  # Blurple
    SUCCESS = discord.Color.from_rgb(87, 171, 90)   # Green
    WARNING = discord.Color.from_rgb(254, 197, 45)  # Yellow
    DANGER = discord.Color.from_rgb(237, 66, 69)    # Red
    MUTE = discord.Color.from_rgb(156, 39, 176)     # Purple
    INFO = discord.Color.from_rgb(33, 150, 243)     # Light Blue

# Emojis
class Emojis:
    KICK = "🦶"
    BAN = "🔨"
    WARN = "⚠️"
    MUTE = "🔇"
    UNMUTE = "🔊"
    TIMEOUT = "⏱️"
    DELETE = "🗑️"
    CLEAR = "✨"
    SUCCESS = "✅"
    ERROR = "❌"
    INFO = "ℹ️"
    MODERATION = "🛡️"

# Default settings
DEFAULT_PREFIX = "!"
LOG_CHANNEL_NAME = "moderation-logs"
