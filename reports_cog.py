from discord.ext import commands


class ReportsCog(commands.Cog, name='Reports'):
    def __init__(self, bot, db=None):
        self.bot = bot
        self.db = db

    async def parse_args(self, args):
        """TODO:Пропарсить переданные аргументы, проверить на ошибки, вернуть словарь"""
        pass

    async def push_to_db(self, content):
        """TODO:Отправить запрос в БД"""
        pass

    @commands.hybrid_command()
    async def report_zone(self, ctx):
        """
        Команда по передаче
        """
        a = await self.parse_args(None)
        status = await self.push_to_db(a)
        await ctx.reply(f'{ctx.author.mention} доложил о закрытии {status}')

    @commands.hybrid_command()
    async def pstats(self, ctx, user=None):
        """
        Команда выводит статистику по указанному игроку
        """
        if user is None:
            await ctx.reply(f"Статистика {ctx.author.mention}")
        else:
            await ctx.reply(f"Статистика {user}")
