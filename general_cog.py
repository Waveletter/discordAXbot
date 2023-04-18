import discord
from discord.ext import commands
import bot_config
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

    @commands.command(name='builds')


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
        #TODO: разобраться почему не распознаёт команды для синхронизации с сервером
        """Синхронизирует команды с текущим сервером"""
        print(f'Started syncing on {ctx.guild}')
        synced = await self.bot.tree.sync(guild=ctx.guild)
        print(f'{Fore.YELLOW + str(len(synced))} commands have been synced with {ctx.guild}')
        for cmd in synced:
            print(f'{Fore.CYAN + str(cmd) + Fore.RESET}')
        await ctx.reply('Sync complete')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def global_sync(self, ctx):
        """Синхронизирует команды глобально"""
        print(f'Started global syncing from command on {ctx.guild}')
        synced = await self.bot.tree.sync()
        print(f'{Fore.YELLOW + str(len(synced))} commands have been synced as global')
        for cmd in synced:
            print(f'{Fore.CYAN + str(cmd) + Fore.RESET}')
        await ctx.reply('Sync complete')
