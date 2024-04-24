import disnake
from disnake.ext import commands
import os
import requests
from main import HOST, PORT
import requests
from random import randint
from dotenv import load_dotenv
import asyncio


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
admin_key = os.getenv("ADMIN_KEY")

bot = commands.InteractionBot(intents=disnake.Intents.all())


@bot.event
async def on_ready():
    print('Logged in:', bot.user)
    await bot.change_presence(
        status=disnake.Status.idle,
        activity=disnake.Streaming(name="Developin' QiQi v1.2-alpha", url="https://www.youtube.com/watch?v=-AuQZrUHjhg")
    )
    for guild in bot.guilds:
        print('Active in {}\n Member Count: {}'.format(guild.name, guild.member_count))


@bot.slash_command(description="Добавляет администратора на сайте",
                   guild_ids=[1226486189448495225],
                   options=[disnake.Option("id_пользователя", "ID пользователя на сайте",
                                           type=disnake.OptionType.integer, required=True)])
async def add_admin_site(inter: disnake.ApplicationCommandInteraction, **kwargs):
    await inter.response.defer(ephemeral=True)
    guild = bot.get_guild(1226486189448495225)
    owner_role = guild.get_role(1226488907084861450)
    if owner_role in inter.user.roles:
        response = requests.get(f"http://{HOST}:{PORT}/ds_bot_admin/{kwargs['id_пользователя']}/{admin_key}")
        if response.status_code == 200:
            return await inter.send(f"Пользователю с user_id: {kwargs['id_пользователя']} "
                                    f"успешно выдан статус администратора", ephemeral=True)
        return await inter.send(f"Ошибка при повышении статуса пользователя", ephemeral=True)
    return await inter.send(f"У вас недостаточно прав для данного действия", ephemeral=True)


@bot.slash_command(description="Добавляет администратора на cервере",
                   guild_ids=[1226486189448495225],
                   options=[disnake.Option("user", "Пользователь в Discord",
                                           type=disnake.OptionType.user, required=True)])
async def add_admin(inter: disnake.ApplicationCommandInteraction, **data):
    await inter.response.defer(ephemeral=True)
    guild = bot.get_guild(1226486189448495225)
    owner_role = guild.get_role(1226488907084861450)
    if owner_role in inter.user.roles:
        admin_site_role = guild.get_role(1226488797865316442)
        admin_role = guild.get_role(1226488167578730517)
        await data["user"].add_roles(admin_site_role, admin_role)
        return await inter.send(f"Успешно выдана роль {data["user"].mention}", ephemeral=True)
    return await inter.send(f"У вас недостаточно прав для данного действия", ephemeral=True)


@bot.slash_command(description="Лишает пользователя на сайте прав администратора",
                   guild_ids=[1226486189448495225],
                   options=[disnake.Option("id_пользователя", "ID пользователя на сайте",
                                           type=disnake.OptionType.integer, required=True)])
async def remove_admin_from_site(inter: disnake.ApplicationCommandInteraction, **kwargs):
    await inter.response.defer(ephemeral=True)
    guild = bot.get_guild(1226486189448495225)
    owner_role = guild.get_role(1226488907084861450)
    if owner_role in inter.user.roles:
        response = requests.get(f"http://{HOST}:{PORT}/remove_admin_ds/{kwargs['id_пользователя']}/{admin_key}")
        if response.status_code == 200:
            return await inter.send(f"Пользователь с user_id: {kwargs['id_пользователя']} "
                                    f"успешно лишен прав администратора", ephemeral=True)
        return await inter.send(f"Ошибка при повышении статуса пользователя", ephemeral=True)
    return await inter.send(f"У вас недостаточно прав для данного действия", ephemeral=True)


bot.run(os.getenv("DISCORD_BOT_TOKEN"))
