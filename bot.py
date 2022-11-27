import asyncio
import datetime
import re
import json
import discord
import pytz

import ogs
import config
from discord.ext import commands, tasks
import time

import osr

intents = discord.Intents.all()
bot = commands.Bot(intents=intents, command_prefix='/')


async def notify_game_start(game):
    channel = bot.get_channel(int(config.GAMES_CHANNEL_ID))
    if channel:
        await channel.send(embed=GameStartEmbed(game))


async def notify_game_finished(game):
    channel = bot.get_channel(int(config.GAMES_CHANNEL_ID))
    if channel:
        await channel.send(embed=GameFinishEmbed(game))

async def notify_daily_event(events, shell):
    channel = bot.get_channel(int(config.DAILY_CHANNEL_ID))
    if channel and (len(events) > 0 or len(shell) >0) :
      await channel.send(embed=DailyEmbed(events, shell))

async def notify_event(event, role):
    channel = bot.get_channel(int(config.EVENT_CHANNEL_ID))
    if channel:
        await channel.send(f'<@&{role}>', embed=EventEmbed(event))


class EventEmbed(discord.Embed):
    def __init__(self, event):
        color = 0xff1774
        title = f'{event.name} commence dans 30 minutes !'
        description = f'{event.description}'
        footer = f'{event.channel if event.channel else event.location}'
        super().__init__(color=color, title=title, description=description)
        self.set_footer(text=footer)


class DailyEmbed(discord.Embed):
    """Daily recap embed"""

    def __init__(self, events, shell):
        color = 0xff1774
        title = f'Bonjour SITS, au programme de ce <t:{int(time.time())}:D> :'
        super().__init__(color= color, title=title)
        if len(events) > 0:
            eventsField = '\n'.join(events)
            self.add_field(name=":calendar: Évènements SITS :", value=eventsField, inline=False)

        if len(shell) > 0:
            gamesField = '\n'.join(shell)
            self.add_field(name=":shell: Parties The Shell :", value=gamesField, inline=False)


class GameStartEmbed(discord.Embed):
    """Embed sended when a game starts"""

    def __init__(self, game):
        id = game['id']
        bl = game['players']['black']['username']
        wh = game['players']['white']['username']
        color = 2895667
        emoji = 'shell' if re.search(config.TAG, game['name'], re.IGNORECASE) else 'crossed_swords'
        link = f'https://online-go.com/game/{id}/'
        link_label = f'{bl} vs {wh}'

        desc = f':{emoji}: [{link_label}]({link}) a commencé !'
        super().__init__(color=color, description=desc)


class GameFinishEmbed(discord.Embed):
    """Embed sended when a game is finished"""

    def __init__(self, game):
        game_id = game['id']
        bl = game['players']['black']['username']
        wh = game['players']['white']['username']
        wh_lost = game['white_lost']
        color = 2895667
        winner = bl if wh_lost else wh
        loser = wh if wh_lost else bl
        emoji = 'shell' if re.search(config.TAG, game['name'], re.IGNORECASE) else 'crossed_swords'
        link = f'https://online-go.com/game/{game_id}/'
        label = f'[{bl} vs {wh}]({link}) est terminé !'
        res = game['outcome']
        win_color = 'noir' if wh_lost else 'blanc'
        desc = f':{emoji}: {label}\n\n'
        resTxt = f'{winner} ({win_color}) gagne par '
        if res == 'Resignation':
            resTxt += 'abandon'
        elif res == 'Timeout':
            resTxt += 'le temps'
        else:
            resTxt += res
        super().__init__(color=color, description=desc)
        self.set_footer(text=resTxt)
        self.set_image(url=f'{config.HOST}/games/{game_id}/png')


