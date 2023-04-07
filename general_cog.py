from discord.ext import commands


class GeneralCog(commands.Cog, name="General"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """
        Проверка доступности бота
        """
        await ctx.send(f'{ctx.author.mention} Pong :ping_pong:')
