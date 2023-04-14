import platform
from bot_config import settings
import discord
from discord.ext import commands
import logging
import asyncio
from general_cog import GeneralCog
from reports_cog import ReportsCog
from colorama import Back, Fore, Style
import time


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


# log_handler = logging.FileHandler(filename="bot.log", encoding='utf-8', mode='w')


async def init(bot):
    bot.help_command = BotHelp()
    await bot.add_cog(GeneralCog(bot))
    await bot.add_cog(ReportsCog(bot))
    # await bot.start(settings['token']) # взаимозаменяемая конструкция?
    # await bot.wait_until_ready()


if __name__ == "__main__":
    # initialize the bot
    intent = discord.Intents.default()
    intent.message_content = True

    bot = commands.Bot(command_prefix=settings['prefix'], intents=intent)

    @bot.event
    async def on_ready():
        prefix = (Fore.GREEN + time.strftime("%H:%M:%S UTC", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
        print(f'{prefix} Logged in as {Fore.YELLOW + str(bot.user)}')
        print(f'{prefix} Bot ID {Fore.YELLOW + str(bot.user.id)}')
        print(f'{prefix} Discord Version {Fore.YELLOW + discord.__version__}')
        print(f'{prefix} Python Version {Fore.YELLOW + str(platform.python_version())}')


    asyncio.run(init(bot))
    log_handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
    bot.run(settings['token'], log_handler=log_handler)
