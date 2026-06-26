import discord
from discord.ext import commands
from discord import app_commands
from config import Colors, Emojis
from utils import (
    create_action_embed,
    create_confirmation_embed,
    create_warn_embed,
    create_error_embed,
    create_moderation_log_embed
)
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Moderation(commands.Cog):
    """Moderation commands with beautiful embeds."""
    
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}  # {user_id: warning_count}
        self.loa_users = {}  # {user_id: (guild_id, mute_duration)} - users on leave of absence
    
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server."""
        
        if member == ctx.author:
            embed = create_error_embed("You cannot kick yourself!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if member.top_role >= ctx.author.top_role:
            embed = create_error_embed("You cannot kick someone with an equal or higher role!")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Create action embed
        embed = create_action_embed(
            action="Member Kicked",
            target_user=member,
            moderator=ctx.author,
            reason=reason,
            color=Colors.DANGER
        )
        
        # Kick the member
        await member.kick(reason=reason)
        
        # Send confirmation
        confirmation = create_confirmation_embed("Kicked", member, "success")
        await ctx.send(embed=confirmation)
        
        # Log to moderation logs
        await self.log_action(embed, ctx.guild)
    
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server."""
        
        try:
            if member == ctx.author:
                embed = create_error_embed("You cannot ban yourself!")
                return await ctx.send(embed=embed, delete_after=5)
            
            if member.top_role >= ctx.author.top_role:
                embed = create_error_embed("You cannot ban someone with an equal or higher role!")
                return await ctx.send(embed=embed, delete_after=5)
            
            # Create action embed
            embed = create_action_embed(
                action="Member Banned",
                target_user=member,
                moderator=ctx.author,
                reason=reason,
                color=Colors.DANGER
            )
            
            # Ban the member
            await member.ban(reason=reason)
            
            # Send confirmation
            confirmation = create_confirmation_embed("Banned", member, "success")
            await ctx.send(embed=confirmation)
            
            # Log to moderation logs
            await self.log_action(embed, ctx.guild)
        except Exception as e:
            logger.error(f"Error in ban command: {e}", exc_info=True)
            embed = create_error_embed(f"An error occurred: {str(e)}")
            await ctx.send(embed=embed, delete_after=5)
    
    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """Unban a user from the server by ID."""
        
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(f"✅ Unbanned user {user} ({user_id})")
        except discord.NotFound:
            await ctx.send("❌ User not found")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Error: {e}")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name="loa")
    @commands.has_permissions(manage_messages=True)
    async def loa(self, ctx, member: discord.Member, reason: str, mute_duration: str = "1h"):
        """Put a user on leave of absence (no pings allowed, auto-mute if pinged)."""
        
        if member == ctx.author:
            embed = create_error_embed("You cannot put yourself on LOA!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if member.bot:
            embed = create_error_embed("You cannot put a bot on LOA!")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Parse mute duration
        duration_map = {
            'm': timedelta(minutes=1),
            'h': timedelta(hours=1),
            'd': timedelta(days=1)
        }
        
        try:
            unit = mute_duration[-1].lower()
            if unit not in duration_map:
                raise ValueError("Invalid unit")
            
            amount = int(mute_duration[:-1])
            if amount <= 0:
                raise ValueError("Invalid amount")
            
            mute_td = duration_map[unit] * amount
        except:
            embed = create_error_embed("Invalid duration! Use format like: 1h, 30m, 1d")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Add to LOA list with mute duration
        self.loa_users[member.id] = (ctx.guild.id, mute_td)
        
        embed = discord.Embed(
            title="🏖️ Leave of Absence",
            description=f"{member.mention} has been put on LOA.",
            color=Colors.WARNING,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="👤 User", value=member.mention, inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=True)
        embed.add_field(name="⏱️ Mute Duration if Pinged", value=mute_duration, inline=True)
        embed.add_field(name="⚠️ Warning", value=f"Anyone who pings this user will be muted for {mute_duration}!", inline=False)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check if message contains pings to LOA users."""
        
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return
        
        # Check if message mentions any LOA users
        for user_id, (guild_id, mute_duration) in list(self.loa_users.items()):
            if guild_id != message.guild.id:
                continue
            
            # Check if user is mentioned
            if any(user.id == user_id for user in message.mentions):
                # Mute the person who pinged
                try:
                    await message.author.timeout(mute_duration, reason=f"Pinged LOA user {user_id}")
                    
                    duration_str = str(mute_duration)
                    embed = discord.Embed(
                        title="🔇 Auto-Mute",
                        description=f"{message.author.mention} has been muted for {duration_str} for pinging an LOA user.",
                        color=Colors.DANGER,
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="⚠️ Reason", value="Pinging LOA user is not allowed", inline=False)
                    await message.channel.send(embed=embed)
                except Exception as e:
                    logger.error(f"Failed to mute user for LOA ping: {e}")
    
    @commands.command(name="loa_remove")
    @commands.has_permissions(manage_messages=True)
    async def loa_remove(self, ctx, member: discord.Member):
        """Remove a user from leave of absence."""
        
        if member.id in self.loa_users:
            del self.loa_users[member.id]
            await ctx.send(f"✅ Removed {member.mention} from LOA.")
        else:
            await ctx.send("❌ User is not on LOA.")
    
    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Warn a member."""
        
        if member == ctx.author:
            embed = create_error_embed("You cannot warn yourself!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if member.bot:
            embed = create_error_embed("You cannot warn a bot!")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Update warning count
        if member.id not in self.warnings:
            self.warnings[member.id] = 0
        
        self.warnings[member.id] += 1
        warn_count = self.warnings[member.id]
        
        # Create warning embed
        embed = create_warn_embed(member, ctx.author, reason, warn_count)
        await ctx.send(embed=embed)
        
        # Log to moderation logs
        await self.log_action(embed, ctx.guild)
        
        # Auto-action after 3 warnings
        if warn_count == 3:
            await member.timeout(timedelta(hours=1), reason="Reached 3 warnings")
            timeout_embed = discord.Embed(
                title=f"{Emojis.TIMEOUT} Automatic Timeout",
                description=f"{member.mention} has been timed out for 1 hour (reached 3 warnings).",
                color=Colors.MUTE
            )
            await ctx.send(embed=timeout_embed)
    
    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str = "1h", *, reason="No reason provided"):
        """Mute a member using timeout."""
        
        if member == ctx.author:
            embed = create_error_embed("You cannot mute yourself!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if member.bot:
            embed = create_error_embed("You cannot mute a bot!")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Parse duration
        duration_map = {
            "s": 1,
            "m": 60,
            "h": 3600,
            "d": 86400
        }
        
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            if unit not in duration_map:
                raise ValueError
            seconds = amount * duration_map[unit]
        except (ValueError, IndexError):
            embed = create_error_embed("Invalid duration format! Use: `1s`, `30m`, `1h`, `7d`")
            return await ctx.send(embed=embed, delete_after=5)
        
        timeout_delta = timedelta(seconds=seconds)
        
        # Create action embed
        embed = create_action_embed(
            action="Member Muted",
            target_user=member,
            moderator=ctx.author,
            reason=reason,
            duration=duration,
            color=Colors.MUTE
        )
        
        # Mute the member
        await member.timeout(timeout_delta, reason=reason)
        
        # Send confirmation
        confirmation = create_confirmation_embed("Muted", member, "success")
        await ctx.send(embed=confirmation)
        
        # Log to moderation logs
        await self.log_action(embed, ctx.guild)
    
    @commands.command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Unmute a member."""
        
        if member == ctx.author:
            embed = create_error_embed("You cannot unmute yourself!")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Create action embed
        embed = discord.Embed(
            title=f"{Emojis.UNMUTE} Member Unmuted",
            description=f"**User:** {member.mention} (`{member.id}`)",
            color=Colors.SUCCESS
        )
        
        embed.add_field(name="👤 Moderator", value=f"{ctx.author.mention}", inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        # Unmute the member
        await member.timeout(None, reason=reason)
        
        # Send confirmation
        confirmation = create_confirmation_embed("Unmuted", member, "success")
        await ctx.send(embed=confirmation)
        
        # Log to moderation logs
        await self.log_action(embed, ctx.guild)
    
    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        """Clear messages from the channel."""
        
        if amount < 1 or amount > 100:
            embed = create_error_embed("Please specify a number between 1 and 100!")
            return await ctx.send(embed=embed, delete_after=5)
        
        deleted = await ctx.channel.purge(limit=amount)
        
        embed = discord.Embed(
            title=f"{Emojis.CLEAR} Messages Cleared",
            description=f"**{len(deleted)}** messages have been deleted.",
            color=Colors.SUCCESS
        )
        
        embed.add_field(name="👤 Moderator", value=f"{ctx.author.mention}", inline=True)
        embed.add_field(name="📍 Channel", value=ctx.channel.mention, inline=True)
        
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=5)
    
    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10, member: discord.Member = None, *, content: str = None):
        """Purge messages with advanced filtering options.
        
        Usage:
        !purge 50 - Delete last 50 messages
        !purge 30 @user - Delete last 30 messages from @user
        !purge 20 --content spam - Delete last 20 messages containing 'spam'
        """
        
        if amount < 1 or amount > 500:
            embed = create_error_embed("Please specify a number between 1 and 500!")
            return await ctx.send(embed=embed, delete_after=5)
        
        def check(msg):
            # Filter by user if specified
            if member and msg.author != member:
                return False
            
            # Filter by content if specified
            if content and content.lower() not in msg.content.lower():
                return False
            
            return True
        
        # Purge messages
        deleted = await ctx.channel.purge(limit=amount, check=check)
        
        # Create purge summary embed
        embed = discord.Embed(
            title=f"{Emojis.DELETE} Messages Purged",
            description=f"**{len(deleted)}** messages have been deleted.",
            color=Colors.SUCCESS
        )
        
        embed.add_field(name="👤 Moderator", value=f"{ctx.author.mention}", inline=True)
        embed.add_field(name="📍 Channel", value=ctx.channel.mention, inline=True)
        
        if member:
            embed.add_field(name="🎯 Target User", value=f"{member.mention}", inline=True)
        
        if content:
            embed.add_field(name="🔍 Filter", value=f"`{content}`", inline=True)
        
        embed.add_field(name="⏰ Timestamp", value=f"<t:{int(__import__('datetime').datetime.now().timestamp())}:F>", inline=False)
        
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=10)
    
    @commands.command(name="warnings")
    async def check_warnings(self, ctx, member: discord.Member = None):
        """Check warnings for a member."""
        
        member = member or ctx.author
        warn_count = self.warnings.get(member.id, 0)
        
        embed = discord.Embed(
            title=f"{Emojis.WARN} Warning Record",
            description=f"**User:** {member.mention}",
            color=Colors.WARNING
        )
        
        embed.add_field(
            name="⚠️ Total Warnings",
            value=f"`{warn_count}/3`",
            inline=False
        )
        
        if warn_count > 0:
            embed.add_field(
                name="📊 Status",
                value="⚠️ **Warning!** User is approaching automatic timeout.",
                inline=False
            )
        else:
            embed.add_field(
                name="📊 Status",
                value="✅ **Clean record** - No warnings.",
                inline=False
            )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="clearwarnings")
    @commands.has_permissions(manage_messages=True)
    async def clear_warnings(self, ctx, member: discord.Member = None):
        """Clear warnings for a member or all members."""
        
        if member:
            # Clear warnings for specific member
            if member.id not in self.warnings or self.warnings[member.id] == 0:
                embed = create_error_embed(f"{member.mention} has no warnings to clear!")
                return await ctx.send(embed=embed, delete_after=5)
            
            old_count = self.warnings[member.id]
            self.warnings[member.id] = 0
            
            embed = discord.Embed(
                title="✨ Warnings Cleared",
                description=f"Warnings cleared for {member.mention}",
                color=Colors.SUCCESS
            )
            
            embed.add_field(name="👤 Moderator", value=f"{ctx.author.mention}", inline=True)
            embed.add_field(name="⚠️ Previous Count", value=f"`{old_count}`", inline=True)
            embed.add_field(name="📝 New Count", value=f"`0`", inline=True)
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await ctx.send(embed=embed)
            
            # Log action
            log_embed = discord.Embed(
                title="✨ Warnings Cleared",
                description=f"Warnings cleared for {member.mention}",
                color=Colors.SUCCESS
            )
            log_embed.add_field(name="🛡️ Moderator", value=f"{ctx.author.mention}", inline=True)
            log_embed.add_field(name="⚠️ Previous Count", value=f"`{old_count}`", inline=True)
            await self.log_action(log_embed, ctx.guild)
        
        else:
            # Clear all warnings
            if not self.warnings or all(count == 0 for count in self.warnings.values()):
                embed = create_error_embed("No warnings to clear!")
                return await ctx.send(embed=embed, delete_after=5)
            
            total_cleared = sum(1 for count in self.warnings.values() if count > 0)
            self.warnings.clear()
            
            embed = discord.Embed(
                title="✨ All Warnings Cleared",
                description=f"All warnings have been reset server-wide",
                color=Colors.SUCCESS
            )
            
            embed.add_field(name="👤 Moderator", value=f"{ctx.author.mention}", inline=True)
            embed.add_field(name="🔄 Users Cleared", value=f"`{total_cleared}`", inline=True)
            
            await ctx.send(embed=embed)
            
            # Log action
            log_embed = discord.Embed(
                title="✨ All Warnings Cleared",
                description=f"All warnings have been reset server-wide by {ctx.author.mention}",
                color=Colors.SUCCESS
            )
            log_embed.add_field(name="🔄 Users Cleared", value=f"`{total_cleared}`", inline=False)
            await self.log_action(log_embed, ctx.guild)
    
    # ==================== SLASH COMMANDS ====================
    
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="Reason for kicking")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    async def slash_kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Slash command version of kick."""
        
        if member == interaction.user:
            await interaction.response.send_message(embed=create_error_embed("You cannot kick yourself!"), ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(embed=create_error_embed("You cannot kick someone with an equal or higher role!"), ephemeral=True)
            return
        
        embed = create_action_embed(
            action="Member Kicked",
            target_user=member,
            moderator=interaction.user,
            reason=reason,
            color=Colors.DANGER
        )
        
        await member.kick(reason=reason)
        confirmation = create_confirmation_embed("Kicked", member, "success")
        await interaction.response.send_message(embed=confirmation)
        await self.log_action(embed, interaction.guild)
    
    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="The member to ban", reason="Reason for banning")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    async def slash_ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Slash command version of ban."""
        
        if member == interaction.user:
            await interaction.response.send_message(embed=create_error_embed("You cannot ban yourself!"), ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(embed=create_error_embed("You cannot ban someone with an equal or higher role!"), ephemeral=True)
            return
        
        embed = create_action_embed(
            action="Member Banned",
            target_user=member,
            moderator=interaction.user,
            reason=reason,
            color=Colors.DANGER
        )
        
        await member.ban(reason=reason)
        confirmation = create_confirmation_embed("Banned", member, "success")
        await interaction.response.send_message(embed=confirmation)
        await self.log_action(embed, interaction.guild)
    
    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="The member to warn", reason="Reason for warning")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def slash_warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Slash command version of warn."""
        
        if member == interaction.user:
            await interaction.response.send_message(embed=create_error_embed("You cannot warn yourself!"), ephemeral=True)
            return
        
        if member.bot:
            await interaction.response.send_message(embed=create_error_embed("You cannot warn a bot!"), ephemeral=True)
            return
        
        if member.id not in self.warnings:
            self.warnings[member.id] = 0
        
        self.warnings[member.id] += 1
        warn_count = self.warnings[member.id]
        
        embed = create_warn_embed(member, interaction.user, reason, warn_count)
        await interaction.response.send_message(embed=embed)
        await self.log_action(embed, interaction.guild)
        
        if warn_count == 3:
            await member.timeout(timedelta(hours=1), reason="Reached 3 warnings")
            timeout_embed = discord.Embed(
                title=f"{Emojis.TIMEOUT} Automatic Timeout",
                description=f"{member.mention} has been timed out for 1 hour (reached 3 warnings).",
                color=Colors.MUTE
            )
            await interaction.followup.send(embed=timeout_embed)
    
    @app_commands.command(name="mute", description="Mute a member using timeout")
    @app_commands.describe(member="The member to mute", duration="Duration (e.g., 1h, 30m, 7d)", reason="Reason for muting")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def slash_mute(self, interaction: discord.Interaction, member: discord.Member, duration: str = "1h", reason: str = "No reason provided"):
        """Slash command version of mute."""
        
        if member == interaction.user:
            await interaction.response.send_message(embed=create_error_embed("You cannot mute yourself!"), ephemeral=True)
            return
        
        if member.bot:
            await interaction.response.send_message(embed=create_error_embed("You cannot mute a bot!"), ephemeral=True)
            return
        
        duration_map = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            if unit not in duration_map:
                raise ValueError
            seconds = amount * duration_map[unit]
        except (ValueError, IndexError):
            await interaction.response.send_message(embed=create_error_embed("Invalid duration format! Use: `1s`, `30m`, `1h`, `7d`"), ephemeral=True)
            return
        
        timeout_delta = timedelta(seconds=seconds)
        
        embed = create_action_embed(
            action="Member Muted",
            target_user=member,
            moderator=interaction.user,
            reason=reason,
            duration=duration,
            color=Colors.MUTE
        )
        
        await member.timeout(timeout_delta, reason=reason)
        confirmation = create_confirmation_embed("Muted", member, "success")
        await interaction.response.send_message(embed=confirmation)
        await self.log_action(embed, interaction.guild)
    
    @app_commands.command(name="unmute", description="Unmute a member")
    @app_commands.describe(member="The member to unmute", reason="Reason for unmuting")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def slash_unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Slash command version of unmute."""
        
        if member == interaction.user:
            await interaction.response.send_message(embed=create_error_embed("You cannot unmute yourself!"), ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"{Emojis.UNMUTE} Member Unmuted",
            description=f"**User:** {member.mention} (`{member.id}`)",
            color=Colors.SUCCESS
        )
        
        embed.add_field(name="👤 Moderator", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        await member.timeout(None, reason=reason)
        confirmation = create_confirmation_embed("Unmuted", member, "success")
        await interaction.response.send_message(embed=confirmation)
        await self.log_action(embed, interaction.guild)
    
    @app_commands.command(name="clear", description="Clear messages from the channel")
    @app_commands.describe(amount="Number of messages to clear (1-100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    async def slash_clear(self, interaction: discord.Interaction, amount: int = 10):
        """Slash command version of clear."""
        
        if amount < 1 or amount > 100:
            await interaction.response.send_message(embed=create_error_embed("Please specify a number between 1 and 100!"), ephemeral=True)
            return
        
        await interaction.response.defer()
        deleted = await interaction.channel.purge(limit=amount)
        
        embed = discord.Embed(
            title=f"{Emojis.CLEAR} Messages Cleared",
            description=f"**{len(deleted)}** messages have been deleted.",
            color=Colors.SUCCESS
        )
        
        embed.add_field(name="👤 Moderator", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="📍 Channel", value=interaction.channel.mention, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="purge", description="Advanced message purge with filtering")
    @app_commands.describe(amount="Number of messages to purge (1-500)", member="Filter by user (optional)", content="Filter by content (optional)")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    async def slash_purge(self, interaction: discord.Interaction, amount: int = 10, member: discord.Member = None, content: str = None):
        """Slash command version of purge."""
        
        if amount < 1 or amount > 500:
            await interaction.response.send_message(embed=create_error_embed("Please specify a number between 1 and 500!"), ephemeral=True)
            return
        
        await interaction.response.defer()
        
        def check(msg):
            if member and msg.author != member:
                return False
            if content and content.lower() not in msg.content.lower():
                return False
            return True
        
        deleted = await interaction.channel.purge(limit=amount, check=check)
        
        embed = discord.Embed(
            title=f"{Emojis.DELETE} Messages Purged",
            description=f"**{len(deleted)}** messages have been deleted.",
            color=Colors.SUCCESS
        )
        
        embed.add_field(name="👤 Moderator", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="📍 Channel", value=interaction.channel.mention, inline=True)
        
        if member:
            embed.add_field(name="🎯 Target User", value=f"{member.mention}", inline=True)
        
        if content:
            embed.add_field(name="🔍 Filter", value=f"`{content}`", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="warnings", description="Check warnings for a member")
    @app_commands.describe(member="The member to check (optional, defaults to you)")
    async def slash_warnings(self, interaction: discord.Interaction, member: discord.Member = None):
        """Slash command version of warnings."""
        
        member = member or interaction.user
        warn_count = self.warnings.get(member.id, 0)
        
        embed = discord.Embed(
            title=f"{Emojis.WARN} Warning Record",
            description=f"**User:** {member.mention}",
            color=Colors.WARNING
        )
        
        embed.add_field(
            name="⚠️ Total Warnings",
            value=f"`{warn_count}/3`",
            inline=False
        )
        
        if warn_count > 0:
            embed.add_field(
                name="📊 Status",
                value="⚠️ **Warning!** User is approaching automatic timeout.",
                inline=False
            )
        else:
            embed.add_field(
                name="📊 Status",
                value="✅ **Clean record** - No warnings.",
                inline=False
            )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(user_id="The user ID to unban")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    async def slash_unban(self, interaction: discord.Interaction, user_id: int):
        """Slash command version of unban."""
        
        try:
            user = await self.bot.fetch_user(user_id)
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ Unbanned user {user} ({user_id})")
        except discord.NotFound:
            await interaction.response.send_message("❌ User not found", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
    
    @app_commands.command(name="loa", description="Put a user on leave of absence")
    @app_commands.describe(member="The member to put on LOA", reason="Reason for LOA", mute_duration="Mute duration if pinged (e.g., 1h, 30m, 1d)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def slash_loa(self, interaction: discord.Interaction, member: discord.Member, reason: str, mute_duration: str = "1h"):
        """Slash command version of loa."""
        
        if member == interaction.user:
            await interaction.response.send_message(embed=create_error_embed("You cannot put yourself on LOA!"), ephemeral=True)
            return
        
        if member.bot:
            await interaction.response.send_message(embed=create_error_embed("You cannot put a bot on LOA!"), ephemeral=True)
            return
        
        # Parse mute duration
        duration_map = {
            'm': timedelta(minutes=1),
            'h': timedelta(hours=1),
            'd': timedelta(days=1)
        }
        
        try:
            unit = mute_duration[-1].lower()
            if unit not in duration_map:
                raise ValueError("Invalid unit")
            
            amount = int(mute_duration[:-1])
            if amount <= 0:
                raise ValueError("Invalid amount")
            
            mute_td = duration_map[unit] * amount
        except:
            await interaction.response.send_message(embed=create_error_embed("Invalid duration! Use format like: 1h, 30m, 1d"), ephemeral=True)
            return
        
        # Add to LOA list with mute duration
        self.loa_users[member.id] = (interaction.guild.id, mute_td)
        
        embed = discord.Embed(
            title="🏖️ Leave of Absence",
            description=f"{member.mention} has been put on LOA.",
            color=Colors.WARNING,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="👤 User", value=member.mention, inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=True)
        embed.add_field(name="⏱️ Mute Duration if Pinged", value=mute_duration, inline=True)
        embed.add_field(name="⚠️ Warning", value=f"Anyone who pings this user will be muted for {mute_duration}!", inline=False)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="loa_remove", description="Remove a user from leave of absence")
    @app_commands.describe(member="The member to remove from LOA")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def slash_loa_remove(self, interaction: discord.Interaction, member: discord.Member):
        """Slash command version of loa_remove."""
        
        if member.id in self.loa_users:
            del self.loa_users[member.id]
            await interaction.response.send_message(f"✅ Removed {member.mention} from LOA.")
        else:
            await interaction.response.send_message("❌ User is not on LOA.", ephemeral=True)
    
    @app_commands.command(name="clearwarnings", description="Clear warnings for a member or all members")
    @app_commands.describe(member="The member to clear warnings for (optional, clears all if not provided)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def slash_clearwarnings(self, interaction: discord.Interaction, member: discord.Member = None):
        """Slash command version of clearwarnings."""
        
        if member:
            # Clear warnings for specific member
            if member.id not in self.warnings or self.warnings[member.id] == 0:
                await interaction.response.send_message(
                    embed=create_error_embed(f"{member.mention} has no warnings to clear!"),
                    ephemeral=True
                )
                return
            
            old_count = self.warnings[member.id]
            self.warnings[member.id] = 0
            
            embed = discord.Embed(
                title="✨ Warnings Cleared",
                description=f"Warnings cleared for {member.mention}",
                color=Colors.SUCCESS
            )
            
            embed.add_field(name="👤 Moderator", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="⚠️ Previous Count", value=f"`{old_count}`", inline=True)
            embed.add_field(name="📝 New Count", value=f"`0`", inline=True)
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await interaction.response.send_message(embed=embed)
            
            # Log action
            log_embed = discord.Embed(
                title="✨ Warnings Cleared",
                description=f"Warnings cleared for {member.mention}",
                color=Colors.SUCCESS
            )
            log_embed.add_field(name="🛡️ Moderator", value=f"{interaction.user.mention}", inline=True)
            log_embed.add_field(name="⚠️ Previous Count", value=f"`{old_count}`", inline=True)
            await self.log_action(log_embed, interaction.guild)
        
        else:
            # Clear all warnings
            if not self.warnings or all(count == 0 for count in self.warnings.values()):
                await interaction.response.send_message(
                    embed=create_error_embed("No warnings to clear!"),
                    ephemeral=True
                )
                return
            
            total_cleared = sum(1 for count in self.warnings.values() if count > 0)
            self.warnings.clear()
            
            embed = discord.Embed(
                title="✨ All Warnings Cleared",
                description=f"All warnings have been reset server-wide",
                color=Colors.SUCCESS
            )
            
            embed.add_field(name="👤 Moderator", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="🔄 Users Cleared", value=f"`{total_cleared}`", inline=True)
            
            await interaction.response.send_message(embed=embed)
            
            # Log action
            log_embed = discord.Embed(
                title="✨ All Warnings Cleared",
                description=f"All warnings have been reset server-wide by {interaction.user.mention}",
                color=Colors.SUCCESS
            )
            log_embed.add_field(name="🔄 Users Cleared", value=f"`{total_cleared}`", inline=False)
            await self.log_action(log_embed, interaction.guild)
    
    async def log_action(self, embed: discord.Embed, guild: discord.Guild):
        """Send moderation action to logs channel."""
        
        log_channel = discord.utils.find(lambda c: c.name == "moderation-logs", guild.channels)
        
        if log_channel:
            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))
