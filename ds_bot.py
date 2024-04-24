from disnake.ext import commands
from dotenv import load_dotenv
from main import HOST, PORT
import os
import time
import disnake
import requests

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


@bot.slash_command(description="Добавляет администратора на сайте",
                   guild_ids=[1226486189448495225],
                   options=[disnake.Option("id_пользователя", "ID пользователя на сайте",
                                           type=disnake.OptionType.integer, required=True)])
async def add_site_admin(inter: disnake.ApplicationCommandInteraction, **data):
    await inter.response.defer(ephemeral=True)
    guild = bot.get_guild(1226486189448495225)
    owner_role = guild.get_role(1226488907084861450)
    if owner_role in inter.user.roles:
        response = requests.get(f"http://{HOST}:{PORT}/ds_bot_admin/{data['id_пользователя']}/{admin_key}")
        if response.status_code == 200:
            return await inter.send(f"Пользователю с user_id: {data['id_пользователя']} "
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
        return await inter.send(f"Успешно выданы роли {data['user'].mention}", ephemeral=True)
    return await inter.send(f"У вас недостаточно прав для данного действия", ephemeral=True)


@bot.slash_command(description="Лишает пользователя на сайте прав администратора",
                   guild_ids=[1226486189448495225],
                   options=[disnake.Option("id_пользователя", "ID пользователя на сайте",
                                           type=disnake.OptionType.integer, required=True)])
async def remove_site_admin(inter: disnake.ApplicationCommandInteraction, **data):
    await inter.response.defer(ephemeral=True)
    guild = bot.get_guild(1226486189448495225)
    owner_role = guild.get_role(1226488907084861450)
    if owner_role in inter.user.roles:
        response = requests.get(f"http://{HOST}:{PORT}/remove_admin_ds/{data['id_пользователя']}/{admin_key}")
        if response.status_code == 200:
            return await inter.send(f"Пользователь с user_id: {data['id_пользователя']} "
                                    f"успешно лишен прав администратора", ephemeral=True)
        return await inter.send(f"Ошибка при понижении статуса пользователя", ephemeral=True)
    return await inter.send(f"У вас недостаточно прав для данного действия", ephemeral=True)


@bot.slash_command(description="Убирает администратора на сервере",
                   guild_ids=[1226486189448495225],
                   options=[disnake.Option("user", "Пользователь в Discord",
                                           type=disnake.OptionType.user, required=True)])
async def remove_admin(inter: disnake.ApplicationCommandInteraction, **data):
    await inter.response.defer(ephemeral=True)
    guild = bot.get_guild(1226486189448495225)
    owner_role = guild.get_role(1226488907084861450)
    if owner_role in inter.user.roles:
        admin_site_role = guild.get_role(1226488797865316442)
        admin_role = guild.get_role(1226488167578730517)
        await data["user"].remove_roles(admin_site_role, admin_role)
        return await inter.send(f"Успешно забраны роли {data['user'].mention}", ephemeral=True)
    return await inter.send(f"У вас недостаточно прав для данного действия", ephemeral=True)


@bot.slash_command(description="Информация о товаре",
                   guild_ids=[1226486189448495225],
                   options=[disnake.Option("название_товара", "Название товара на сайте",
                                           type=disnake.OptionType.string, required=False),
                            disnake.Option("id_товара", "ID товара на сайте",
                                           type=disnake.OptionType.integer, required=False),
                            ])
async def product_info(inter: disnake.ApplicationCommandInteraction, **data):
    await inter.response.defer()
    if len(data) == 0:
        return await inter.send(
            embed=disnake.Embed(title="Ошибка. Необходимо указать один из параметров", color=0x2b2d31)
        )
    response = requests.get(f"http://{HOST}:{PORT}/api/items")
    if response.status_code != 200:
        return await inter.send(
            embed=disnake.Embed(title="Ошибка при получении товаров", color=0x2b2d31)
        )
    all_products = response.json()["items"]
    product_id, product_name = data.get("id_товара", None), data.get("название_товара", None)
    for product in all_products:
        if product["id"] == product_id or product_name.lower() in \
                [product["category"].lower(), product["description"].lower(), product["name"].lower()]:
            return await inter.send(
                embed=disnake.Embed(title=product["name"],
                                    description=product["description"],
                                    color=0x03b2f8
                                    ).add_field(
                    name="Количество", value=product["amount"]
                                    ).add_field(
                    name="Категория", value=product["category"]
                                    ).add_field(
                    name="Видимость", value=product["is_visible"], inline=False
                                    ).add_field(
                    name="Цена", value=f"{product['price']} ₽"
                ), ephemeral=False)
    return await inter.send(
        embed=disnake.Embed(title="Ничего не найдено", color=0x2b2d31)
    )


@bot.slash_command(description="Отображает ping бота",
                   guild_ids=[1226486189448495225])
async def ping(inter: disnake.ApplicationCommandInteraction):
    await inter.send(embed=disnake.Embed(
        title="🏓 Pong!",
        description=f"The bot latency is {round(bot.latency * 1000)}ms.",
        color=0x03b2f8
    ), ephemeral=True)


bot.run(os.getenv("DISCORD_BOT_TOKEN"))
