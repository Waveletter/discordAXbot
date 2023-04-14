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

    @commands.command()
    async def report_zone(self, ctx, *args):
        """
        Команда по передаче
        """
        a = await self.parse_args(args)
        status = await self.push_to_db(a)
        await ctx.reply(f'{ctx.author.mention} доложил о закрытии {status}')

    @commands.command()
    async def personalstats(self, ctx, user=None):
        """
        Команда выводит статистику по указанному игроку; по умолчанию выводит статистику по вызвавшему команду
        """
        if user is None:
            await ctx.reply(f"Статистика {ctx.author.mention}")
        else:
            await ctx.reply(f"Статистика {user}")
