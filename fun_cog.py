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

        @commands.hybrid_command()  # из ReportsCog
        async def pstats(self, ctx, user=None) -> None:
            """
            Команда выводит статистику по указанному игроку
            """
            if user is None:
                await ctx.reply(f"Статистика {ctx.author.mention}")
            else:
                await ctx.reply(f"Статистика {user}")
