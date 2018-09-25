# coding: UTF-8
import json
import pprint
import datetime
import functools
import collections
import MeCab

# 出力されるデータのスキーマについては ./sample-data-schema/2to3-sample.json を参照

def calc_all(data):
    return None

# userデータ（messageなど）を引数に取り、スコアを算出
# 各スコアの算出について詳細はこのメソッドの下に続く各メソッドを参照
def calc_scores(data):
    user_scores = {
        "userId"              : data["user"]["name"],
        "userName"            : data["user"]["fullName"],
        "activeRate"          : calc_active_rate(data),
        "knowledgeAmount"     : calc_knowledge_amount(data),
        "responseTime"        : calc_response_time(data),
        "myReactionSpeed"     : calc_my_reaction_speed(data),
        "sentimentalJourney"  : calc_sentimental_journey(data),
        "mentionsToAll"       : calc_mentions_to_all(data),
        "tagUseScore"         : calc_tag_use_score(data),
        "influencerScore"     : calc_influencer_score(data),
        "groupAcitivity"      : calc_group_activity(data),
        "mentionsTargetScore" : calc_mentions_target_score(data)
    }
    return user_scores

# activeRate : ログイン率の計算
def calc_active_rate(data)->int:
    bias = 1000
    # ログインした日数
    all_actions = list(map(lambda x: x["message"], data["messages"])) + list(map(lambda x: x["reaction"], data["sendReactions"]))
    all_created_at = list(map(lambda x: datetime.date.fromtimestamp(int(x["createdAt"]) / 1000), all_actions))
    active_days = len(set(all_created_at))  #set()で重複した日付が削除される
    # 全日数
    period = data["period"]
    _s = list(map(lambda x: int(x), period["start"].split("-")))
    _e = list(map(lambda x: int(x), period["end"].split("-")))
    start = datetime.date(_s[0], _s[1], _s[2])
    end = datetime.date(_e[0], _e[1], _e[2])
    return int((active_days / ((end - start).days + 1)) * bias)

# knowledgeAmount : 知識量
def calc_knowledge_amount(data)->int:
    bias = 10
    mecab = MeCab.Tagger("-d /var/lib/mecab/dic/juman-utf8")
    messages = list(map(lambda x: x["message"], data["messages"]))
    score = 0
    for message in messages:
        text = message["text"]
        lines = list(map(lambda x: x.split("\t"),
            filter(lambda x: x.count("\t"), mecab.parse(text).split("\n"))))
        words = list(map(lambda x: {
                "word": x[0],
                "part": x[1].split(",")[0],
                "part-detail": x[1].split(",")[1]
            }, lines))
        nouns = list(filter(lambda x: x["part"] == "名詞", words))
        verbs = list(filter(lambda x: x["part"] == "動詞", words))
        score = (len(nouns) * 2) + (len(verbs) * 1)
    return score * bias

# responseTime : 返事の早さ
def calc_response_time(data)->int:
    bias = 100
    threshold = 10e5
    time_amounts = list(map(lambda x: (
            int(x["reaction"]["createdAt"]) - int(x["message"]["createdAt"])
        ), data["sendReactions"]))
    score = sum(list(map(lambda x: int(threshold / x), time_amounts)))
    return score * bias

# myReactionSpeed : 自分が行うリアクションの早さ
def calc_my_reaction_speed(data)->int:
    bias = 100
    threshold = 10e5
    time_amounts = list(map(lambda x: (
            int(x["reaction"]["createdAt"]) - int(x["message"]["createdAt"])
        ), data["sendReactions"]))
    score = sum(list(map(lambda x: int(threshold / x), time_amounts)))
    return score * bias

# sentimentalJourney : 自分のメッセージについたリアクションのsentimenスコア
def calc_sentimental_journey(data)->int:
    bias = 25
    reactions = functools.reduce(lambda x, y: x + y,
                    map(lambda x: x["receivedReactions"], data["messages"]))
    total = len(reactions)
    sentiments = {}
    for i in range(total):
        del reactions[i]["createdAt"]
        sentiments[reactions[i]["name"]] = reactions[i]["sentiment"]
    # uniq_count = collections.Counter(map(lambda x: x["name"], reactions))
    return (int(total / 100.0) + len(sentiments)) * bias

# mentionsToAll : @allの使用の多さ
def calc_mentions_to_all(data)->int:
    bias = 25
    num = sum(list(map(lambda x: len(x), map(lambda x: x["mentions"]["toGroup"], data["messages"]))))
    return num * bias

# tagUseScore : タグの利用数に基づくスコア
def calc_tag_use_score(data)->int:
    bias = 75
    num = sum(map(lambda x: len(x["tags"]), data["messages"]))
    return num * bias

# influencerScore : インフルエンサースコア
def calc_influencer_score(data)->int:
    bias = 5
    receivedMentions = data["receivedMentions"]
    score = len(receivedMentions)
    return score * bias

# groupAcitivity : 所属するグループの活発度
def calc_group_activity(data)->list:
    bias = 40
    group_score = []
    return list(map(lambda x: x * bias, group_score))

# mentionsTargetScore : どれほど幅広くメンション、幅広いグループでの発言（@all）を行っているか
def calc_mentions_target_score(data)->int:
    bias = 30
    m_to_group = list(map(lambda x: x["mentions"]["toGroup"], data["messages"]))
    m_to_user = list(map(lambda x: x["mentions"]["toUser"], data["messages"]))
    mentions = functools.reduce(lambda x, y: x + y, m_to_group + m_to_user)
    n = len(set(list(map(lambda x: x["name"], mentions))))
    return n * bias



""" テスト用コード
def p(obj):
    pprint.pprint(obj)
def test():
    with open("./sample-data-schema/1to2-sample-2.json") as f:
        raw_json = json.load(f)
    score_list = calc_scores(raw_json)
    p(score_list)
test()
#"""
