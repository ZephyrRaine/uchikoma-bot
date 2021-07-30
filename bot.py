import re
import json
import discord
import ogs
import config as config
from discord.ext import commands, tasks
bot = commands.Bot(command_prefix='!')

async def select_channel(game):
  channel_id = config.CHANNEL_ID
  """
  if game['ended']:
    sgf = await ogs.get_sgf_game(game['id'])
    if re.search(config.TAG, sgf, re.IGNORECASE):
      channel_id = config.TAGGED_CHANNEL_ID
  """
  return channel_id

async def notify_game_start(game):
  channel_id = config.CHANNEL_ID
  channel = bot.get_channel(int(channel_id))
  if channel:
    await channel.send(embed=GameStartEmbed(game))

async def notify_game_finished(game):
  channel_id = await select_channel(game)
  channel = bot.get_channel(int(channel_id))
  if channel:
    await channel.send(embed=GameFinishEmbed(game))

class GameStartEmbed(discord.Embed):
  """Embed sended when the scraper find a new game."""
  def __init__(self, game):
    id = game['id']
    bl = game['players']['black']['username']
    wh = game['players']['white']['username']
    color = 2895667
    emoji = 'crossed_swords'
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
    emoji = 'crossed_swords'
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
    self.check.start()
    self.scrap.start()

  def is_new_game(self, game):
    """check if a game is already cached"""
    list_ids = [player['id'] for player in self.players]
    time = json.loads(game['time_control_parameters'])
    live = time.get('speed') == 'live'
    cached = self.cache.get(game['id'])
    bl = game['players']['black']['id'] in list_ids
    wh = game['players']['white']['id'] in list_ids
    return live and not cached
    return bl and wh and live and not cached

  async def reset(self):
    """
    update player list and reset interator
    """
    self.players = await ogs.get_group_members(config.GROUP_ID)
    self.curr_idx = 0

  @tasks.loop(seconds=config.INTERVAL)
  async def scrap(self):
    """scrap next player or reset if the scraper has finished a cycle"""
    print(f'scraping {self.curr_idx}')
    return await self.reset() if self.curr_idx < 0 else await self.scrap_next_player()

  async def scrap_next_player(self):
    """pick the next player of the list and notify his starting games."""
    if self.curr_idx < len(self.players):
      self.curr_player = self.players[self.curr_idx]
      games = await ogs.get_active_games(self.curr_player['id'])
      self.curr_idx += 1
      new_games = [game for game in games if self.is_new_game(game)]
      for game in new_games:
        self.cache[game['id']] = game
        await notify_game_start(game)
    else:
      self.curr_idx = -1

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

  @scrap.before_loop
  async def before_scrap(self):
    await self.bot.wait_until_ready()

  @check.before_loop
  async def before_check(self):
    await self.bot.wait_until_ready()

@bot.event
async def on_ready():
  print('Uchikoma is ready to work !')

bot.add_cog(Scraper(bot))
bot.run(config.BOT_TOKEN)