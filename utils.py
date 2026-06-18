# Utility functions for embeds and formatting
import discord
from datetime import datetime
from config import Colors, Emojis

def create_action_embed(
    action: str,
    target_user: discord.Member,
    moderator: discord.Member,
    reason: str = "No reason provided",
    duration: str = None,
    color: discord.Color = Colors.PRIMARY
) -> discord.Embed:
    """Create a professional moderation action embed."""
    
    embed = discord.Embed(
        title=f"{Emojis.MODERATION} {action}",
        description=f"**User:** {target_user.mention} (`{target_user.id}`)",
        color=color,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="👤 Moderator",
        value=f"{moderator.mention}",
        inline=True
    )
    
    if duration:
        embed.add_field(
            name=f"{Emojis.TIMEOUT} Duration",
            value=duration,
            inline=True
        )
    
    embed.add_field(
        name="📝 Reason",
        value=reason,
        inline=False
    )
    
    embed.add_field(
        name="⏰ Timestamp",
        value=f"<t:{int(datetime.now().timestamp())}:F>",
        inline=False
    )
    
    embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
    embed.set_footer(
        text=f"User ID: {target_user.id}",
        icon_url="https://cdn.discordapp.com/embed/avatars/0.png"
    )
    
    return embed


def create_confirmation_embed(
    action: str,
    target_user: discord.Member,
    status: str = "success"
) -> discord.Embed:
    """Create a confirmation embed for moderation actions."""
    
    color = Colors.SUCCESS if status == "success" else Colors.DANGER
    emoji = Emojis.SUCCESS if status == "success" else Emojis.ERROR
    
    embed = discord.Embed(
        title=f"{emoji} {action}",
        description=f"{target_user.mention} has been {action.lower()}.",
        color=color,
        timestamp=datetime.now()
    )
    
    embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
    
    return embed


def create_warn_embed(
    target_user: discord.Member,
    moderator: discord.Member,
    reason: str,
    warn_count: int
) -> discord.Embed:
    """Create a warning embed with warn count."""
    
    embed = discord.Embed(
        title=f"{Emojis.WARN} Warning Issued",
        description=f"{target_user.mention} has been warned.",
        color=Colors.WARNING,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="⚠️ Warn Count", value=f"`{warn_count}`", inline=True)
    embed.add_field(name="👤 Moderator", value=f"{moderator.mention}", inline=True)
    embed.add_field(name="📝 Reason", value=reason, inline=False)
    
    embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
    embed.set_footer(text=f"User ID: {target_user.id}")
    
    return embed


def create_error_embed(error_message: str) -> discord.Embed:
    """Create an error embed."""
    
    embed = discord.Embed(
        title=f"{Emojis.ERROR} Error",
        description=error_message,
        color=Colors.DANGER,
        timestamp=datetime.now()
    )
    
    return embed


def create_moderation_log_embed(
    action: str,
    target_user: discord.Member,
    moderator: discord.Member,
    reason: str,
    duration: str = None
) -> discord.Embed:
    """Create an embed for moderation logs."""
    
    action_lower = action.lower()
    if "kick" in action_lower:
        color = Colors.DANGER
        emoji = Emojis.KICK
    elif "ban" in action_lower:
        color = Colors.DANGER
        emoji = Emojis.BAN
    elif "warn" in action_lower:
        color = Colors.WARNING
        emoji = Emojis.WARN
    elif "mute" in action_lower or "timeout" in action_lower:
        color = Colors.MUTE
        emoji = Emojis.TIMEOUT
    else:
        color = Colors.PRIMARY
        emoji = Emojis.MODERATION
    
    embed = discord.Embed(
        title=f"{emoji} Moderation Log - {action}",
        color=color,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="👤 User",
        value=f"{target_user.mention}\n`{target_user.id}`",
        inline=True
    )
    
    embed.add_field(
        name="🛡️ Moderator",
        value=f"{moderator.mention}",
        inline=True
    )
    
    embed.add_field(name="\u200b", value="\u200b", inline=True)  # Empty field for spacing
    
    embed.add_field(
        name="📝 Reason",
        value=reason,
        inline=False
    )
    
    if duration:
        embed.add_field(
            name=f"{Emojis.TIMEOUT} Duration",
            value=duration,
            inline=True
        )
    
    embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
    embed.set_footer(text=f"ID: {target_user.id}")
    
    return embed
