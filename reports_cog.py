import discord
from discord.ext import commands
from discord import app_commands
from discord import ui
import discord


class ZoneReportModal(ui.Modal, title='Zone Report'):
    place = ui.TextInput(label='Система',
                         placeholder='Sol',
                         style=discord.TextStyle.short)
    zonetype = ui.TextInput(label='Зона конфликта',
                            placeholder='Малая интенсивность',
                            style=discord.TextStyle.short)
    participants = ui.TextInput(label='Ник:сборка',
                                placeholder='Woruas:CH2mg2sg;komsiant:K5msc',
                                style=discord.TextStyle.long)
    timers = ui.TextInput(label='Время закрытия',
                          placeholder='Фаза перехватчиков-01:50;Закрытие-49:50;1я гидра-01:34:21;2я гидра-01:52:43',
                          style=discord.TextStyle.long)
    spawns = ui.TextInput(label='Количество и тип таргоидов',
                          placeholder='S:43;C:4;B:2;M:0;H:2',
                          style=discord.TextStyle.short)


    def __init__(self, db=None):
        super().__init__()
        self.db = db

    async def parse_args(self):
        """TODO:Пропарсить переданные аргументы, проверить на ошибки, вернуть словарь"""
        pass

    async def push_to_db(self):
        """TODO:Отправить запрос в БД"""
        pass

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        a = await self.parse_args()
        status = await self.push_to_db()
        await interaction.response.send_message(f'{interaction.user} передал информацию о закрытии зоны {self.place}')


class ReportsCog(commands.Cog, name='Reports'):
    def __init__(self, bot, db=None):
        self.bot = bot
        self.db = db


    @commands.hybrid_command()
    async def pstats(self, ctx, user=None):
        """
        Команда выводит статистику по указанному игроку
        """
        if user is None:
            await ctx.reply(f"Статистика {ctx.author.mention}")
        else:
            await ctx.reply(f"Статистика {user}")

    @app_commands.command(name='report_zone')
    async def report_zone(self, interaction: discord.Interaction):
        """Команда для составления отчёта по зоне"""
        await interaction.response.send_modal(ZoneReportModal())
