import sqlite3

class Pilot:
    def __init__(self, *, id: int = -1, gid: int = -1, name: str = None, nick: str = None, guild: str = None,
                 roles: list = None):
        self.id = id
        self.git = gid
        self.name = name
        self.nick = nick
        self.guild = guild
        self.roles = roles


class PilotStatistic:
    def __init__(self, *, date: str = None, ranks: list = None, zones: int = None, kills: dict = None,
                 achievements: list = None):
        self.date = date
        self.ranks = ranks
        self.zones = zones
        self.kills = kills
        self.achievements = achievements


class PilotHandler:
    def __init__(self):
        self.pilots = list()
        self.pilot_set = set()

    def add_pilot(self, *, pilot: Pilot = Pilot(),
                  stat: PilotStatistic = PilotStatistic()) -> None:

        self.pilots.append((pilot, stat))

    def load(self, table: str, db_cursor: sqlite3.Cursor):



