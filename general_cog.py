import discord
from discord.ext import commands
from discord import app_commands
from bot_config import settings
from colorama import Fore


class GeneralCog(commands.Cog, name="General"):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def ping(self, ctx):
        """
        Проверка доступности бота
        """
        await ctx.reply(f'Pong :ping_pong:')

    #@commands.hybrid_command()
    async def preengineered(self, ctx):
        """
        Показать информацию о предмодифицированных модулях
        """
        pass

    #@commands.hybrid_command()
    async def macros(self, ctx):
        """
        Набор макросов
        """
        pass

    #@commands.command()
    async def graphic(self, ctx, selection):
        """
        Вывести интересующий график
        """
        pass

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, ctx):
        """Синхронизирует команды, предназначенные текущему серверу, с текущим сервером"""
        print(f'Started syncing on {ctx.guild}')
        synced = await self.bot.tree.sync(guild=ctx.guild)
        print(f'{Fore.YELLOW + str(len(synced))} commands have been synced with {ctx.guild}')
        for cmd in synced:
            print(f'{Fore.CYAN + str(cmd) + Fore.RESET}')
        await ctx.message.delete(delay=5)
        await ctx.reply(f'Sync complete; Synced {str(len(synced))} commands with current server')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def global_sync(self, ctx):
        """Синхронизирует команды глобально"""
        print(f'Started global syncing from command on {ctx.guild}')
        synced = await self.bot.tree.sync()
        print(f'{Fore.YELLOW + str(len(synced))} commands have been synced as global')
        for cmd in synced:
            print(f'{Fore.CYAN + str(cmd) + Fore.RESET}')
        await ctx.message.delete(delay=5)
        await ctx.reply(f'Global sync complete; Synced {str(len(synced))} globally')

    @app_commands.command(name='builds')
    @app_commands.describe(category='Вывести список сборок кораблей')
    @app_commands.choices(category=[
        discord.app_commands.Choice(name='AX', value='ax'),
        discord.app_commands.Choice(name='Trade', value='trade'),
        discord.app_commands.Choice(name='PVP', value='pvp'),
        discord.app_commands.Choice(name='PVE', value='pve'),
        discord.app_commands.Choice(name='Exploration', value='explore'),
        discord.app_commands.Choice(name='All', value='all')
    ])
    async def builds(self, interaction: discord.Interaction, category: app_commands.Choice[str]):
        """
        Показать сборки кораблей. Разрешены категории 'ax', 'trade', 'pvp', 'pve', 'explore'
        """
        args = [category.value]

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

        cat_str = ''    #Просто для красивого вывода категорий
        for i in allowed_cats:
            cat_str += ' ' + i

        embed = discord.Embed(title='Сборки кораблей по категориям', color=discord.Color.dark_gold(),
                              description=f'Доступные категории: {cat_str}')
        for category in reply.keys():
            embed.add_field(name=f'{category.upper():-^40}', value=category_description[category], inline=False)
            for record in reply[category]:
                embed.add_field(name=record[0], value=f'[Link]({record[1]})', inline=False)

        await interaction.response.send_message(embed=embed)
