import os
import json

import requests

from flask import Flask, request
from dotenv import load_dotenv

from chiwawa_client import ChiwawaClient
#import call_back

from gremlin_python.driver import client, serializer
import pprint
import time

from concurrent.futures import ThreadPoolExecutor

from datetime import datetime
#import make_query


ENDPOINT = 'intern-2018-fjmt'
DB_NAME = 'sample-database'
GRAPH_NAME = 'sample-graph'
PRIMARY_KEY = 'k0oZuYmygP4nr9XpgahGnBJiSxmICEIGNPoGO0nAiVJ3wSdb6bQcGuN29Ff43ix1xkiV1tPgFGaWXYiqvxbaOQ=='

# クライアントを生成
c = client.Client('wss://{}.gremlin.cosmosdb.azure.com:443/'.format(ENDPOINT), 'g',
                      username="/dbs/{0}/colls/{1}".format(DB_NAME, GRAPH_NAME),
                      password="{}".format(PRIMARY_KEY),
                      message_serializer=serializer.GraphSONSerializersV2d0()
                      )


app = Flask(__name__)
load_dotenv('.env')
env = os.environ

#t = time.localtime()

executer = ThreadPoolExecutor(2)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/message', methods=['POST'])
def messages():
    if is_request_valid(request):
        body = request.get_json(silent=True)
        companyId = body['companyId']
        msgObj = body['message']
        groupId = msgObj['groupId']
        messageText = msgObj['text']
        userName = msgObj['createdUserName']
#        if(messageText == 'history'):
#            cc = ChiwawaClient(companyId, env['CHIWAWA_API_TOKEN'])
#            message_list = cc.get_message_list(group_id = groupId)
#            txt = ''
#            for text in message_list['messages']:
#                if text['createdUserName'].find('history -') != -1:                   
#                    txt += '\n' + text['text']
#            messageText = txt
        if('#searchMember' in messageText):
            text = messageText.split(" ", 1)
            type_name = text[1]
            query = 'g.V().hasLabel(\'' + type_name + '\').values(\'fullName\')'
            print(query)
            callback = c.submitAsync(query)
            res = [i for it in callback.result() for i in it]
            pprint.pprint(res)
            send_message(companyId, groupId, str(res))

        elif('# ' in messageText):
            text = messageText.split(" ", 2)
            group = text[1]
            full_name = text[2]
            #query_type = text[3]

            if(group == 'user'):
                query = 'g.V().has(\'' + group + '\', \'fullName\',  \'' + full_name + '\').out(\'belongsTo\').values(\'fullName\')'
            elif(group == 'group'):
                query = 'g.V().has(\'' + group + '\', \'fullName\',  \'' + full_name + '\').in(\'belongsTo\').values(\'fullName\')'
            print(query)
            callback = c.submitAsync(query)
            res = [i for it in callback.result() for i in it]
            pprint.pprint(res)
            send_message(companyId, groupId, str(res))

        elif('#:>' in messageText):
            query = messageText.split(" ", 1)
            query = query[1]
            print(query)
            callback = c.submitAsync(query)
            res = [i for it in callback.result() for i in it]
            pprint.pprint(res)
            send_message(companyId, groupId, str(res))
        elif('?' in messageText):
            text = '#searchMember (user/group) : メンバを返す\n# (user/group) name : (所属先/所属メンバ)を返す'
            send_message(companyId, groupId, text)
        elif('tell me who is the hero in ' in messageText):
            text = messageText.split(" ", 8)
            start = text[7].split("-", 2)
            end = text[8].split("-", 2)

            start_time = datetime(int(start[0]),int(start[1]),int(start[2])).strftime('%s')
            end_time = datetime(int(end[0]),int(end[1]),int(end[2])).strftime('%s')

            executer.submit(all_run, str(start_time), str(end_time), companyId, groupId)
        else:
            send_message(companyId, groupId, userName + 'さん、' + messageText)
        return "OK"
    else:
        return "Request is not valid."

def all_run(start_time, end_time, cId, gId):
    user_list = get_data(start_time, end_time, cId, gId)

    print(user_list)
    send_message(cId, gId, "user_info\n" + str(user_list))

    return user_list

# Check if token is valid.
def is_request_valid(request):
    validationToken = env['CHIWAWA_VALIDATION_TOKEN']
    requestToken = request.headers['X-Chiwawa-Webhook-Token']
    return validationToken == requestToken

