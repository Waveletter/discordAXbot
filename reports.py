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
    def __init__(self, *, user: str = None, guild: str = None, user_id: int = None, guild_id: int = None, date=None, table: str = None) -> None:
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


class ZoneReport(Report):
    """Отчёт по зонам конфликта"""
    def __init__(self, *, user: str = None, guild: str = None, user_id: int = None, guild_id: int = None, date=None, zonetype: str = None,
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
            print(f'{Fore.CYAN}Report committed!')
            reports.get().write_to_db(self.db_conn.cursor())
            self._used_space -= 1

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


