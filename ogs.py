from aiohttp import request
import localconfig as config

async def get_player(player_id):
  """get player details"""
  uri = f'{config.HOST}/players/{player_id}/'
  async with request('GET', uri) as res:
    return await res.json()

async def get_game(game_id):
  """get game details"""
  uri = f'{config.HOST}/games/{game_id}/'
  async with request('GET', uri) as res:
    return await res.json()

async def get_sgf_game(game_id):
  """get game's sgf. Assumes that game is finished"""
  uri = f'{config.HOST}/games/{game_id}/sgf'
  async with request('GET', uri) as res:
    return await res.text()

async def get_active_games(player_id):
  """get player's active games (no matter time setting)"""
  async def acc(uri, result):
    async with request('GET', uri) as res:
      body = await res.json()
      next = body.get('next')
      result += [game for game in body['results']]
      return await acc(next, result) if next else result
  uri = f'{config.HOST}/players/{player_id}/games/?ended__isnull=true'
  result = await acc(uri, [])
  return result

async def get_group_members(group_id):
  """get all group's players"""
  async def acc(uri, result):
    async with request('GET', uri) as res:
      body = await res.json()
      next = body['next']
      result += [member['user'] for member in body['results']]
      return await acc(next, result) if next else result
  uri = f'{config.HOST}/groups/{group_id}/members/'
  result = await acc(uri, [])
  return result