class Scraper(commands.Cog):
    """
    The scraper has 2 independent tasks that run forever :
      - scrap: browse the player's list and get active games for each of them.
        when a live game is found, we notify the channel and cache the game.
      - check: request details for each cached games and see if they are finished.
    """

    def __init__(self, bot):
        self.bot = bot
        self.curr_idx = -1
        self.curr_player = None
        self.players = []
        self.cache = {}
        self.cachedEvents = {}

    async def start(self):
        print("OK START")

        self.check.start()
        self.scrap.start()
        self.daily.start()
        self.event_check.start()
        print("OK LETS GO")

    def is_new_game(self, game):
        """check if a game is already cached"""
        list_ids = [player['id'] for player in self.players]
        time = json.loads(game['time_control_parameters'])
        live = time.get('speed') == 'live'
        cached = self.cache.get(game['id'])
        paused = "gamedata" in game and 'paused_since' in game['gamedata']
        bl = game['players']['black']['id'] in list_ids
        wh = game['players']['white']['id'] in list_ids
        return bl and wh and live and not cached and not paused

    async def reset(self):
        """
        update player list and reset interator
        """
        self.players = await ogs.get_group_members(config.GROUP_ID)
        self.curr_idx = 0

    async def scrap_next_player(self):
        """pick the next player of the list and notify his starting games."""
        if self.curr_idx < len(self.players):
            self.curr_player = self.players[self.curr_idx]
            games = await ogs.get_active_games(self.curr_player['id'])
            self.curr_idx += 1
            new_games = [game for game in games if self.is_new_game(game)]
            for game in new_games:
                self.cache[game['id']] = game
                print(f'Notifying game')
                await notify_game_start(game)
        else:
            self.curr_idx = -1

    @tasks.loop(seconds=config.INTERVAL)
    async def scrap(self):
        """scrap next player or reset if the scraper has finished a cycle"""
        print(f'scraping {self.curr_idx}')
        return await self.reset() if self.curr_idx < 0 else await self.scrap_next_player()

    @tasks.loop(seconds=config.CHECK_INTERVAL)
    async def check(self):
        """browse all cached games and notify finished ones"""
        print(f'checking {len(self.cache)}')
        for game_id in list(self.cache):
            game = await ogs.get_game(game_id)
            if game['ended']:
                self.cache.pop(game_id)
                if game['outcome'] != 'Cancellation':
                    await notify_game_finished(game)

    @tasks.loop(seconds=config.EVENT_CHECK_INTERVAL)
    async def event_check(self):
        print("checking events")

        guild_id = self.bot.get_guild(int(config.GUILD_ID))
        role = guild_id.get_role('777434394998472704')

        events = guild_id.scheduled_events
        for e in events:
            print(e.start_time.astimezone(pytz.timezone("Europe/Paris")))
            print(datetime.datetime.now().astimezone(pytz.timezone("Europe/Paris")))
            print(e.start_time.astimezone(pytz.timezone("Europe/Paris")) - datetime.datetime.now().astimezone(pytz.timezone("Europe/Paris")))
            td = e.start_time.astimezone(pytz.timezone("Europe/Paris")) - datetime.datetime.now().astimezone(pytz.timezone("Europe/Paris"))
            if (e.start_time.date() == datetime.datetime.today().date())\
            and (td <= datetime.timedelta(minutes=30)) and td > datetime.timedelta() \
            and not self.cachedEvents.get(e.id) :
                self.cachedEvents[e.id] = e
                await notify_event(e, '777434394998472704')

        for e in list(self.cachedEvents):
            if self.cachedEvents.get(e).start_time.astimezone(pytz.timezone("Europe/Paris")) < datetime.datetime.now().astimezone(pytz.timezone("Europe/Paris")):
                self.cachedEvents.pop(e)
        print(f"done checking events, {len(self.cachedEvents)} cached events")

    #@tasks.loop(time=datetime.time(hour=7, minute=0, second=0))
    @tasks.loop(seconds=10)
    async def daily(self):
        """get all planned events for the day"""
        print("getting today events")
        print(config.GUILD_ID)
        guild_id = self.bot.get_guild(int(config.GUILD_ID))
        events = guild_id.scheduled_events

        print(len(events))
        ev = []
        for e in events:
             if(e.start_time.date() == datetime.datetime.today().date()):
                ev.append(f'{e.name} à <t:{int(time.mktime(e.start_time.astimezone(pytz.timezone("Europe/Paris")).timetuple()))}:t>, dans {e.channel if e.location is None else e.location}')

        games = await osr.get_scheduled_games()

        await notify_daily_event(ev, games)

    @scrap.before_loop
    async def before_scrap(self):
        await self.bot.wait_until_ready()

    @check.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @daily.before_loop
    async def before_daily(self):
        await self.bot.wait_until_ready()

    @event_check.before_loop
    async def before_event_check(self):
        await self.bot.wait_until_ready()


@bot.event
async def on_ready():
    print('Uchikoma is ready to work')
    await cog.start()


async def main():
    # start the client
    async with bot:
        await bot.add_cog(cog)
        await bot.start(config.BOT_TOKEN)


cog = Scraper(bot)
asyncio.run(main())
