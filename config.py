import os

HOST = 'http://online-go.com/api/v1'

BOT_TOKEN = os.environ["BOT_TOKEN"]

# identifier of the OGS group to observe
GROUP_ID = os.environ["OGS_GROUP_ID"]

# identifier of the Discord channel that receives notifications
GAMES_CHANNEL_ID = os.environ["DISCORD_GAMES_CHANNEL_ID"]

DAILY_CHANNEL_ID = os.environ["DISCORD_DAILY_CHANNEL_ID"]

EVENT_CHANNEL_ID = os.environ["DISCORD_EVENT_CHANNEL_ID"]

GUILD_ID = os.environ["DISCORD_GUILD_ID"]

#MEMBERS_ROLE = os.environ["MEMBERS_ROLE"]

# check players in sec
INTERVAL = 5

# check running games in sec
CHECK_INTERVAL = 30

EVENT_CHECK_INTERVAL = 30

TAG = '#vague'