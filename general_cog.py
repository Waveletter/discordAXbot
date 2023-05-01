import discord
from discord.ext import commands
from discord import app_commands
from bot_config import settings
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

    # @commands.hybrid_command()
    async def preengineered(self, ctx):
        """
        Показать информацию о предмодифицированных модулях
        """
        pass

    # @commands.hybrid_command()
    async def macros(self, ctx):
        """
        Набор макросов
        """
        pass

    # @commands.command()
    async def graphic(self, ctx, selection):
        """
        Вывести интересующий график
        """
        pass

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, ctx):
        """Синхронизирует команды, предназначенные текущему серверу, с текущим сервером"""
        print(f'Started syncing on {ctx.guild}')
        synced = await self.bot.tree.sync(guild=ctx.guild)
        print(f'{Fore.YELLOW + str(len(synced))} commands have been synced with {ctx.guild}')
        for cmd in synced:
            print(f'{Fore.CYAN + str(cmd) + Fore.RESET}')
        await ctx.message.delete(delay=5)
        await ctx.reply(f'Sync complete; Synced {str(len(synced))} commands with current server')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def global_sync(self, ctx):
        """Синхронизирует команды глобально"""
        print(f'Started global syncing from command on {ctx.guild}')
        synced = await self.bot.tree.sync()
        print(f'{Fore.YELLOW + str(len(synced))} commands have been synced as global')
        for cmd in synced:
            print(f'{Fore.CYAN + str(cmd) + Fore.RESET}')

        await ctx.message.delete(delay=5)
        await ctx.reply(f'Global sync complete; Synced {str(len(synced))} globally')

    @app_commands.command(name='builds')
    @app_commands.describe(category='Вывести список сборок кораблей')
    @app_commands.choices(category=[
        discord.app_commands.Choice(name='AX', value='ax'),
        discord.app_commands.Choice(name='Trade', value='trade'),
        discord.app_commands.Choice(name='PVP', value='pvp'),
        discord.app_commands.Choice(name='PVE', value='pve'),
        discord.app_commands.Choice(name='Exploration', value='explore'),
        discord.app_commands.Choice(name='All', value='all')
    ])
    async def builds(self, interaction: discord.Interaction, category: app_commands.Choice[str]):
        """
        Показать сборки кораблей. Разрешены категории 'ax', 'trade', 'pvp', 'pve', 'explore'
        """
        args = [category.value]

        allowed_cats = ['ax', 'trade', 'pvp', 'pve', 'explore', 'all']
        category_description = {'ax': 'Сборки для противодействия таргоидам',
                                'trade': 'Сборки для торговых кораблей',
                                'pvp': 'Сборки для противодействия игрокам',
                                'pve': 'Сборки для противодействия NPC',
                                'explore': 'Сборки для исследования галактики'
                                }
        categories = list()
        if args.count('all') > 0:
            allowed_cats.pop(allowed_cats.index('all'))
            categories = allowed_cats
        elif len(args) == 0:
            categories.append('ax')
        else:
            for category in args:
                try:
                    categories.append(allowed_cats[allowed_cats.index(category.lower())])
                except ValueError:
                    await interaction.response.send_message(
                        f'Категории {category} не существует. Разрешённые категории: {allowed_cats}',
                        delete_after=settings['timeout'])
                    return

        reply = dict()
        for i in categories:
            reply.update({i: list()})

        try:
            with open(settings['builds'], 'r') as builds:
                for line in builds:
                    for cat in reply.keys():
                        if line.startswith(cat):
                            reply[cat].append(
                                (line.strip().split(';'))[1:])  # append a pair of build name and build link
        except Exception as ex:
            await interaction.response.send_message(f'File error {ex}', delete_after=settings['timeout'])
            return

        embed = discord.Embed(title='Сборки кораблей по категориям', color=discord.Color.dark_gold())
        for category in reply.keys():
            embed.add_field(name=f'{category.upper():-^40}', value=category_description[category], inline=False)
            # todo: добавить обработку описания
            for record in reply[category]:
                if len(record) > 2:
                    # символ \u2060 Неразрывный пробел с нулевой шириной для того, чтобы дискорд не сокращал строку
                    embed.add_field(name=record[2], value=f'[{record[0]}]({record[1]})', inline=False)
                else:
                    embed.add_field(name=record[0], value=f'[Link to the build]({record[1]})', inline=False)

        await interaction.response.send_message(embed=embed, delete_after=settings['timeout'])

    def parse_ship(self, ship: str) -> tuple:
        with open(settings['notations'], mode='r', encoding='utf-8') as notation_file:
            for line in notation_file:
                if line.startswith('ship') and line.find(ship) >= 0:
                    stroke = line.strip().split(';')
                    if len(stroke) >= 4:
                        return stroke[2], stroke[3]
                    else:
                        return stroke[2], None
        raise ValueError(f'Введённого корабля {ship} не обнаружено')

    def parse_weapon(self, weapon: str) -> tuple:
        amount = ''
        size = None
        wtype = None
        wepname = ''

        for character in weapon:
            if character.isdigit():
                amount += character
                continue
            if size is None:
                size = character
                continue
            if wtype is None:
                wtype = character
                continue
            wepname += character

        if any((amount == '', size is None, wtype is None, wepname == '')):
            raise ValueError(f'Не получилось распарсить {weapon}')

        amount = int(amount)

        print(amount, size, wtype, wepname, weapon)

        with open(settings['notations'], mode='r', encoding='utf-8') as notation_file:
            for line in notation_file:
                stroke = line.strip().split(';')
                if type(size) is str and line.startswith('size') and stroke[1] == size:
                    if len(stroke) >= 4:
                        size = stroke[2:4]
                    else:
                        size = [stroke[2], 'None']
                    continue
                if type(wtype) is str and line.startswith('type') and stroke[1] == wtype:
                    if len(stroke) >= 4:
                        wtype = stroke[2:4]
                    else:
                        wtype = [stroke[2], 'None']
                    continue
                if type(wepname) is str and line.startswith('weapon') and stroke[1] == wepname:
                    if len(stroke) >= 4:
                        wepname = stroke[2:4]
                    else:
                        wepname = [stroke[2], 'None']
                    continue

        if any(map(lambda x: type(x) == str, [wtype, wepname, size])):
            print(wtype, wepname, size)
            raise ValueError(f'{weapon} не был найден в файле')

        parsed = (f'{size[0]} {wtype[0]} {wepname[0]}', f'{size[1]} {wtype[1]} {wepname[1]}')

        return amount, parsed[0], parsed[1]


    def decipher_notation(self, notation: str, lang: str = 'en') -> discord.Embed:
        weapon_list = list()
        embed = discord.Embed()

        index_ship = 0
        for character in notation:
            if character.islower():
                index_ship += 1
            else:
                break

        ship_name = notation[index_ship:index_ship+3]
        print(f'Ship Name: {ship_name}')

        index = index_ship+3 #нужно распарсить типы орудий
        str_length = len(notation)
        while index < str_length:
            weapon = ''
            if notation[index].isdigit():
                weapon += notation[index]
                index += 1
            while index < str_length and notation[index].isdigit():
                weapon += notation[index]
                index += 1
            while index < str_length and notation[index].isalpha():
                weapon += notation[index]
                index += 1
            weapon_list.append(weapon)

        try:
            ship_name, ship_name_ru = self.parse_ship(ship_name)
        except ValueError as err:
            print(err)
            raise
        try:
            resulting_list = list()
            for weapon in weapon_list:
                amount, name, name_ru = self.parse_weapon(weapon.lower())
                resulting_list.append((amount, name, name_ru))
        except ValueError as err:
            print(err)
            raise
        if lang == 'en':
            embed.title = f'Расшифровка нотации {notation}'
            embed.add_field(name='Наименование корабля:', value=f'```{ship_name}```')
            str = '```'
            for weapon in resulting_list:
                str += f'{weapon[0]}x {weapon[1]}\n'
                #str += u'\n\u2060' #для сохранения пустой строки (избежание её обрезания)
            str += '```'
            embed.add_field(name='Вооружение:', value=str)
        elif lang == 'ru':
            embed.title = f'Расшифровка нотации {notation}'
            embed.add_field(name='Наименование корабля:', value=f'```{ship_name_ru}```')
            str = '```'
            for weapon in resulting_list:
                str += f'{weapon[0]}x {weapon[2]}\n'
                #str += u'\n\u2060'  # для сохранения пустой строки (избежание её обрезания)
            str += '```'
            embed.add_field(name='Вооружение:', value=str)
        else:
            print(lang)
            raise AttributeError(f'Неправильный езык {lang}')

        return embed

    def notation_help(self) -> discord.Embed:
        embed = discord.Embed(title="Помощь по краткой нотации")
        embed.description = f'Краткая нотация используется для быстрой записи сборки корабля. Она состоит из' \
                            f' краткого имени корабля и перечисления его вооружения.\n' \
                            f'```\n' \
                            f'<shipmods><SHIP><weapon1><weapon2>...' \
                            f'```' \
                            f'По соглашению, тип корабля пишется полностью заглавными буквами, остальное пишется прописью\n' \
                            f'Каждый тип оружия записывается следуюшим способом: количество, класс(размер), тип, наименование\n' \
                            f'```\n' \
                            f'<№><size><type><name>' \
                            f'```' \
                            f'Пример записи:' \
                            f'```\n' \
                            f'KRT3mfmsc2mftvb' \
                            f'```' \
                            f'Что в развёрнутом виде означает "Krait MK II с тремя средними фиксированными ' \
                            f'модифицированными осколочными орудиями и двумя средними лучами с теплосбросом"'
        embed.set_footer(text=f'Для справки по существующим нотациям вызовите иную категорию')
        return embed

    def get_category_embed(self, name: str, category: str, lang: str = 'en') -> discord.Embed:
        embed = discord.Embed()
        notation_list = list()
        with open(settings['notations'], mode='r', encoding='utf-8') as notation_file:
            for line in notation_file:
                if line.startswith(category):
                    notation_list.append(line.strip().split(';')[1:])
        embed.title = f'Категория: {name}'

        descr = '```'
        for notation in notation_list:
            if len(notation) >= 3:
                descr += f'{notation[0]:^5} - {notation[1]}\n'
                #descr += f'{notation[0]:^5} - {notation[1]}({notation[2]})\n'
            elif len(notation) == 2:
                descr += f'{notation[0]:^5} - {notation[1]}\n'
            else:
                print(notation)
                print(notation_list)
                raise KeyError('Плохая строка')
        descr += '```'
        embed.description = descr

        return embed

    @app_commands.command(name='notation', description='Расшифровка краткой нотации')
    @app_commands.describe(ntype='Тип нотации')
    @app_commands.choices(ntype=[
        discord.app_commands.Choice(name='Ships', value='ship'),
        discord.app_commands.Choice(name='Weapons', value='weapon'),
        discord.app_commands.Choice(name='Modifiers', value='mods'),
        discord.app_commands.Choice(name='Help', value='help'),
        discord.app_commands.Choice(name='Decipher', value='decipher')
    ])
    @app_commands.describe(notation='Строка нотации для расшифровки (может быть пустой)')
    @app_commands.describe(lang='Язык вывода (по умолчанию английский)')
    async def notation(self, interaction: discord.Interaction, ntype: app_commands.Choice[str],
                       notation: str = None, lang: str = 'en') -> None:
        if ntype.value == 'help':
            await interaction.response.send_message(embed=self.notation_help(), ephemeral=True,
                                                    delete_after=settings['timeout'])
            return

        if ntype.value == 'decipher':
            if notation is None:
                await interaction.response.send_message(f'Введите нотацию!', ephemeral=True,
                                                        delete_after=settings['timeout'])
                return

            try:
                await interaction.response.send_message(embed=self.decipher_notation(notation, lang), ephemeral=True,
                                                        delete_after=settings['timeout'])
            except ValueError as err:
                await interaction.response.send_message(f'Ошибка в нотации {notation}; {err}',
                                                        ephemeral=True,
                                                        delete_after=settings['timeout'])
            except AttributeError as err:
                await interaction.response.send_message(f'Неправильно выбран язык {lang}',
                                                        ephemeral=True,
                                                        delete_after=settings['timeout'])
                print(err)
            return

        if ntype.value == 'mods':
            types = ['size', 'type']
        else:
            types = [ntype.value]

        await interaction.response.defer(ephemeral=True)
        for itype in types:
            embed = self.get_category_embed(ntype.name, itype, lang)
            await interaction.followup.send(embed=embed, ephemeral=True)
