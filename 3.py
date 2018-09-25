# coding: UTF-8
import json
import matplotlib
import matplotlib.pyplot as plt

def ranking():
    inputFile = open('2to3data-sample.json','r')
    jsonData = json.load(inputFile)

    total_score = []
    users = []
    graph_score = {}

    for i in jsonData[1:]:
        userName = i['userName']
        activeRate = i['activeRate']
        knowledgeAmount = i['knowledgeAmount']
        responseTime = i['responseTime']
        myReactionSpeed = i['myReactionSpeed']
        sentimentalJourney = i['sentimentalJourney']
        mentionsToAll = i['mentionsToAll']
        tagUseScore = i['tagUseScore']
        influencerScore = i['influencerScore']
        mentionsTargetScore = i['mentionsTargetScore']
        score = activeRate + knowledgeAmount + responseTime + myReactionSpeed + sentimentalJourney + mentionsToAll\
                        + tagUseScore + influencerScore + mentionsTargetScore
        users.append(userName)
        total_score.append(score)

    graph_score.update(zip(total_score, users))
    sorted_score = sorted(graph_score.items() , reverse = True)

    sorted_score2 = []

    if len(sorted_score) > 5:
        for i in range(5):
            sorted_score2.append(sorted_score[i])
        sorted_score2 = dict(sorted_score2)
        ranking_score = sorted_score2.keys()
        user_name = sorted_score2.values()
    else:
        sorted_score = dict(sorted_score)
        ranking_score = sorted_score.keys()
        user_name = sorted_score.values()

    plt.style.use('ggplot')
    font = {'family' : 'meiryo'}
    matplotlib.rc('font', **font)
    plt.bar(user_name,ranking_score)
    plt.savefig('saikyo.png')
