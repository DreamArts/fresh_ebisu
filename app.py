import os
import json

from flask import Flask, request
from dotenv import load_dotenv
import requests

from .chiwawa_client import ChiwawaClient
from .cosmosdb import CosmosDB

app = Flask(__name__)
load_dotenv('.env')
env = os.environ


@app.route('/tenki', methods=['POST'])
def bot():
    if is_request_valid(request):
        body = request.get_json(silent=True)
        company_id = body['companyId']
        __message = body['message']
        group_id = __message['groupId']
        text = __message['text']
        user_id = __message['createdBy']
        if text == 'user_count':
            cc = ChiwawaClient(company_id, env['CHIWAWA_API_TOKEN'])
            user_count = int(CosmosDB.submit('g.V().hasLabel("user").count()')[0])
            cc.post_message(group_id=group_id'ユーザー数: {0}'.format(user_count))
        return "OK"
    else:
        return "Request is invalid."

def is_request_valid(request):
    validationToken = env['CHIWAWA_VALIDATION_TOKEN']
    receivedToken = request.headers['X-Chiwawa-Webhook-Token']
    return validationToken == receivedToken
