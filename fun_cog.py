from discord.ext import commands
from discord import app_commands
import discord


class DebugCog(commands.Cog, name="Miscellaneous"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='followup')
    async def followup(self, interaction: discord.Interaction) -> None:
        """Тест нескольких ответов"""
        await interaction.response.defer()
        await interaction.followup.send("First followup")
        await interaction.followup.send("Second followup")
