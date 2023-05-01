import sqlite3
import typing

import discord
from bot_config import settings
from colorama import Fore, Back, Style
from discord import Embed
import copy
from discord import ui
import datetime

ZoneReport = typing.NewType('ZoneReport', None)  # Forward declaration


class Queue:
    """"""

    def __init__(self, *, maxsize):
        super().__init__()
        self.maxsize = maxsize
        self.list = list()

    def __iter__(self):
        return self.list.__iter__()

    def put(self, item) -> None:
        if len(self.list) < self.maxsize:
            self.list.append(item)
        else:
            raise IndexError("Queue is overflowing! (Trying to insert item in a full queue)")

    def get(self) -> object:
        return self.list.pop(0)

    def pop(self, index: int) -> object:
        return self.list.pop(index)

    def full(self) -> bool:
        return len(self.list) == self.maxsize

    def __getitem__(self, item):
        return self.list[item]

    def __setitem__(self, key, value):
        self.list[key] = value
        return value

    def qsize(self):
        return len(self.list)


class Report:
    """Базовый класс отчёта"""

    def __init__(self, *, user: str = None, guild: str = None, user_id: int = None, guild_id: int = None, date=None,
                 table: str = None) -> None:
        self.user_id = user_id
        self.guild_id = guild_id
        self.date = date
        self.table = table
        self.user = user
        self.guild = guild

    def construct_embed(self) -> Embed:
        embed = discord.Embed()
        embed.add_field(name='Пользователь', value=self.user, inline=True)
        embed.add_field(name='Сервер', value=self.guild, inline=True)
        embed.add_field(name='Дата заполнения', value=self.date)
        return embed

    def construct_modal(self) -> ui.Modal:
        modal = ui.Modal()
        modal.add_item(ui.TextInput(label='Пользователь', placeholder=self.user, style=discord.TextStyle.short))
        modal.add_item(ui.TextInput(label='Сервер', placeholder=self.guild, style=discord.TextStyle.short))
        modal.add_item(ui.TextInput(label='Дата заполнения', placeholder=self.date, style=discord.TextStyle.short))

        async def placeholder():
            pass

        modal.on_submit = placeholder
        return modal

    def write_to_db(self, cursor: sqlite3.Cursor) -> None:
        data = f'{self.user_id};{self.date};{self.guild_id}'
        cursor.execute(f"INSERT INTO {self.table} :dump", data)

    @property
    def user_id(self) -> int:
        return self._user

    @user_id.setter
    def user_id(self, name: int) -> None:
        self._user = name

    @property
    def guild_id(self) -> int:
        return self._guild

    @guild_id.setter
    def guild_id(self, ng: int) -> None:
        self._guild = ng

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, data) -> None:
        self._date = data

    @property
    def table(self) -> str:
        return self._table

    @table.setter
    def table(self, tb: str) -> None:
        self._table = tb


class MetaSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ReportManager(object, metaclass=MetaSingleton):
    """
    Менеджер репортов. Отвечает за итоговую выгрузку в БД, отвечает паттерну Singleton
    (при помощи наследования от метакласса)
    """

    REPORT_LIMIT_PER_USER = 20  # Ограничение по количеству хранимых в памяти репортов для того чтобы не забить всю
    # память репортами
    # REPORT_LIMIT_PER_GUILD = 1000
    TOTAL_LIMIT = 3000

    def __init__(self, database: sqlite3.Connection = None, tables: dict = settings['tables'], reset: bool = False,
                 guilds: list = settings['guilds']) -> None:
        """
        Инициализация менеджера
        :param database: Соединение с БД SQLite sqlite3.Connection
        :param tables: Словарь имён таблиц и конструкторов таблиц
        :param guilds: Список серверов
        """
        self._used_space = 0
        self._storage = dict()

        self.db_conn = database
        self.tables = tables.keys()
        cur = self.db_conn.cursor()
        db_tables = cur.execute("SELECT name FROM sqlite_master").fetchall()

        if reset is True:
            for db_table in db_tables:
                if db_table not in tables:
                    cur = self.db_conn.cursor()

        for table in tables:
            if table not in db_tables:
                settings['tables'][table](self.db_conn)  # В словаре должен быть передан валидный метод создания таблицы
                print(f'Created table {Fore.YELLOW + table}')

        print(f'Initialized Report Manager')

    def add_report(self, report: Report) -> None:
        """Добавить отчёт в очередь"""
        if report.guild_id not in self._storage.keys():
            self._storage.update({report.guild_id: dict()})
        if report.user_id not in self._storage[report.guild_id].keys():
            self._storage[report.guild_id].update({report.user_id: Queue(maxsize=self.REPORT_LIMIT_PER_USER)})

        report_queue = self._storage[report.guild_id][report.user_id]
        if not report_queue.full():
            report_queue.put(report)
            self._used_space += 1
            print(f'{Fore.BLUE}Report added! {report.guild_id} {Fore.RESET}')
        else:
            self.commit_report(user=report.user_id, guild=report.guild_id)

    def commit_report(self, *, user: int, guild: int, index: int = 0, amount: int = 1) -> Report:
        """
        Отправляет репорт в БД
        :param user: user id
        :param guild: guild id
        :param amount: amount
        :param index: report index
        :return: last report committed
        """
        if amount > self._storage[guild][user].qsize():
            raise IndexError('Tried to commit too many reports')

        reports = self._storage[guild][user]
        last_committed = None
        for index in range(index, index + amount):
            print(f'{Fore.CYAN}Report committed!')
            last_committed = reports.pop(index).write_to_db(self.db_conn.cursor())
            self._used_space -= 1

        return last_committed

    def replace_report(self, *, report: Report, index: int, user_id: int, guild_id: int) -> Report:
        """Заменяет отчёт"""
        if not self.is_present(uid=user_id, gid=guild_id):
            raise KeyError('No such reports')
        if index < 0 or index > len(self.fetch_reports(user_id=user_id, guild_id=guild_id)):
            raise IndexError('Index error')
        self._storage[guild_id][user_id][index] = report
        return report

    def remove_report(self, *, index: int, user_id: int, guild_id: int) -> Report:
        """Удаляет рапорт из очереди"""
        if not self.is_present(uid=user_id, gid=guild_id):
            raise KeyError('No such reports')
        if index < 0 or index > len(self.fetch_reports(user_id=user_id, guild_id=guild_id)):
            raise IndexError('Index error')
        return self._storage[guild_id][user_id].pop(index)

    def fetch_reports(self, *, user_id: int, guild_id: int) -> tuple:
        """
        Возвращает сохранённые в кеше отчёты пользователя
        :param user_id: user_id, ИД пользователя дискорд
        :param guild_id: guild_id, ИД сервера
        :return: кортеж с отчётами, если такой пользователь присутствует, и пустой кортеж если нет
        """
        if self.is_present(user_id, guild_id) is True:
            return tuple(self._storage[guild_id][user_id])
        else:
            return tuple()

    def fetch_report(self, *, user_id: int, guild_id: int, index: int) -> Report:
        if self.is_present(user_id, guild_id) is True:
            return self._storage[guild_id][user_id][index]
        else:
            print(f'Did not find the report')
            return None

    def fetch_guilds(self) -> tuple:
        return tuple(self._storage.keys())

    def fetch_guild_users(self, guild: int) -> tuple:
        return tuple(self._storage[guild].keys())

    def is_present(self, uid: int, gid: int) -> bool:
        """Проверяет, существует ли очередь отчётов для данного пользователя"""
        try:
            test = self._storage[gid][uid]
        except KeyError:
            print(f'Did not find reports with guild id {gid}, user id {uid}')
            return False
        return True


class ZoneReportModal(ui.Modal, title='Zone Report'):
    """
    Модалка для обработки репортов по зонам. Выдаёт окно взаимодействия, в которое записываются результаты закрытия зоны
    """
    place = ui.TextInput(label='Система',
                         default='Sol',
                         style=discord.TextStyle.short)
    zonetype = ui.TextInput(label='Зона конфликта',
                            default='Малая интенсивность',
                            style=discord.TextStyle.short)
    participants = ui.TextInput(label='Ник:сборка;',
                                default='Woruas:CH2mg2sg;komsiant:K5msc',
                                style=discord.TextStyle.long)
    timers = ui.TextInput(label='Фаза зоны-Время;',
                          default='Фаза перехватчиков-01:50;Закрытие-49:50;1я гидра-01:34:21;2я гидра-01:52:43',
                          style=discord.TextStyle.long)
    spawns = ui.TextInput(label='Тип таргоида:Количество;',
                          default='Scout:43;Cyclops:4;Basilisk:2;Medusa:0;Hydra:2',
                          style=discord.TextStyle.short)

    # По умолчанию инициализироваться из настроек
    def __init__(self, rep_manager=ReportManager(database=sqlite3.connect(settings['db']), tables=settings['tables']),
                 report_to_edit: int = None, uid: int = None, gid: int = None):
        super().__init__()
        self.manager = rep_manager
        self.report_to_edit = report_to_edit
        self.user_id = uid
        self.guild_id = gid

    def set_index(self, value: int) -> None:
        self.report_to_edit = value

    def set_uid(self, uid: int) -> None:
        self.user_id = uid

    def set_gid(self, gid: int) -> None:
        self.guild_id = gid

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

    def set_place(self, value: str) -> None:
        self.place.default = value

    def set_zone(self, value: str) -> None:
        self.zonetype.default = value

    def set_participants(self, value: str) -> None:
        self.participants.default = value

    def set_timers(self, value: str) -> None:
        self.timers.default = value

    def set_spawns(self, value: str) -> None:
        self.spawns.default = value

    async def parse_args(self, *, user: str, guild: str, user_id: int, guild_id: int, date: datetime.datetime = None) -> ZoneReport:
        """Пропарсит переданные аргументы, вернёт ZoneReport"""
        # TODO: добавить проверку входных данных!!
        report = ZoneReport()
        report.user_id = user_id
        report.guild_id = guild_id
        if date is None:
            report.date = datetime.datetime.now()
        else:
            report.date = date
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
        date = None
        if self.report_to_edit is not None:
            report = self.manager.fetch_report(user_id=self.user_id, guild_id=self.guild_id, index=self.report_to_edit)
            name = report.user
            gname = report.guild
            uid = report.user_id
            gid = report.guild_id
            date = report.date
        else:
            if interaction.user.nick is None:
                name = interaction.user.name
            else:
                name = f'{interaction.user.nick}({interaction.user.name})'
            uid = interaction.user.id
            gid = interaction.guild.id
            gname = interaction.guild.name

        report = await self.parse_args(user=name, guild=gname,
                                  user_id=uid, guild_id=gid, date=date)

        await self.push_to_db(report)

        # Чтобы инициализировать вебхук, нужно предварительно использовать response.defer()
        await interaction.response.defer()
        if self.report_to_edit is None:
            await interaction.followup.send(
                f'{interaction.user.mention} передал информацию о закрытии зоны в местности "{self.place.value}"')
        else:
            await interaction.followup.send(f'Отчёт #{self.report_to_edit} игрока {report.user} исправлен')
        await interaction.followup.send(
            f'{len(self.manager.fetch_reports(user_id=interaction.user.id, guild_id=interaction.guild.id))} отчёт(а)(ов) ожидают подтверждения',
            ephemeral=True)


