from bot_config import settings
import discord
from discord.ext import commands


intent = discord.Intents.default()
intent.message_content = True

bot = commands.Bot(command_prefix=settings['prefix'], intents=intent)


@bot.command()
async def hello(ctx):
    author = ctx.message.author
    await ctx.send(f'Hello, {author.mention}')


bot.run(settings['token'])
