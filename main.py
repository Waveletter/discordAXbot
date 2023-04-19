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


class BotClient(commands.Bot):
    def __init__(self):
        intent = discord.Intents.default()
        intent.message_content = True
        super().__init__(command_prefix=settings['prefix'], intents=intent)
        self.help_command = BotHelp()
        asyncio.run(self.add_cog(GeneralCog(self)))
        asyncio.run(self.add_cog(ReportsCog(self)))

    async def on_ready(self):
        prefix = (Fore.GREEN + time.strftime("%H:%M:%S UTC", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
        print(f'{prefix} Logged in as {Fore.YELLOW + str(self.user)}')
        print(f'{prefix} Bot ID {Fore.YELLOW + str(self.user.id)}')
        print(f'{prefix} Discord Version {Fore.YELLOW + discord.__version__}')
        print(f'{prefix} Python Version {Fore.YELLOW + str(platform.python_version())}')


if __name__ == "__main__":
    # initialize the bot
    bot = BotClient()
    log_handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')

    @bot.tree.command(name='report_zone')
    async def report_zone(interaction: discord.Interaction):
        """Команда для составления отчёта по зоне"""
        await interaction.response.send_modal(ZoneReportModal())

    @bot.tree.command(name='builds')
    async def builds(interaction: discord.Interaction):

        """
        Показать сборки кораблей. Разрешены категории 'ax', 'trade', 'pvp', 'pve', 'explore'
        """
        args = interaction.command.parameters
        allowed_cats = ['ax', 'trade', 'pvp', 'pve', 'explore', 'all']
        category_description = {'ax': 'Сборки для противодействия таргоидам',
                                'trade': 'Сборки для торговых кораблей',
                                'pvp': 'Сборки для противодействия игрокам',
                                'pve': 'Сборки для противодействия NPC',
                                'explore': 'Сборки для исследования галактики'
                                }
        categories = list()
        if args.count('all') > 0:
            allowed_cats.pop(allowed_cats.index('all'))
            categories = allowed_cats
        elif len(args) == 0:
            categories.append('ax')
        else:
            for category in args:
                try:
                    categories.append(allowed_cats[allowed_cats.index(category.lower())])
                except ValueError:
                    await interaction.response.send_message(f'Категории {category} не существует. Разрешённые категории: {allowed_cats}')
                    return

        reply = dict()
        for i in categories:
            reply.update({i: list()})

        try:
            with open(settings['builds'], 'r') as builds:
                for line in builds:
                    for cat in reply.keys():
                        if line.startswith(cat):
                            reply[cat].append(
                                (line.strip().split(';'))[1:])  # append a pair of build name and build link
        except Exception as ex:
            await interaction.response.send_message(f'File error {ex}')
            return

        embed = discord.Embed(title='Сборки кораблей по категориям', color=discord.Color.dark_gold(),
                              description=f'Доступные категории: {allowed_cats}')
        for category in reply.keys():
            embed.add_field(name=f'{category.upper():-^40}', value=category_description[category], inline=False)
            for record in reply[category]:
                embed.add_field(name=record[0], value=f'[Link]({record[1]})', inline=False)

        await interaction.response.send_message(embed=embed)


    for i in bot.tree.get_commands():
        print(f'{Fore.YELLOW + i.name} {Fore.WHITE + i.description}')

    bot.run(settings['token'], log_handler=log_handler)
