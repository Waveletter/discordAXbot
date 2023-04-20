import platform
from bot_config import settings
import discord
from discord.ext import commands
import logging
import asyncio
from general_cog import GeneralCog
from reports_cog import ReportsCog, ZoneReportModal
from colorama import Back, Fore, Style
import time
import interactions


class BotHelp (commands.MinimalHelpCommand):
    """
    Minimal class for printing help in embed
    """
    async def send_pages(self):
        destination = self.get_destination()
        embed = discord.Embed(color=discord.Color.dark_gold(), description='')
        for page in self.paginator.pages:
            embed.description += page
        await destination.send(embed=embed)


class BotClient(commands.Bot):
    def __init__(self,):
        intent = discord.Intents.default()
        intent.message_content = True
        super().__init__(command_prefix=settings['prefix'], intents=intent)
        self.help_command = BotHelp()

    def add_cogs(self, Cogs, Guilds):
        for cog in Cogs:
            asyncio.run(self.add_cog(cog, guilds=Guilds))


    async def on_ready(self):
        prefix = (Fore.GREEN + time.strftime("%H:%M:%S UTC", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
        print(f'{prefix} Logged in as {Fore.YELLOW + str(self.user)}')
        print(f'{prefix} Bot ID {Fore.YELLOW + str(self.user.id)}')
        print(f'{prefix} Discord Version {Fore.YELLOW + discord.__version__}')
        print(f'{prefix} Python Version {Fore.YELLOW + str(platform.python_version())}')


if __name__ == "__main__":
    # initialize the bot
    bot = BotClient()
    bot.add_cogs(Cogs=[GeneralCog(bot), ReportsCog(bot)], Guilds=[discord.Object(id=1090316883770740766)])
    log_handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')

    @bot.tree.command(name='report_zone')
    async def report_zone(interaction: discord.Interaction):
        """Команда для составления отчёта по зоне"""
        await interaction.response.send_modal(ZoneReportModal())

    for i in bot.tree.get_commands():
        print(f'{Fore.YELLOW + i.name} {Fore.WHITE + i.description}')

    bot.run(settings['token'], log_handler=log_handler)
