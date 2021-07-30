import os

HOST = 'http://online-go.com/api/v1'

BOT_TOKEN = os.environ["BOT_TOKEN"]

# identifier of the OGS group to observe
GROUP_ID = os.environ["OGS_GROUP_ID"]

# identifier of the Discord channel that receives notifications
CHANNEL_ID = os.environ["DISCORD_CHANNEL_ID"]

# check players in sec
INTERVAL = 5

# check running games in sec
CHECK_INTERVAL = 30

TAGGED_CHANNEL_ID = os.environ["DISCORD_TAGGED_CHANNEL_ID"]

TAG = '#vague'