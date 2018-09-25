import json
import pprint
import datetime


class RawDataPrettifier:
    # データベースから出力された結果をキレイにする
    def prettify_from(self, raw):
        unixtime = raw["period"]
        s = datetime.date.fromtimestamp(int(unixtime["start"]))
        e = datetime.date.fromtimestamp(int(unixtime["end"]))
        period = {
            "start": "{0}-{1:0=2}-{2:0=2}".format(s.year, s.month, s.day),
            "end": "{0}-{1:0=2}-{2:0=2}".format(e.year, e.month, e.day)
        }
        ret = {
            "user":             self._get_user_from(raw["user"]),
            "messages":         self._get_messages_from(raw["messages"]),
            "receivedMentions": self._get_received_mentions_from(raw["receivedMentions"]),
            "sendReactions":    self._get_send_reactions_from(raw["sendReactions"]),
            "period":           period
        }
        return ret

    def _get_user_from(self, raw):
        return self._parse_element(raw)

    def _get_messages_from(self, raw):
        ret = []
        for item in raw:
            ret.append(
                {
                    "message": self._parse_element(item["message"]),
                    "receivedReactions": self._parse_elements(item["receivedReactions"]),
                    "tags": self._parse_elements(item["tags"]),
                    "mentions": {
                        "toGroup": self._parse_elements(item["mentions"]["toGroup"]),
                        "toUser": self._parse_elements(item["mentions"]["toUser"])
                    }
                }
            )
        return ret

    def _get_received_mentions_from(self, raw):
        if len(raw) == 0:
            return []    
        else:
            return self._parse_elements(raw)

    def _get_send_reactions_from(self, raw):
        if len(raw) == 0:
            return []
        else:
            return list(map(lambda x: {
                        "reaction": self._parse_element(x["reaction"]),
                        "message":  self._parse_element(x["message"][0])
                    }, raw))

    # パーサー
    # 例)  INPUT => {id:129hqwi7wg2ed, label:hoeg, type:vertex, properties:{name:{id:19h, value:piyo}}}
    #     OUTPUT => {name:piyo}
    # Nodeは、ここではCosmosGraphDB上のedgeまたはvertexとする
    def _parse_element(self, node):
        prop = node["properties"]
        keys = prop.keys()
        ret = {}
        for key in keys:
            ret[key] = prop[key][0]["value"]
        return ret

    # コレクション用パーサー
    def _parse_elements(self, col):
        return list(map(self._parse_element, col))
