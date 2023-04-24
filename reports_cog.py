from discord.ext import commands
from discord import app_commands
from discord import ui
import discord
import datetime
from bot_config import settings
from colorama import Fore, Back, Style
from reports import *


class ZoneReportModal(ui.Modal, title='Zone Report'):
    """
    Модалка для обработки репортов по зонам. Выдаёт окно взаимодействия, в которое записываются результаты закрытия зоны
    """
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

    # По умолчанию инициализироваться из настроек
    def __init__(self, rep_manager=ReportManager(database=sqlite3.connect(settings['db']), tables=settings['tables'])):
        super().__init__()
        self.manager = rep_manager

    async def parse_args(self, user_id: int, guild_id: int) -> ZoneReport:
        """Пропарсит переданные аргументы, вернёт ZoneReport"""
        # TODO: добавить проверку входных данных!!
        report = ZoneReport()
        report.user = user_id
        report.guild = guild_id
        report.date = datetime.datetime.now()
        report.zone_type = self.zonetype.value.strip().upper()

        participants = dict()
        for player in self.participants.value.strip().split(';'):
            pair = list(player.strip().split(':'))
            if len(pair) < 2:
                continue
            participants.update({pair[0].strip(): pair[1].strip()})  # добавить игрока и его билд в словарь
        report.participants = participants

        timings = dict()
        for item in self.timers.value.strip().split(';'):
            pair = item.strip().split('-')
            if len(pair) < 2:
                continue
            timings.update({pair[0].strip(): pair[1].strip()})
        report.timings = timings

        goids = dict()
        for item in self.spawns.value.strip().split(';'):
            pair = item.strip().split(':')
            if len(pair) < 2:
                continue
            goids.update({pair[0].strip(): int(pair[1].strip())})
        report.tharg_counters = goids

        return report

    async def push_to_db(self, report: Report) -> None:
        """Отправляет рапорт в менеджер для дальнейшей отправки в БД"""
        self.manager.add_report(report)

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        a = await self.parse_args(interaction.user.id, interaction.guild.id)
        status = await self.push_to_db(a)
        # Чтобы инициализировать вебхук, нужно предварительно использовать response.defer()
        await interaction.response.defer()
        await interaction.followup.send(
            f'{interaction.user.mention} передал информацию о закрытии зоны {self.place.value}')
        await interaction.followup.send(f'{len(self.manager.fetch_reports(user=interaction.user.id, guild=interaction.guild.id))} отчётов ожидают подтверждения',
                                                ephemeral=True)


class ReportsCog(commands.Cog, name='Reports'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def pstats(self, ctx, user=None) -> None:
        """
        Команда выводит статистику по указанному игроку
        """
        if user is None:
            await ctx.reply(f"Статистика {ctx.author.mention}")
        else:
            await ctx.reply(f"Статистика {user}")

    @app_commands.command(name='report_zone')
    async def report_zone(self, interaction: discord.Interaction) -> None:
        """Команда для составления отчёта по зоне"""
        await interaction.response.send_modal(ZoneReportModal(ReportManager(database=self.bot.db_conn)))



