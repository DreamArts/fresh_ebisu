# coding: UTF-8
import json
import pprint
import datetime
import functools
import collections
import MeCab


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

# 出力されるデータのスキーマについては ./sample-data-schema/2to3-sample.json を参照
class ScoreCalculator:
    # userデータ（messageなど）を引数に取り、スコアを算出
    # 各スコアの算出について詳細はこのメソッドの下に続く各メソッドを参照
    def calc_scores(self, data):
        user_scores = {
            "userId"              : data["user"]["name"],
            "userName"            : data["user"]["fullName"],
            "activeRate"          : self._calc_active_rate(data),
            "knowledgeAmount"     : self._calc_knowledge_amount(data),
            "responseTime"        : self._calc_response_time(data),
            "myReactionSpeed"     : self._calc_my_reaction_speed(data),
            "sentimentalJourney"  : self._calc_sentimental_journey(data),
            "mentionsToAll"       : self._calc_mentions_to_all(data),
            "tagUseScore"         : self._calc_tag_use_score(data),
            "influencerScore"     : self._calc_influencer_score(data),
            "groupAcitivity"      : self._calc_group_activity(data),
            "mentionsTargetScore" : self._calc_mentions_target_score(data)
        }
        return user_scores

    # activeRate : ログイン率の計算
    def _calc_active_rate(self, data)->int:
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
    def _calc_knowledge_amount(self, data)->int:
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
    def _calc_response_time(self, data)->int:
        bias = 100
        threshold = 10e5
        time_amounts = list(map(lambda x: (
                int(x["reaction"]["createdAt"]) - int(x["message"]["createdAt"])
            ), data["sendReactions"]))
        score = sum(list(map(lambda x: int(threshold / x), time_amounts)))
        return score * bias

    # myReactionSpeed : 自分が行うリアクションの早さ
    def _calc_my_reaction_speed(self, data)->int:
        bias = 100
        threshold = 10e5
        time_amounts = list(map(lambda x: (
                int(x["reaction"]["createdAt"]) - int(x["message"]["createdAt"])
            ), data["sendReactions"]))
        score = sum(list(map(lambda x: int(threshold / x), time_amounts)))
        return score * bias

    # sentimentalJourney : 自分のメッセージについたリアクションのsentimenスコア
    def _calc_sentimental_journey(self, data)->int:
        bias = 25
        messages = data["messages"]
        if len(messages) == 0:
            return 0
        try:
            reactions = functools.reduce(lambda x, y: x + y,
                            map(lambda x: x["receivedReactions"], messages))
            total = len(reactions)
            sentiments = {}
            for i in range(total):
                del reactions[i]["createdAt"]
                sentiments[reactions[i]["name"]] = reactions[i]["sentiment"]
            # uniq_count = collections.Counter(map(lambda x: x["name"], reactions)
            return (int(total / 100.0) + len(sentiments)) * bias
        except:
            import traceback
            traceback.print_exc()

    # mentionsToAll : @allの使用の多さ
    def _calc_mentions_to_all(self, data)->int:
        bias = 25
        num = sum(list(map(lambda x: len(x), map(lambda x: x["mentions"]["toGroup"], data["messages"]))))
        return num * bias

    # tagUseScore : タグの利用数に基づくスコア
    def _calc_tag_use_score(self, data)->int:
        bias = 75
        num = sum(map(lambda x: len(x["tags"]), data["messages"]))
        return num * bias

    # influencerScore : インフルエンサースコア
    def _calc_influencer_score(self, data)->int:
        bias = 5
        receivedMentions = data["receivedMentions"]
        score = len(receivedMentions)
        return score * bias

    # groupAcitivity : 所属するグループの活発度
    def _calc_group_activity(self, data)->list:
        #bias = 40
        #group_score = {}
        return {}#list(map(lambda x: x * bias, group_score))

    # mentionsTargetScore : どれほど幅広くメンション、幅広いグループでの発言（@all）を行っているか
    def _calc_mentions_target_score(self, data)->int:
        bias = 30
        messages = data["messages"]
        if len(messages) == 0:
            return 0
        m_to_group = list(map(lambda x: x["mentions"]["toGroup"], messages))
        m_to_user = list(map(lambda x: x["mentions"]["toUser"], messages))
        mentions = functools.reduce(lambda x, y: x + y, m_to_group + m_to_user)
        n = len(set(list(map(lambda x: x["name"], mentions))))
        return n * bias
