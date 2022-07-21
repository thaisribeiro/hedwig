import os
class Config(object):
    SLACK_TOKEN = os.getenv('SLACK_TOKEN')
    SLACK_CHANNEL = os.getenv('SLACK_CHANNEL')
    SLACK_EMOJI_APP = ':edwiges:'
    SLACK_USER_NAME = os.getenv('SLACK_USER_NAME')
    SLACK_TIME = os.getenv('SLACK_TIME')
    SLACK_EMOJIS_SQUAD = os.getenv('SLACK_EMOJIS_SQUAD')
    REDIS_URL = os.getenv('REDIS_URL')
    MESSAGE_OPEN_MR=os.getenv('MESSAGE_OPEN_MR')
    MESSAGE_PIPELINE_ERROR=os.getenv('MESSAGE_PIPELINE_ERROR')
    MESSAGE_MR_APPROVED=os.getenv('MESSAGE_MR_APPROVED')
    MESSAGE_COMMENTS=os.getenv('MESSAGE_COMMENTS')
    SLACK_IMAGE_MR =  os.getenv('SLACK_IMAGE_MR')