class ZoneReport(Report):
    """Отчёт по зонам конфликта"""

    def __init__(self, *, user: str = None, guild: str = None, user_id: int = None, guild_id: int = None, date=None,
                 zonetype: str = None,
                 wing_constitution: dict = None, timings: dict = None, tharg_count: dict = None,
                 table: str = 'zone_reports', place: str = None) -> None:
        super().__init__(user=user, guild=guild, user_id=user_id, guild_id=guild_id, date=date, table=table)
        self.zone_type = zonetype
        self.participants = wing_constitution
        self.timings = timings
        self.tharg_counters = tharg_count
        self.place = place

    def write_to_db(self, cursor: sqlite3.Cursor) -> None:
        pass

    def construct_embed(self) -> Embed:
        embed = discord.Embed()
        embed.add_field(name='Пользователь', value=self.user, inline=True)
        embed.add_field(name='Сервер', value=self.guild)
        embed.add_field(name='Дата заполнения', value=self.date)
        embed.add_field(name='Место', value=self.place)
        embed.add_field(name='Тип зоны', value=self.zone_type)
        if len(self.participants.keys()) == 0:
            embed.add_field(name='Участники', value='Не удалось разобрать строку')
        else:
            val_str = ''
            for player in self.participants.keys():
                val_str += f'{player}({self.participants[player]});\n'
            embed.add_field(name='Участники', value=val_str)
        if len(self.timings.keys()) < 3:
            embed.add_field(name='Временные отсечки', value='Не удалось разобрать строку')
        else:
            val_str = ''
            for timetype in self.timings.keys():
                val_str += f'{timetype}: {self.timings[timetype]} ;\n'
            embed.add_field(name='Временные отсечки', value=val_str)
        if len(self.tharg_counters.keys()) == 0:
            embed.add_field(name='Замеченные таргоиды', value='Не удалось разобрать строку')
        else:
            val_str = ''
            for tharg_type in self.tharg_counters.keys():
                val_str += f'{tharg_type} : {self.tharg_counters[tharg_type]} ;\n'
            embed.add_field(name='Замеченные таргоиды', value=val_str)
        return embed

    def construct_modal(self) -> ZoneReportModal:
        modal = ZoneReportModal()
        modal.title = f'Отчёт от {self.date}'
        modal.set_place(self.place)
        modal.set_zone(self.zone_type)
        srt = ''
        for i in self.participants.keys():
            srt += f'{i}:{self.participants[i]};'
        modal.set_participants(srt)
        srt = ''
        for i in self.timings.keys():
            srt += f'{i}-{self.timings[i]};'
        modal.set_timers(srt)
        srt = ''
        for i in self.tharg_counters.keys():
            srt += f'{i}:{self.tharg_counters[i]};'
        modal.set_spawns(srt)

        return modal

    @property
    def zone_type(self) -> str:
        return self._zone_type

    @zone_type.setter
    def zone_type(self, zone: str) -> None:
        self._zone_type = zone

    @property
    def participants(self) -> dict:
        return self._participants

    @participants.setter
    def participants(self, new_p: dict) -> None:
        self._participants = copy.deepcopy(new_p)

    @property
    def timings(self) -> dict:
        return self._timings

    @timings.setter
    def timings(self, times: dict) -> None:
        self._timings = copy.deepcopy(times)

    @property
    def tharg_counters(self) -> dict:
        return self._tharg_counters

    @tharg_counters.setter
    def tharg_counters(self, tc: dict) -> None:
        self._tharg_counters = copy.deepcopy(tc)

    @property
    def place(self) -> str:
        return self._place

    @place.setter
    def place(self, value: str) -> None:
        self._place = value
