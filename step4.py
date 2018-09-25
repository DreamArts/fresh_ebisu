# coding: UTF-8
import json
import datetime
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.font_manager import FontProperties

class Figure:
    @staticmethod
    def ranking2(data):
        jsonData = data["scores"]

        users = []

        for i in jsonData:
            userId = i['userId']
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
            users.append({
                "name": "{0}\n({1})".format(userName, userId),
                "score": score
            })
        users.sort(key=lambda x: x["score"], reverse=True)

        period = data["period"]

        print(period)

        user_names = list(map(lambda x: x["name"], users))
        ranking_scores = list(map(lambda x: x["score"], users))
        max_score = max(map(lambda x: x["score"], users))   
        plt.ylim(0, max_score * 1.1 + 20)
        top = 10
        graph_title = "{0}〜{1}".format(
            datetime.date.fromtimestamp(int(period["start"]) / 1000),
            datetime.date.fromtimestamp(int(period["end"]) / 1000))
        plt.title("スコアランキング （期間：{0}）".format(graph_title))
        plt.bar(user_names[:top], ranking_scores[:top])
        plt.xticks(user_names[:top], rotation=90)
        for x, y in zip(list(range(top)), ranking_scores[:top]):
            plt.text(x, y, y, ha='center', va='bottom')

        
        filename = 'saikyo_{0}_{1}.png'.format(
            datetime.date.fromtimestamp(int(period["start"]) / 1000),
            datetime.date.fromtimestamp(int(period["end"]) / 1000)
        )
        plt.savefig(filename)
        return filename
