import platform
from bot_config import settings
import discord
from discord.ext import commands
import logging
import logging.handlers
import asyncio
from general_cog import GeneralCog
from reports_cog import ReportsCog
from fun_cog import DebugCog
from colorama import Back, Fore, Style
import time
import reports

import sqlite3


class BotHelp(commands.MinimalHelpCommand):
    """
    Minimal class for printing help in embed
    """

    async def send_pages(self):
        destination = self.get_destination()
        embed = discord.Embed(color=discord.Color.dark_gold(), description='')
        for page in self.paginator.pages:
            embed.description += page
        await destination.send(embed=embed)


class BotClient(commands.Bot):

    def __init__(self, command_prefix, intent, help, db: str, repo_manager: reports.ReportManager = None,
                 logger: logging.Logger = None):
        super().__init__(command_prefix=command_prefix, intents=intent)
        self.help_command = help
        self.db_conn = sqlite3.connect(db)
        if repo_manager is not None:
            self.report_manager = repo_manager
        else:
            self.report_manager = reports.ReportManager(database=self.db_conn)
        self.logger = logger

    def add_cogs(self, cogs: list, guilds: discord.Object):
        for cog in cogs:
            asyncio.run(self.add_cog(cog, guilds=guilds))

    def add_a_cog(self, cog: commands.Cog, guilds: discord.Object):
        asyncio.run(self.add_cog(cog, guilds=guilds))

    def assign_report_manager(self, report_manager: reports.ReportManager):
        """

        :type report_manager: ReportManager
        """
        self.report_manager = report_manager

    def assign_logger(self, logger: logging.Logger):
        self.logger = logger

    async def on_ready(self):
        prefix = (Fore.GREEN + time.strftime("%H:%M:%S UTC", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
        print(f'{prefix} Logged in as {Fore.YELLOW + str(self.user) + Fore.RESET}')
        print(f'{prefix} Bot ID {Fore.YELLOW + str(self.user.id) + Fore.RESET}')
        print(f'{prefix} Discord Version {Fore.YELLOW + discord.__version__ + Fore.RESET}')
        print(f'{prefix} Python Version {Fore.YELLOW + str(platform.python_version()) + Fore.RESET}')


def initialize_db(db_conn: sqlite3.Connection, logger: logging.Logger):
    cursor = db_conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("CREATE TABLE IF NOT EXISTS guilds ("
                   "id INTEGER NOT NULL UNIQUE, "
                   "name TEXT NOT NULL, "
                   "PRIMARY KEY (id) "
                   ")")
    print(f'Initialized table \'{Fore.YELLOW} guilds {Fore.RESET}\'')
    logger.info("Initialized table 'guilds'")
    cursor.execute("CREATE TABLE IF NOT EXISTS roles("
                   "guild_id INTEGER NOT NULL, "
                   "name TEXT NOT NULL, "
                   "PRIMARY KEY (guild_id, name), "
                   "FOREIGN KEY (guild_id) REFERENCES guilds (id) ON DELETE CASCADE ON UPDATE CASCADE"
                   ")")
    print(f'Initialized table \'{Fore.YELLOW} roles {Fore.RESET}\'')
    logger.info("Initialized table 'roles'")
    cursor.execute("CREATE TABLE IF NOT EXISTS pilots("
                   "id INTEGER NOT NULL,"
                   "guild_id INTEGER NOT NULL UNIQUE,"
                   "name TEXT,"
                   "nickname TEXT,"
                   "guild_name TEXT,"
                   "roles TEXT,"
                   "PRIMARY KEY (id, guild_id),"
                   "FOREIGN KEY (guild_id, guild_name) REFERENCES guilds(id, name)"
                   " ON DELETE NO ACTION ON UPDATE CASCADE"
                   ")")
    print(f'Initialized table \'{Fore.YELLOW} pilots {Fore.RESET}\'')
    logger.info("Initialized table 'pilots'")
    cursor.execute("CREATE TABLE IF NOT EXISTS rank_kills("
                   "author_id INTEGER NOT NULL,"
                   "author_gid INTEGER NOT NULL,"
                   "rank TEXT,"
                   "video_link TEXT NOT NULL,"
                   "approved INTEGER NOT NULL,"
                   "PRIMARY KEY (author_id, author_gid, rank),"
                   "FOREIGN KEY (author_id, author_gid) REFERENCES pilots(id, guild_id) "
                   " ON DELETE NO ACTION ON UPDATE CASCADE"
                   ")")
    print(f'Initialized table \'{Fore.YELLOW} rank_kills {Fore.RESET}\'')
    logger.info("Initialized table 'rank_kills'")
    cursor.execute("CREATE TABLE IF NOT EXISTS pilot_statistics("
                   "record_id INTEGER,"
                   "pilot_id INTEGER,"
                   "pilot_gid INTEGER,"
                   "ranks TEXT,"
                   "zones_reported INTEGER,"
                   "date TEXT,"
                   "scout_kills INTEGER,"
                   "glaive_kills INTEGER,"
                   "cyclop_kills INTEGER,"
                   "basilisk_kills INTEGER,"
                   "medusa_kills INTEGER,"
                   "hydra_kills INTEGER,"
                   "achievements TEXT,"
                   "PRIMARY KEY (record_id),"
                   "FOREIGN KEY (pilot_id, pilot_gid) REFERENCES pilots(id, guild_id) "
                   " ON DELETE NO ACTION ON UPDATE CASCADE"
                   ")")
    print(f'Initialized table \'{Fore.YELLOW} pilot_statistics {Fore.RESET}\'')
    logger.info("Initialized table 'pilot_statistics'")
    cursor.execute("CREATE TABLE IF NOT EXISTS zone_reports("
                   "id INTEGER,"
                   "author_id INTEGER,"
                   "author_gid INTEGER,"
                   "system TEXT,"
                   "zone_type TEXT,"
                   "date TEXT,"
                   "wing_composition TEXT,"
                   "wing_size INTEGER,"
                   "timings TEXT,"
                   "completion_time TEXT,"
                   "time_per_hydra TEXT,"
                   "scouts INTEGER,"
                   "glaives INTEGER,"
                   "cyclops INTEGER,"
                   "basilisks INTEGER,"
                   "medusas INTEGER,"
                   "hydras INTEGER,"
                   "PRIMARY KEY (id),"
                   "FOREIGN KEY (author_id, author_gid) REFERENCES pilots(id, guild_id) "
                   " ON DELETE NO ACTION ON UPDATE CASCADE"
                   ")")
    print(f'Initialized table \'{Fore.YELLOW} zone_reports {Fore.RESET}\'')
    logger.info("Initialized table 'zone_reports'")
    cursor.execute("CREATE TABLE IF NOT EXISTS bgs("
                   "record_id INTEGER,"
                   "system TEXT,"
                   "author_id INTEGER,"
                   "author_gid INTEGER,"
                   "date TEXT,"
                   "system_state TEXT,"
                   "participants TEXT,"
                   "scouts_killed INTEGER,"
                   "glaives_killed INTEGER,"
                   "cyclopses_killed INTEGER,"
                   "basilisks_killed INTEGER,"
                   "medusas_killed INTEGER,"
                   "hydras_killed INTEGER,"
                   "orthruses_killed INTEGER,"
                   "low_zones_completed INTEGER,"
                   "med_zones_completed INTEGER,"
                   "high_zones_completed INTEGER,"
                   "very_high_zones_completed INTEGER,"
                   "station_zones_completed INTEGER,"
                   "big_station_zones_completed INTEGER,"
                   "ground_zones_completed INTEGER,"
                   "people_evacuated INTEGER,"
                   "supplies_delivered INTEGER,"
                   "samples_obtained INTEGER,"
                   "settlements_restored INTEGER,"
                   "PRIMARY KEY (record_id),"
                   "FOREIGN KEY (author_id, author_gid) REFERENCES pilots(id, guild_id)"
                   " ON DELETE NO ACTION ON UPDATE CASCADE"
                   ")")
    print(f'Initialized table \'{Fore.YELLOW} bgs {Fore.RESET}\'')
    logger.info("Initialized table 'bgs'")
    cursor.execute("CREATE TABLE IF NOT EXISTS builds("
                   "id INTEGER,"
                   "author_id INTEGER,"
                   "author_gid INTEGER,"
                   "notation TEXT,"
                   "name TEXT,"
                   "type TEXT,"
                   "link TEXT,"
                   "description TEXT,"
                   "PRIMARY KEY (id),"
                   "FOREIGN KEY (author_id, author_gid) REFERENCES pilots(id, guild_id)"
                   " ON DELETE NO ACTION ON UPDATE CASCADE"
                   ")")
    print(f'Initialized table \'{Fore.YELLOW} builds {Fore.RESET}\'')
    logger.info("Initialized table 'builds'")
    cursor.execute("CREATE TABLE IF NOT EXISTS notations("
                   "type TEXT,"
                   "short TEXT,"
                   "full_en TEXT,"
                   "full_ru TEXT,"
                   "PRIMARY KEY (type, short)"
                   ")")
    print(f'Initialized table \'{Fore.YELLOW} notations {Fore.RESET}\'')
    logger.info("Initialized table 'notations'")


if __name__ == "__main__":
    # initialize the bot

    intent = discord.Intents.default()
    intent.message_content = True
    bot = BotClient(command_prefix=settings['prefix'], intent=intent, help=BotHelp(), db=settings['db'])
    bot.add_cogs(cogs=[GeneralCog(bot), ReportsCog(bot)], guilds=settings['guilds'])
    bot.add_a_cog(cog=DebugCog(bot), guilds=[settings['guilds'][0]])

    # log_handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    logging.getLogger('discord.http').setLevel(logging.INFO)

    log_handler = logging.handlers.RotatingFileHandler(
        filename="bot.log", encoding='utf-8',
        maxBytes=64 * 1024 * 1024,  # 64 MB
        backupCount=5
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    bot.assign_logger(logger)

    for i in bot.tree.get_commands():
        print(f'{Fore.YELLOW + i.name} {Fore.WHITE + i.description + Fore.RESET}')

    initialize_db(bot.db_conn, bot.logger)

    bot.run(settings['token'], log_handler=None)
