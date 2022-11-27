import datetime
import time
import pytz
from aiohttp import request
import config


async def get_scheduled_games():
  """get player details"""
  uri = f'https://openstudyroom.org/calendar/get-game-appointment-events/'
  async with request('GET', uri) as result:
    j = await result.json()
    j.sort(key=lambda x: x["start"])
    games = []
    for g in j:
        print(g)
        date = datetime.datetime.strptime(g['start'], '%Y-%m-%d %H:%M:%S')

        if date.date() == datetime.datetime.today().date() \
        and g["divisions"][0]["league"]["community"]["pk"] == 13 :
            games.append(f'Groupe :regional_indicator_{g["divisions"][0]["name"].lower()}: : {g["users"][0]["name"]} vs {g["users"][1]["name"]} à <t:{int((date.replace(tzinfo=pytz.timezone("UTC"))).timestamp())}:t>')

    return games