import platform
from bot_config import settings
import discord
from discord.ext import commands
import logging
import asyncio
from general_cog import GeneralCog
from reports_cog import ReportsCog
from fun_cog import DebugCog
from colorama import Back, Fore, Style
import time
import reports

import sqlite3


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

    def __init__(self, command_prefix, intent, help, db):
        super().__init__(command_prefix=command_prefix, intents=intent)
        self.help_command = help
        self.db_conn = sqlite3.connect(db)

    def add_cogs(self, cogs: list, guilds: discord.Object):
        for cog in cogs:
            asyncio.run(self.add_cog(cog, guilds=guilds))

    def add_a_cog(self, cog: commands.Cog, guilds: discord.Object):
        asyncio.run(self.add_cog(cog, guilds=guilds))

    async def on_ready(self):
        prefix = (Fore.GREEN + time.strftime("%H:%M:%S UTC", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
        print(f'{prefix} Logged in as {Fore.YELLOW + str(self.user)}')
        print(f'{prefix} Bot ID {Fore.YELLOW + str(self.user.id)}')
        print(f'{prefix} Discord Version {Fore.YELLOW + discord.__version__}')
        print(f'{prefix} Python Version {Fore.YELLOW + str(platform.python_version())}')


@commands.command(name='get_gid', hidden=True)
@commands.is_owner()
async def get_gid(ctx: commands.Context):
    print(f'{ctx.guild.id}')
    await ctx.reply('GID Sent')



if __name__ == "__main__":
    # initialize the bot

    intent = discord.Intents.default()
    intent.message_content = True
    bot = BotClient(command_prefix=settings['prefix'], intent=intent, help=BotHelp(), db=settings['db'])
    bot.add_cogs(cogs=[GeneralCog(bot), ReportsCog(bot)], guilds=settings['guilds'])
    bot.add_a_cog(cog=DebugCog(bot), guilds=[settings['guilds'][0]])
    bot.add_command(get_gid)

    log_handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
    report_manager = reports.ReportManager(database=bot.db_conn, tables=settings['tables'], guilds=settings['guilds'])

    for i in bot.tree.get_commands():
        print(f'{Fore.YELLOW + i.name} {Fore.WHITE + i.description + Fore.RESET}')

    bot.run(settings['token'], log_handler=log_handler)
