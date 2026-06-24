import json
import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from config import Colors

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "verification_config.json"


class VerificationView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.success,
        custom_id="universal_bot:verify_button",
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.verify_member(interaction)


class Verification(commands.Cog):
    """Per-server verification gate."""

    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        self.bot.add_view(VerificationView(self))

    def load_config(self):
        if not DATA_PATH.exists():
            return {}

        try:
            with DATA_PATH.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError) as error:
            logger.error("Failed to load verification config: %s", error)
            return {}

    def save_config(self):
        with DATA_PATH.open("w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=2)

    def guild_config(self, guild_id):
        return self.config.get(str(guild_id), {})

    async def verify_member(self, interaction: discord.Interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return

        settings = self.guild_config(interaction.guild.id)
        role_id = settings.get("role_id")
        if not role_id:
            await interaction.response.send_message(
                "Verification is not set up in this server yet.",
                ephemeral=True,
            )
            return

        role = interaction.guild.get_role(role_id)
        if role is None:
            await interaction.response.send_message(
                "The verification role no longer exists. Ask an admin to run `/verification_setup` again.",
                ephemeral=True,
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message("You are already verified.", ephemeral=True)
            return

        try:
            await interaction.user.add_roles(role, reason="Verified with verification button")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I cannot give you the verified role. My role needs to be above it.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message("You are verified. Welcome in.", ephemeral=True)

    @app_commands.command(
        name="verification_setup",
        description="Create a verification channel and button for this server.",
    )
    @app_commands.describe(
        verified_role="Role members receive after pressing Verify.",
        channel_name="Name for the verification channel.",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    async def verification_setup(
        self,
        interaction: discord.Interaction,
        verified_role: discord.Role,
        channel_name: str = "verify",
    ):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        bot_member = guild.me
        if bot_member is None:
            await interaction.followup.send("I could not check my server permissions.", ephemeral=True)
            return

        if verified_role >= bot_member.top_role:
            await interaction.followup.send(
                "Move my role above the verified role, then run this command again.",
                ephemeral=True,
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            verified_role: discord.PermissionOverwrite(view_channel=False),
            bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }

        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel is None:
            channel = await guild.create_text_channel(
                channel_name,
                overwrites=overwrites,
                reason="Verification channel setup",
            )
        else:
            await channel.edit(overwrites=overwrites, reason="Verification channel setup")

        self.config[str(guild.id)] = {
            "channel_id": channel.id,
            "role_id": verified_role.id,
        }
        self.save_config()

        embed = discord.Embed(
            title="Server Verification",
            description="Press the button below to verify and unlock the server.",
            color=Colors.SUCCESS,
        )
        embed.set_footer(text=f"{guild.name} verification")

        await channel.send(embed=embed, view=VerificationView(self))
        await interaction.followup.send(
            f"Verification is ready in {channel.mention}. Members will receive {verified_role.mention}.",
            ephemeral=True,
        )

    @app_commands.command(
        name="verification_lockdown",
        description="Hide all channels from unverified members except the verification channel.",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    async def verification_lockdown(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        settings = self.guild_config(interaction.guild.id)
        channel_id = settings.get("channel_id")
        role_id = settings.get("role_id")
        if not channel_id or not role_id:
            await interaction.response.send_message(
                "Run `/verification_setup` first.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        verified_role = guild.get_role(role_id)
        verify_channel = guild.get_channel(channel_id)
        if verified_role is None or verify_channel is None:
            await interaction.followup.send("Verification settings are stale. Run `/verification_setup` again.")
            return

        updated = 0
        for channel in guild.channels:
            if channel.id == verify_channel.id:
                continue

            overwrite_everyone = channel.overwrites_for(guild.default_role)
            overwrite_verified = channel.overwrites_for(verified_role)
            overwrite_everyone.view_channel = False
            overwrite_verified.view_channel = True
            await channel.set_permissions(guild.default_role, overwrite=overwrite_everyone)
            await channel.set_permissions(verified_role, overwrite=overwrite_verified)
            updated += 1

        await interaction.followup.send(
            f"Locked {updated} channel(s). Unverified members can only see {verify_channel.mention}.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Verification(bot))
