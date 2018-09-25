from gremlin_python.driver import client, serializer

class CosmosDB:
    @staticmethod
    def submit(query):
        ENDPOINT = 'your_endpoint'
        DB_NAME = 'your_db'
        GRAPH_NAME = 'your_graph'
        PRIMARY_KEY = 'your_key'
        # クライアントを生成
        c = client.Client('wss://{}.gremlin.cosmosdb.azure.com:443/'.format(ENDPOINT), 'g',
                                username="/dbs/{0}/colls/{1}".format(DB_NAME, GRAPH_NAME),
                                password="{}".format(PRIMARY_KEY),
                                message_serializer=serializer.GraphSONSerializersV2d0()
                            )
        # sample : query = 'g.V().hasLabel("user").out("adds")'
        callback = c.submitAsync(query)
        # コールバックが複数回に分かれて返ってくるので一つのリストにする
        res = [i for it in callback.result() for i in it]
        return res
  