# Send message to Chiwawa server
def send_message(companyId, groupId, message):
    url = 'https://{0}.chiwawa.one/api/public/v1/groups/{1}/messages'.format(companyId, groupId)
    headers = {
        'Content-Type': 'application/json',
        'X-Chiwawa-API-Token': env['CHIWAWA_API_TOKEN']
    }
    content = {
        'text': message
    }
    requests.post(url, headers=headers, data=json.dumps(content))

def get_data(start_time, end_time, cId, gId):
    # クライアントを生成
    c = client.Client('wss://{}.gremlin.cosmosdb.azure.com:443/'.format(ENDPOINT), 'g',
                      username="/dbs/{0}/colls/{1}".format(DB_NAME, GRAPH_NAME),
                      password="{}".format(PRIMARY_KEY),
                      message_serializer=serializer.GraphSONSerializersV2d0()
                      )
    
    all_data = []

    #query_get_member = "g.V().hasLabel('user').values('name')"
    #callback = c.submitAsync(query_get_member)
    callback = c.submitAsync("g.V().hasLabel('user').values('name')")
    members = [i for it in callback.result() for i in it]

    for name in members:
        js = {}
        get_user = "g.V().has('user', 'name', '" + str(name) + "')"
        callback = c.submitAsync(get_user)
        js["user"] = [i for it in callback.result() for i in it]

        get_messages = get_user + ".out('posts').where(values('createdAt').is(between('" + start_time + "', '" + end_time + "'))).order().by('createdAt', decr)"
        callback = c.submitAsync(get_messages)
        messages = [i for it in callback.result() for i in it]

        js["messages"] = []
        for message in messages:
            sub_js = {}
            message_id = message["id"]
            sub_js["message"] = message            
            sub_js["mentions"] ={}

            query_get_all_data_from_message =  "g.V().hasLabel('message').has('id', '" + message_id + "').both('mentions', 'attachedTo')"
            callback = c.submitAsync(query_get_all_data_from_message)
            chaos_text = [i for it in callback.result() for i in it]

            tmp_user = []
            tmp_group = []
            tmp_reaction = []
            tmp_tag = []

            for indivisual_js in chaos_text:
                if indivisual_js["label"] == 'user':
                    tmp_user.append(indivisual_js)
                if indivisual_js["label"] == 'group':
                    tmp_group.append(indivisual_js)
                if indivisual_js["label"] == 'reaction':
                    tmp_reaction.append(indivisual_js)           
                if indivisual_js["label"] == 'tag':
                    tmp_tag.append(indivisual_js)

            sub_js["mentions"]["toUser"] = tmp_user
            sub_js["mentions"]["toGroup"] = tmp_group
            sub_js["receiveReactions"] = tmp_reaction
            sub_js["tags"] = tmp_tag

            """
            for indivisual_js in chaos_text:
                if indivisual_js["label"] == 'user':
                    sub_js["mentions"]["toUser"] = indivisual_js
                if indivisual_js["label"] == 'group':
                    sub_js["mentions"]["toGroup"] = indivisual_js
                if indivisual_js["label"] == 'reaction':
                    sub_js["receiveReactions"] = indivisual_js           
                if indivisual_js["label"] == 'tag':
                    sub_js["tags"] = indivisual_js
            """

            js["messages"].append(sub_js)
            
        get_received_mentions = get_user + ".in('mentions').where(values('createdAt').is(between('" + start_time + "', '" + end_time + "'))).order().by('createdAt', decr)"
        callback = c.submitAsync(get_received_mentions)
        js["receivedMentions"] = [i for it in callback.result() for i in it]

        get_send_reactions = get_user + ".out('adds').where(values('createdAt').is(between('" + start_time + "', '" + end_time + "'))).order().by('createdAt', decr)"
        callback = c.submitAsync(get_send_reactions)
        reactions = [i for it in callback.result() for i in it]

        #未実装
        #js["groups"] = []
        #get_group = get_user + ".out('belongsTo').where(values('createdAt').is(between('" + start_time + "', '" + end_time + "'))).order().by('createdAt', decr)"
        #callback = c.submitAsync(get_send_reactions)
        #reactions = [i for it in callback.result() for i in it]


        js["sendReactions"] = []
        for reaction in reactions:
            sub_js = {}
            sub_js["reaction"] = reaction
            reaction_id = reaction["id"]

            get_send_reaction = "g.V().hasLabel('reaction').has('id', '" + reaction_id + "').out('attachedTo')"
            callback = c.submitAsync(get_send_reaction)
            sub_js["message"] = [i for it in callback.result() for i in it]

            js["sendReactions"].append(sub_js)
        
        all_data.append(js)

        #print('alljs')
        #send_message(cId, gId, name)
        print(str(js))
        
        send_message(cId, gId, str(name))

    print('end')
    return all_data