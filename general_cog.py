from discord.ext import commands


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
    async def builds(self, ctx, category):
        """
        Показать сборки кораблей
        """
        pass

    @commands.command()
    async def preengineered(self, ctx):
        """
        Показать информацию о предмодифицированных модулях
        """
        pass

    @commands.command()
    async def macros(self, ctx):
        """
        Набор макросов
        """
        pass

    @commands.command()
    async def graphic(self, ctx, selection):
        """
        Вывести интересующий график
        """
        pass

