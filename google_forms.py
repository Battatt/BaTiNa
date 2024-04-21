from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime as dt
from dotenv import load_dotenv
import os
import json


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
with open("sheet_info.json") as file:
    file = json.load(file)
    last_time = file["last_time"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
sample_spreadsheet_id = os.getenv('SPREADSHEET_ID')
SAMPLE_RANGE_NAME = "answers!A:I"


def main():
    """It sends message using discord webhook from a spreadsheet."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=sample_spreadsheet_id, range=SAMPLE_RANGE_NAME)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            print("No data found.")
            return
        send_flag = False
        questions = values[0]
        for row in values[1:]:
            if not send_flag:
                time_now = dt.strptime(row[0], "%d.%m.%Y %H:%M:%S").timestamp()
                if time_now > last_time:
                    send_flag = True
            if send_flag:
                webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK_URL"), username="BaTiNa submits",
                                         content="<@&1226488907084861450>")
                embed = DiscordEmbed(title="Заявка на администратора", color="03b2f8")
                embed.add_embed_field(name=questions[1], value=f"```{row[1]}```", inline=False)
                embed.add_embed_field(name=questions[2], value=f"```{row[2]}```", inline=False)
                embed.add_embed_field(name=questions[3], value=f"```{row[3]}```", inline=False)
                embed.add_embed_field(name=questions[4], value=f"```{row[4]}```", inline=False)
                embed.add_embed_field(name=questions[5], value=f"```{row[5]}```", inline=False)
                embed.add_embed_field(name=questions[6], value=f"```{row[6]}```", inline=False)
                embed.add_embed_field(name=questions[7], value=f"```{row[7]}```", inline=False)
                embed.add_embed_field(name=questions[8], value=f"```{row[8]}```", inline=False)
                embed.set_footer(text=f"Отправлено в {row[0]}")
                embed.set_timestamp()
                webhook.add_embed(embed)
                webhook.execute()
        with open("sheet_info.json", "w") as f:
            json.dump({"last_time": dt.strptime(values[-1][0], "%d.%m.%Y %H:%M:%S").timestamp()}, f)
    except HttpError as err:
        print(err)


if __name__ == "__main__":
    main()
