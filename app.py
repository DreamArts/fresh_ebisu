import os
import json
import requests
import pprint
import time

from flask import Flask, request
from dotenv import load_dotenv
from chiwawa_client import ChiwawaClient
from gremlin_python.driver import client, serializer
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from step2 import RawDataPrettifier    #RawDataPrettifier
from step3 import ScoreCalculator    #ScoreCalculator
from step4 import Figure



app = Flask(__name__)
load_dotenv('.env')
env = os.environ

executer = ThreadPoolExecutor(2)

@app.route('/message', methods=['POST'])
def messages():
    if is_request_valid(request):
        ENDPOINT = env['ENDPOINT']
        DB_NAME = env['DB_NAME']
        GRAPH_NAME = env['GRAPH_NAME']
        PRIMARY_KEY = env['PRIMARY_KEY']
        c = client.Client('wss://{}.gremlin.cosmosdb.azure.com:443/'.format(ENDPOINT), 'g',
                      username="/dbs/{0}/colls/{1}".format(DB_NAME, GRAPH_NAME),
                      password="{}".format(PRIMARY_KEY),
                      message_serializer=serializer.GraphSONSerializersV2d0()
                      )
        body = request.get_json(silent=True)
        companyId = body['companyId']
        msgObj = body['message']
        groupId = msgObj['groupId']
        messageText = msgObj['text']
        userName = msgObj['createdUserName']
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
            if(group == 'user'):
                query = 'g.V().has(\'' + group + '\', \'fullName\',  \'' + full_name + '\').out(\'belongsTo\').values(\'fullName\')'
            elif(group == 'group'):
                query = 'g.V().has(\'' + group + '\', \'fullName\',  \'' + full_name + '\').in(\'belongsTo\').values(\'fullName\')'
            callback = c.submitAsync(query)
            res = [i for it in callback.result() for i in it]
            pprint.pprint(res)
            send_message(companyId, groupId, str(res))

        elif('#:>' in messageText):
            query = messageText.split(" ", 1)
            query = query[1]
            callback = c.submitAsync(query)
            res = [i for it in callback.result() for i in it]
            pprint.pprint(res)
            send_message(companyId, groupId, str(res))
        elif('?' in messageText):
            text = '#searchMember (user/group) : メンバを返す\n# (user/group) name : (所属先/所属メンバ)を返す'
            send_message(companyId, groupId, text)
        elif('TELL ME WHO IS THE SAI-KYO ' in messageText):
            text = messageText.split(" ", 7)
            start = text[6].split("-", 2)
            end = text[7].split("-", 2)
            start_time = datetime(int(start[0]),int(start[1]),int(start[2])).strftime('%s')
            end_time = datetime(int(end[0]),int(end[1]),int(end[2])).strftime('%s')
            executer.submit(all_run, str(start_time), str(end_time), companyId, groupId)
        else:
            send_message(companyId, groupId, userName + 'さん、' + messageText)
        return "OK"
    else:
        return "Request is not valid."

def all_run(start_time, end_time, cId, gId):
    try:
        get_data(start_time, end_time, cId, gId)
    except:
        import traceback
        traceback.print_exc()


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
        'X-Chiwawa-API-Token': env['CHIWAWA_API_TOKEN']}
    content = { 'text': message }
    requests.post(url, headers=headers, data=json.dumps(content))

def get_data(start_time, end_time, cId, gId):
    # クライアントを生成
    ENDPOINT = env['ENDPOINT']
    DB_NAME = env['DB_NAME']
    GRAPH_NAME = env['GRAPH_NAME']
    PRIMARY_KEY = env['PRIMARY_KEY']
    c = client.Client('wss://{}.gremlin.cosmosdb.azure.com:443/'.format(ENDPOINT), 'g',
                      username="/dbs/{0}/colls/{1}".format(DB_NAME, GRAPH_NAME),
                      password="{}".format(PRIMARY_KEY),
                      message_serializer=serializer.GraphSONSerializersV2d0()
                      )
    
    print("DB接続情報===============================")
    print("ENDPOINT = {0}".format(ENDPOINT))
    print("DB_NAME = {0}".format(DB_NAME))
    print("GRAPH_NAME = {0}".format(GRAPH_NAME))
    print("PRIMARY_KEY = {0}".format(PRIMARY_KEY))
    print("=========================================")
    print("")

    callback = c.submitAsync("g.V().hasLabel('user').values('name')")
    members = [i for it in callback.result() for i in it]

    send_message(cId, gId, "ユーザーは{0}人います！\n只今計算中です。少々お待ちください。".format(len(members)))

    rdp = RawDataPrettifier()
    sc = ScoreCalculator()
    scores_list = []

    log_file = open("./log/log{0}--{1}".format(start_time, end_time), "a")

    for name in members:
        js = {}
        get_user = "g.V().has('user', 'name', '" + str(name) + "')"
        callback = c.submitAsync(get_user)
        js["user"] = [i for it in callback.result() for i in it][0]

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
            sub_js["receivedReactions"] = tmp_reaction
            sub_js["tags"] = tmp_tag

            js["messages"].append(sub_js)
            
        get_received_mentions = get_user + ".in('mentions').where(values('createdAt').is(between('" + start_time + "', '" + end_time + "'))).order().by('createdAt', decr)"
        callback = c.submitAsync(get_received_mentions)
        js["receivedMentions"] = [i for it in callback.result() for i in it]

        get_send_reactions = get_user + ".out('adds').where(values('createdAt').is(between('" + start_time + "', '" + end_time + "'))).order().by('createdAt', decr)"
        callback = c.submitAsync(get_send_reactions)
        reactions = [i for it in callback.result() for i in it]

        js["sendReactions"] = []
        for reaction in reactions:
            sub_js = {}
            sub_js["reaction"] = reaction
            reaction_id = reaction["id"]

            get_send_reaction = "g.V().hasLabel('reaction').has('id', '" + reaction_id + "').out('attachedTo')"
            callback = c.submitAsync(get_send_reaction)
            sub_js["message"] = [i for it in callback.result() for i in it]

            js["sendReactions"].append(sub_js)

        js["period"] = {
            "start": start_time,
            "end": end_time 
        }
        print("")
        print("{0} ===========================".format(name))
        print(js)

        prettified = rdp.prettify_from(js)
        scores = sc.calc_scores(prettified)
        total_score = 0
        for value in scores.values():
            if type(value) == type(int()):
                total_score += int(value)
        if total_score > 0:
            scores_list.append(scores)
            print("---")
            print(scores)
            log_file.write(json.dumps(scores))
            log_file.flush()
        #send_message(cId, gId, str(name))

    log_file.close()
    data = {
        "period":{
            "start": start_time,
            "end": end_time 
        },
        "scores": scores_list
    }
    result_filename = Figure.ranking2(data)

    cc = ChiwawaClient(cId, env['CHIWAWA_API_TOKEN'])
    cc.post_file(group_id=gId, file_path=result_filename, file_type='image/png')
