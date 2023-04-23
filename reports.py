import sqlite3
from typing import Type

import discord
from bot_config import settings
from colorama import Fore, Back, Style
from discord import Embed
import copy


class Queue:
    """Название говорит само за себя.. пришлось накалякать по-быстрому"""
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

    def full(self) -> bool:
        return len(self.list) == self.maxsize

    def __getitem__(self, item):
        return self.list[item]

    def __setitem__(self, key, value):
        self.list[key] = value
        return value


class Report:
    """Базовый класс отчёта"""
    def __init__(self, *, user: int = None, guild: int = None, date=None, table: str = None) -> None:
        self.user = user
        self.guild = guild
        self.date = date
        self.table = table

    def construct_embed(self) -> Embed:
        embed = discord.Embed()
        embed.add_field(name='Пользователь', value=self.user, inline=True)
        embed.add_field(name='Сервер', value=self.guild, inline=True)
        embed.add_field(name='Дата заполнения', value=self.date)
        return embed

    def write_to_db(self, cursor: sqlite3.Cursor) -> None:
        data = f'{self.user};{self.date};{self.guild}'
        cursor.execute(f"INSERT INTO {self.table} :dump", data)

    @property
    def user(self) -> int:
        return self._user

    @user.setter
    def user(self, name: int) -> None:
        self._user = name

    @property
    def guild(self) -> int:
        return self._guild

    @guild.setter
    def guild(self, ng: int) -> None:
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


class ZoneReport(Report):
    """Отчёт по зонам конфликта"""
    def __init__(self, *,  user: int = None, guild: int = None, date=None, zonetype: str = None,
                 wing_constitution: dict = None, timings: dict = None, tharg_count: dict = None,
                 table: str = 'zone_reports') -> None:
        super().__init__(user=user, guild=guild, date=date, table=table)
        self.zone_type = zonetype
        self.participants = wing_constitution
        self.timings = timings
        self.tharg_counters = tharg_count

    def write_to_db(self, cursor: sqlite3.Cursor) -> None:
        pass

    @property
    def zone_type(self) -> str:
        return self._zone_type

    @zone_type.setter
    def zone_type(self, zone: str) -> None:
        self._zone_type = zone

    @property
    def participants(self) -> Type[dict]:
        return self._participants

    @participants.setter
    def participants(self, new_p: dict) -> None:
        self._participants = copy.deepcopy(dict)

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
    #REPORT_LIMIT_PER_GUILD = 1000
    TOTAL_LIMIT = 3000

    def __init__(self, database: sqlite3.Connection, tables: dict = settings['tables'], reset: bool = False,
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
        #TODO: Переделать с Queue на что-то что даёт произвольный доступ.. брух.. но сохраняет поведение очереди..
        if report.guild not in self._storage.keys():
            self._storage.update({report.guild: dict()})
        if report.user not in self._storage[report.guild].keys():
            self._storage[report.guild].update({report.user: Queue(maxsize=self.REPORT_LIMIT_PER_USER)})

        report_queue = self._storage[report.guild][report.user]
        if not report_queue.full():
            report_queue.put(report)
            self._used_space += 1
        else:
            self.commit_report(user=report.user, guild=report.guild)

    def commit_report(self, *, user: int, guild: int, amount: int = 1) -> None:
        """

        :param user: user id
        :param guild: guild id
        :param amount: amount
        :return:
        """
        if amount > self._storage[guild][user].qsize():
            raise IndexError('Tried to commit too many reports')

        reports = self._storage[guild][user]
        for index in range(amount):
            reports.get().write_to_db(self.db_conn.cursor())
            self._used_space -= 1

    def fetch_reports(self, *, user: int, guild: int) -> tuple:
        return tuple(self._storage[guild][user])

    def fetch_guilds(self) -> tuple:
        return tuple(self._storage.keys())

    def fetch_guild_users(self, guild: int) -> tuple:
        return tuple(self._storage[guild].keys())

