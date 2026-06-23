import discord
from discord.ext import commands
from discord import app_commands
import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from config import Colors

# Load environment variables from .env file or environment
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)
TOKEN = os.getenv('DISCORD_TOKEN')

# Fallback: read .env file directly if dotenv fails
if not TOKEN:
    try:
        with open(env_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                if line.startswith('DISCORD_TOKEN='):
                    TOKEN = line.strip().split('=', 1)[1]
                    break
    except Exception as e:
        logger.error(f"Failed to read .env file: {e}")

# Check if token is still missing
if not TOKEN:
    logger.error("❌ DISCORD_TOKEN not found in environment variables or .env file!")
    raise ValueError("DISCORD_TOKEN is required but not set")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.moderation = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


@bot.event
async def on_ready():
    """Called when the bot is ready."""
    try:
        synced = await bot.tree.sync()
        logger.info(f'✅ Synced {len(synced)} slash command(s)')
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
    
    logger.info(f'✅ Bot logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🛡️ server safety | !help | /help"
        )
    )
    
    # Send test message to log channel
    log_channel_id = 1518955819691937882
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        try:
            await log_channel.send("✅ Bot is online and logging is working!")
            logger.info(f"✅ Test message sent to log channel")
        except Exception as e:
            logger.error(f"Failed to send test message: {e}")


@bot.event
async def on_member_remove(member):
    """Called when a member leaves the server."""
    log_channel_id = 1518955819691937882
    log_channel = bot.get_channel(log_channel_id)
    
    if log_channel:
        embed = discord.Embed(
            title="👋 Member Left",
            description=f"{member.mention} has left the server.",
            color=Colors.DANGER,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="User", value=f"{member} (`{member.id}`)", inline=True)
        embed.add_field(name="Joined", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        
        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to log member leave: {e}")


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    
    logger.error(f"Command error: {error} - Type: {type(error).__name__}")
    
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)
    
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            title="❌ Bot Permission Missing",
            description=f"I don't have the required permissions to perform this action.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)
    
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title="❌ Invalid Argument",
            description="Please check your command syntax.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)
    
    elif isinstance(error, commands.MemberNotFound):
        embed = discord.Embed(
            title="❌ Member Not Found",
            description="The specified member could not be found.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)
    
    else:
        logger.error(f"Unhandled error: {error}", exc_info=True)
        embed = discord.Embed(
            title="❌ An Error Occurred",
            description=f"An unexpected error occurred: {str(error)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handle slash command errors."""
    
    logger.error(f"Slash command error: {error} - Type: {type(error).__name__}")
    
    if isinstance(error, app_commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    elif isinstance(error, app_commands.BotMissingPermissions):
        embed = discord.Embed(
            title="❌ Bot Permission Missing",
            description=f"I don't have the required permissions to perform this action.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    elif isinstance(error, app_commands.NoPrivateMessage):
        embed = discord.Embed(
            title="❌ Server Only",
            description="This command can only be used in a server.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    else:
        logger.error(f"Slash command error: {error}", exc_info=True)
        embed = discord.Embed(
            title="❌ An Error Occurred",
            description=f"An unexpected error occurred: {str(error)}",
            color=discord.Color.red()
        )
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                logger.error("Failed to send error message to user")


async def load_cogs():
    """Load all cogs from the cogs directory."""
    cogs_dir = "cogs"
    
    if not os.path.exists(cogs_dir):
        os.makedirs(cogs_dir)
        logger.warning(f"Created {cogs_dir} directory")
    
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logger.info(f"✅ Loaded cog: {filename[:-3]}")
            except Exception as e:
                logger.error(f"❌ Failed to load cog {filename}: {e}")


@bot.command(name="help")
async def help_command(ctx):
    """Display help for the bot."""
    
    embed = discord.Embed(
        title="🛡️ Moderation Bot - Command List",
        description="Here are all available moderation commands:",
        color=Colors.PRIMARY
    )
    
    # Moderation Commands
    embed.add_field(
        name="🔨 **Prefix Commands** (!)",
        value="`!kick <member> [reason]` - Kick a member\n"
              "`!ban <member> [reason]` - Ban a member\n"
              "`!warn <member> [reason]` - Warn a member (3 warns = timeout)\n"
              "`!mute <member> [duration] [reason]` - Mute a member\n"
              "`!unmute <member> [reason]` - Unmute a member\n"
              "`!clear [amount]` - Clear messages (1-100)\n"
              "`!purge [amount] [@user] [--content text]` - Advanced message purge\n"
              "`!warnings [member]` - Check warnings\n"
              "`!clearwarnings [@user]` - Clear warnings (all if no user)",
        inline=False
    )
    
    # Slash Commands
    embed.add_field(
        name="⚡ **Slash Commands** (/)",
        value="`/kick` - Kick a member\n"
              "`/ban` - Ban a member\n"
              "`/warn` - Warn a member\n"
              "`/mute` - Mute a member\n"
              "`/unmute` - Unmute a member\n"
              "`/clear` - Clear messages\n"
              "`/purge` - Advanced message purge\n"
              "`/warnings` - Check warnings\n"
              "`/clearwarnings` - Clear warnings",
        inline=False
    )
    
    # Durations for mute
    embed.add_field(
        name="⏱️ **Mute Duration Format**",
        value="`1s` - seconds\n"
              "`30m` - minutes\n"
              "`1h` - hours\n"
              "`7d` - days",
        inline=False
    )
    
    # Notes
    embed.add_field(
        name="📝 **Notes**",
        value="• All moderation actions are logged to `#moderation-logs`\n"
              "• Create a `#moderation-logs` channel for logging\n"
              "• Use either prefix (!) or slash (/) commands\n"
              "• Only users with moderation permissions can use these commands",
        inline=False
    )
    
    embed.set_footer(text="Version 1.0.0 | Made with ❤️")
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/123456789/moderation-icon.png"
    )
    
    await ctx.send(embed=embed)


async def main():
    """Main bot startup function."""
    if not TOKEN:
        logger.error("❌ DISCORD_TOKEN not found in .env file!")
        return
    
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
