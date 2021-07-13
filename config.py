import os

HOST = 'http://online-go.com/api/v1'

BOT_TOKEN = os.environ["BOT_TOKEN"]

# identifier of the Discord channel that receives notifications
CHANNEL_ID = os.environ["DISCORD_CHANNEL_ID"]

# identifier of the OGS group to observe
GROUP_ID = os.environ["OGS_GROUP_ID"]

INTERVAL = 5

CHECK_INTERVAL = 30