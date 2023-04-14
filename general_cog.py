import discord
from discord.ext import commands
import bot_config


class GeneralCog(commands.Cog, name="General"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """
        Проверка доступности бота
        """
        await ctx.reply(f'Pong :ping_pong:')

    @commands.command()
    async def builds(self, ctx, *args):
        """
        Показать сборки кораблей. Разрешены категории 'ax', 'trade', 'pvp', 'pve', 'explore'
        """
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
                    await ctx.reply(f'Категории {category} не существует. Разрешённые категории: {allowed_cats}')
                    return

        reply = dict()
        for i in categories:
            reply.update({i: list()})

        try:
            with open(bot_config.settings['builds']) as builds:
                for line in builds:
                    for cat in reply.keys():
                        if line.startswith(cat):
                            reply[cat].append(
                                (line.strip().split(';'))[1:])  # append a pair of build name and build link
        except Exception as ex:
            await ctx.reply(f'File error {ex}')
            return

        embed = discord.Embed(title='Сборки кораблей по категориям', color=discord.Color.dark_gold(),
                              description=f'Доступные категории: {allowed_cats}')
        for category in reply.keys():
            embed.add_field(name=f'{category.upper():-^40}', value=category_description[category], inline=False)
            for record in reply[category]:
                embed.add_field(name=record[0], value=f'[Link]({record[1]})', inline=False)

        await ctx.reply(embed=embed)

    #@commands.command()
    async def preengineered(self, ctx):
        """
        Показать информацию о предмодифицированных модулях
        """
        pass

    #@commands.command()
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
