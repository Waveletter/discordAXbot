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
    participants = ui.TextInput(label='Ник:сборка;',
                                placeholder='Woruas:CH2mg2sg;komsiant:K5msc',
                                style=discord.TextStyle.long)
    timers = ui.TextInput(label='Фаза зоны-Время;',
                          placeholder='Фаза перехватчиков-01:50;Закрытие-49:50;1я гидра-01:34:21;2я гидра-01:52:43',
                          style=discord.TextStyle.long)
    spawns = ui.TextInput(label='Тип таргоида:Количество;',
                          placeholder='S:43;C:4;B:2;M:0;H:2',
                          style=discord.TextStyle.short)

    # По умолчанию инициализироваться из настроек
    def __init__(self, rep_manager=ReportManager(database=sqlite3.connect(settings['db']), tables=settings['tables']),
                 report_to_edit: int = None):
        super().__init__()
        self.manager = rep_manager
        self.report_to_edit = report_to_edit

    def set_place_plh(self, value: str) -> None:
        self.place.placeholder = value

    def set_zone_plh(self, value: str) -> None:
        self.zonetype.placeholder = value

    def set_participants_plh(self, value: str) -> None:
        self.participants.placeholder = value

    def set_timers_plh(self, value: str) -> None:
        self.timers.placeholder = value

    def set_spawns_plh(self, value: str) -> None:
        self.spawns.placeholder = value

    async def parse_args(self, *, user: str, guild: str, user_id: int, guild_id: int) -> ZoneReport:
        """Пропарсит переданные аргументы, вернёт ZoneReport"""
        # TODO: добавить проверку входных данных!!
        report = ZoneReport()
        report.user_id = user_id
        report.guild_id = guild_id
        report.date = datetime.datetime.now()
        report.user = user
        report.guild = guild
        report.zone_type = self.zonetype.value.strip().upper()
        report.place = self.place.value.strip().upper()

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

    async def push_to_db(self, report: Report, /) -> None:
        """Отправляет рапорт в менеджер для дальнейшей отправки в БД"""
        try:
            if self.report_to_edit is None:
                self.manager.add_report(report)
            else:
                self.manager.replace_report(report=report, index=self.report_to_edit,
                                            user_id=report.user_id, guild_id=report.guild_id)
        finally:
            print('Pushed a report')

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        a = await self.parse_args(user=interaction.user.nick, guild=interaction.guild.name,
                                  user_id=interaction.user.id, guild_id=interaction.guild.id)

        status = await self.push_to_db(a)

        # Чтобы инициализировать вебхук, нужно предварительно использовать response.defer()
        await interaction.response.defer()
        if self.report_to_edit is None:
            await interaction.followup.send(
                f'{interaction.user.mention} передал информацию о закрытии зоны в местности "{self.place.value}"')
        await interaction.followup.send(f'{len(self.manager.fetch_reports(user_id=interaction.user.id, guild_id=interaction.guild.id))} отчёт(а)(ов) ожидают подтверждения',
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

    @app_commands.command(name='report_zone', description='Команда для составления отчёта по зоне')
    async def report_zone(self, interaction: discord.Interaction) -> None:
        """Команда для составления отчёта по зоне"""
        await interaction.response.send_modal(ZoneReportModal(ReportManager(database=self.bot.db_conn)))

    @app_commands.command(name='show_reports', description='Выведет отчёты пользователя, подготовленные к отправке')
    async def show_reports(self, interaction: discord.Interaction) -> None:
        """Выведет отчёты пользователя, подготовленные к отправке"""
        stashed_reports = ReportManager().fetch_reports(user_id=interaction.user.id, guild_id=interaction.guild.id)
        await interaction.response.defer(ephemeral=True)
        if len(stashed_reports) == 0:
            await interaction.followup.send(f'У вас не подготовлено отчётов', ephemeral=True)
        else:
            index = 0
            for report in stashed_reports:
                await interaction.followup.send(f'Рапорт #{index}', embed=report.construct_embed(), ephemeral=True)
                index += 1

    @app_commands.command(name='amend_report', description='Изменяет состав отчёта')
    @app_commands.describe(category='Тип репорта')
    @app_commands.choices(category=[
        discord.app_commands.Choice(name='Zone', value='zone')
    ])
    async def amend_report(self, interaction: discord.Interaction, category: app_commands.Choice[str], index: int) -> None:
        """"""
        if (type(index) is not int) or index < 0 or index > len(ReportManager(self.bot.db_conn).fetch_reports(user_id=interaction.user.id, guild_id=interaction.guild.id)):
            await interaction.response.send_message('Плохой индекьс! Индекс подразумевает порядковый номер', ephemeral=True)
            return

        if category.value == 'zone':
            modal = ZoneReportModal(ReportManager(self.bot.db_conn), report_to_edit=index)
            old_report = ReportManager(self.bot.db_conn).fetch_report(user_id=interaction.user.id,
                                                                      guild_id=interaction.guild.id,
                                                                      index=index)
            if type(old_report) is not ZoneReport:
                await interaction.response.send_message('Неверный тип отчёта', ephemeral=True)
                print(f'uid: {interaction.user.id}, index: {index}, type: {type(index)}')
                print(f'{Fore.RED} Вернулся {type(old_report)}{Fore.RESET}')
                return
            #TODO: сделать методы конвертации в строку словарей
            modal.set_place_plh(old_report.place)
            modal.set_zone_plh(old_report.zone_type)
            srt = ''
            for i in old_report.participants.keys():
                srt += f'{i}:{old_report.participants[i]};'
            modal.set_participants_plh(srt)
            srt = ''
            for i in old_report.timings.keys():
                srt += f'{i}-{old_report.timings[i]};'
            modal.set_timers_plh(srt)
            srt = ''
            for i in old_report.tharg_counters.keys():
                srt += f'{i}:{old_report.tharg_counters[i]};'
            modal.set_spawns_plh(srt)

            await interaction.response.send_modal(modal)



