import logging
import re

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from config import Colors

logger = logging.getLogger(__name__)

CUSTOM_EMOJI_RE = re.compile(r"<(?P<animated>a?):(?P<name>[A-Za-z0-9_]{2,32}):(?P<id>[0-9]{15,25})>")
VALID_EMOJI_NAME_RE = re.compile(r"^[A-Za-z0-9_]{2,32}$")


class Emojis(commands.Cog):
    """Emoji utility commands."""

    def __init__(self, bot):
        self.bot = bot

    def parse_custom_emoji(self, emoji_text: str):
        match = CUSTOM_EMOJI_RE.fullmatch(emoji_text.strip())
        if match is None:
            return None

        emoji_id = int(match.group("id"))
        emoji_name = match.group("name")
        extension = "gif" if match.group("animated") else "png"
        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}?quality=lossless"
        return emoji_name, emoji_id, url

    def clean_name(self, name: str):
        name = name.strip()
        if not VALID_EMOJI_NAME_RE.fullmatch(name):
            return None
        return name

    async def create_emoji(self, guild: discord.Guild, emoji_text: str, name: str | None, reason: str):
        parsed = self.parse_custom_emoji(emoji_text)
        if parsed is None:
            raise ValueError("Send a custom Discord emoji like `<:name:id>` or `<a:name:id>`.")

        source_name, emoji_id, url = parsed
        final_name = self.clean_name(name or source_name)
        if final_name is None:
            raise ValueError("Emoji names must be 2-32 characters and can only use letters, numbers, and underscores.")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError("I could not download that emoji. Make sure it is a custom emoji I can access.")
                image_bytes = await response.read()

        if len(image_bytes) > 256 * 1024:
            raise ValueError("That emoji is too large for Discord's custom emoji limit.")

        return await guild.create_custom_emoji(
            name=final_name,
            image=image_bytes,
            reason=reason,
        ), emoji_id

    @commands.command(name="stealemoji", aliases=["steal"])
    @commands.guild_only()
    @commands.has_permissions(manage_emojis_and_stickers=True)
    @commands.bot_has_permissions(manage_emojis_and_stickers=True)
    async def steal_emoji_prefix(self, ctx, emoji: str, name: str | None = None):
        """Steal a custom emoji into this server."""
        try:
            created, source_id = await self.create_emoji(
                ctx.guild,
                emoji,
                name,
                reason=f"Emoji stolen by {ctx.author}",
            )
        except ValueError as error:
            embed = discord.Embed(title="Could Not Steal Emoji", description=str(error), color=Colors.DANGER)
            await ctx.send(embed=embed, delete_after=8)
            return
        except discord.Forbidden:
            embed = discord.Embed(
                title="Missing Permission",
                description="I need `Manage Expressions` / `Manage Emojis and Stickers` to add emojis.",
                color=Colors.DANGER,
            )
            await ctx.send(embed=embed, delete_after=8)
            return
        except discord.HTTPException as error:
            embed = discord.Embed(title="Discord Rejected It", description=str(error), color=Colors.DANGER)
            await ctx.send(embed=embed, delete_after=8)
            return

        embed = discord.Embed(
            title="Emoji Added",
            description=f"Added {created} as `:{created.name}:`",
            color=Colors.SUCCESS,
        )
        await ctx.send(embed=embed)

    @app_commands.command(name="steal_emoji", description="Add a custom emoji from another server to this server.")
    @app_commands.describe(
        emoji="Paste the custom emoji, like <:name:id> or <a:name:id>.",
        name="Optional new emoji name.",
    )
    @app_commands.default_permissions(manage_emojis_and_stickers=True)
    @app_commands.checks.has_permissions(manage_emojis_and_stickers=True)
    @app_commands.checks.bot_has_permissions(manage_emojis_and_stickers=True)
    async def steal_emoji_slash(self, interaction: discord.Interaction, emoji: str, name: str | None = None):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            created, _source_id = await self.create_emoji(
                interaction.guild,
                emoji,
                name,
                reason=f"Emoji stolen by {interaction.user}",
            )
        except ValueError as error:
            await interaction.followup.send(str(error), ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.followup.send(
                "I need `Manage Expressions` / `Manage Emojis and Stickers` to add emojis.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as error:
            await interaction.followup.send(f"Discord rejected it: {error}", ephemeral=True)
            return

        embed = discord.Embed(
            title="Emoji Added",
            description=f"Added {created} as `:{created.name}:`",
            color=Colors.SUCCESS,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Emojis(bot))
