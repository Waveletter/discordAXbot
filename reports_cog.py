from discord.ext import commands
from discord import app_commands
from bot_config import settings
from colorama import Fore, Back, Style
from reports import *


class ReportButton(discord.ui.Button):
    """Базовый класс для создания кнопачек управления отчётами"""
    def __init__(self, *, style=discord.ButtonStyle.secondary, label=None,
                 disabled=False, custom_id=None, url=None, emoji=None, row=None,
                 user_id: int = None, guild_id: int = None,
                 report_manager: ReportManager = ReportManager(), index: int = None):
        super().__init__(style=style, label=label, disabled=disabled,
                         custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.uid = user_id
        self.gid = guild_id
        self.report_manager = report_manager
        self.index = index

    @property
    def uid(self) -> int:
        return self._uid
        
    @uid.setter
    def uid(self, uid: int):
        self._uid = uid

    @property
    def gid(self) -> int:
        return self._gid

    @gid.setter
    def gid(self, gid: int):
        self._gid = gid

    @property
    def report_manager(self) -> ReportManager:
        return self._repm

    @report_manager.setter
    def report_manager(self, repo: ReportManager):
        self._repm = repo


class CommitButton(ReportButton):
    """"""
    def __init__(self, *, user_id: int, guild_id: int, report_manager: ReportManager, index: int):
        super().__init__(user_id=user_id, guild_id=guild_id, style=discord.ButtonStyle.green, label='Commit Report',
                         report_manager=report_manager, index=index)

    async def callback(self, interaction: discord.Interaction) -> None:
        self.report_manager.commit_report(user=self.uid, guild=self.gid, index=self.index)
        await interaction.response.send_message(f'Отчёт #{self.index} игрока {interaction.user.mention} отправлен')


class AmendButton(ReportButton):
    """"""
    def __init__(self, *, user_id: int, guild_id: int, report_manager: ReportManager, index: int):
        super().__init__(user_id=user_id, guild_id=guild_id, style=discord.ButtonStyle.gray, label='Amend Report',
                         report_manager=report_manager, index=index)

    async def callback(self, interaction: discord.Interaction) -> None:
        report = self.report_manager.fetch_report(user_id=self.uid, guild_id=self.gid, index=self.index)
        modal = report.construct_modal()
        modal.set_index(self.index)

        await interaction.response.send_modal(modal)


class DeleteButton(ReportButton):
    """"""
    def __init__(self, *, user_id: int, guild_id: int, report_manager: ReportManager, index: int):
        super().__init__(user_id=user_id, guild_id=guild_id, style=discord.ButtonStyle.red, label='Delete Report',
                         report_manager=report_manager, index=index)

    async def callback(self, interaction: discord.Interaction) -> None:
        self.report_manager.remove_report(user_id=self.uid, guild_id=self.gid, index=self.index)
        await interaction.response.send_message(f'Отчёт #{self.index} игрока {interaction.user.mention} удалён')


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
        repo_man = ReportManager()
        stashed_reports = repo_man.fetch_reports(user_id=interaction.user.id, guild_id=interaction.guild.id)
        await interaction.response.defer(ephemeral=True)
        if len(stashed_reports) == 0:
            await interaction.followup.send(f'У вас не подготовлено отчётов', ephemeral=True)
        else:
            index = 0
            for report in stashed_reports:
                view = ui.View()
                view.add_item(CommitButton(user_id=interaction.user.id,
                                           guild_id=interaction.guild.id,
                                           report_manager=repo_man,
                                           index=index))
                view.add_item(AmendButton(user_id=interaction.user.id,
                                          guild_id=interaction.guild.id,
                                          report_manager=repo_man,
                                          index=index))
                view.add_item(DeleteButton(user_id=interaction.user.id,
                                           guild_id=interaction.guild.id,
                                           report_manager=repo_man,
                                           index=index))

                await interaction.followup.send(f'Рапорт #{index}', embed=report.construct_embed(),
                                                ephemeral=True, view=view)
                index += 1





