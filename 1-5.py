import json
import pprint


# データベースから出力された結果をキレイにする
def prettify_from(raw):
    json = {}
    json["user"] = get_user_from(raw["user"])
    json["messages"] = get_messages_from(raw["messages"])
    json["receivedMentions"] = get_received_mentions_from(raw["receivedMentions"])
    json["sendReactions"] = get_send_reactions_from(raw["sendReactions"])
    json["period"] = raw["period"]
    return json

def get_user_from(raw):
    return parse_element(raw)

def get_messages_from(raw):
    ret = []
    for item in raw:
        ret.append(
            {
                "message": parse_element(item["message"]),
                "receivedReactions": parse_elements(item["receivedReactions"]),
                "tags": parse_elements(item["tags"]),
                "mentions": {
                    "toGroup": parse_elements(item["mentions"]["toGroup"]),
                    "toUser": parse_elements(item["mentions"]["toUser"])
                }
            }
        )
    return ret

def get_received_mentions_from(raw):
    return parse_elements(raw)

def get_send_reactions_from(raw):
    return list(map(lambda x: {
                "reaction":parse_element(x["reaction"]),
                "message":parse_element(x["message"])
            }, raw))

# パーサー
# 例)  INPUT => {id:129hqwi7wg2ed, label:hoeg, type:vertex, properties:{name:{id:19h, value:piyo}}}
#     OUTPUT => {name:piyo}
# Nodeは、ここではCosmosGraphDB上のedgeまたはvertexとする
def parse_element(node):
    prop = node["properties"]
    keys = prop.keys()
    ret = {}
    for key in keys:
        ret[key] = prop[key][0]["value"]
    return ret

# コレクション用パーサー
def parse_elements(col):
    return list(map(parse_element, col))


#""" テスト用コード
def p(obj):
    pprint.pprint(obj)

def test():
    raw_json = []
    with open("./sample-data-schema/1to2-sample.json") as f:
        raw_json = json.load(f)
    pre = prettify_from(raw_json)
    p(pre)

test()
#"""