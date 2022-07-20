import os
import json
import requests
import redis
import constants
import logging
from flask import Flask
from flask import request, jsonify
from settings import Config
from urllib.parse import urlparse

app = Flask(__name__)

logging.basicConfig(filename='record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

url = urlparse(os.environ.get("REDIS_URL"))
r = redis.Redis(host=url.hostname, port=url.port, username=url.username, password=url.password)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    try:
        result = json.loads(json.dumps(request.json))
        
        if request.method == "POST":
            switch = {
                "merge_request": handle_event_merge_request,
                "pipeline": handle_status_pipeline,
                "note": handle_comments
            }
            
            switch[result.get("object_kind")](result) 
    except Exception as e:
        app.logger.error(f"Error log info: {e}")
        return jsonify({"status": 'error'}), 500

def handle_event_merge_request(result):
    if result['object_attributes'].get('action') in ['close', 'reopen', 'approved', 'unapproved', 'unapproved', 'approval', 'unapproval', 'merge']:
        if result['object_attributes']['action'] == 'merge':
            r.delete(f'merge_request_{result["object_attributes"]["id"]}')
        return {}
    
    if {i['id'] for i in result.get('labels') if i['title'] == 'approved'} or result['object_attributes'].get('approved'):
        ts = r.get(f'merge_request_{result["object_attributes"]["id"]}')
        
        return request_post_message(
            text=constants.MESSAGE_MR_APPROVED,
            ts=ts
        )

    return post_message(result)

def handle_status_pipeline(result):
    ts = r.get(f'merge_request_{result["merge_request"]["id"]}')
    if result['object_attributes']['status'] == 'failed':
        return request_post_message(
            text=constants.MESSAGE_PIPELINE_ERROR,
            ts=ts
        )

def handle_comments(result):
    ts = r.get(f'merge_request_{result["merge_request"]["id"]}')
    return request_post_message(
            text=constants.MESSAGE_COMMENTS,
            ts=ts
        )


def post_message(result):
    object_attributes = result["object_attributes"]
    project_name=result["project"]["description"]
    username=result["user"]["username"]
    avatar=result["user"]["avatar_url"]
    branch_title=object_attributes["title"]
    branch_url=object_attributes["url"]
    source_branch=object_attributes["source_branch"]
    target_branch=object_attributes["target_branch"]

    attachments=[
        {
            "color": "#3AA3E3",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": constants.MESSAGE_OPEN_MR.format(slack_squad=Config.SLACK_TIME)
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Projeto:* *{project_name}*\n*Link:* <{branch_url}|{branch_title}>\n*Origem:* {source_branch}\n*Destino:* {target_branch}\n*Autor(a):* @{username}"
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": avatar,
                        "alt_text": "avatar"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "*Squad: *"
                        },
                        {
                            "type": "mrkdwn",
                            "text": Config.SLACK_EMOJIS_SQUAD
                        }
                    ]
                }
            ]
        }
    ]
    
    response = request_post_message(
        attachments=attachments
    )
    
    # set redis ts message
    r.set(f'merge_request_{object_attributes["id"]}', response["ts"])
    
    return response

def request_post_message(**args):
    data = {
        "token": Config.SLACK_TOKEN,
        "channel": Config.SLACK_CHANNEL
    }
    
    if args.get('ts'):
        data.update({
            "thread_ts": args.get('ts'),
            "text": args.get('text')
        })
    else:
        data.update({
            "icon_emoji": Config.SLACK_EMOJI_APP,
            "username": Config.SLACK_USER_NAME,
            "attachments": json.dumps(args.get('attachments'))
        })
    
    response = requests.post("https://slack.com/api/chat.postMessage", data).json()
    return response
