# 最初に！！！！！！
topicブランチが実際に動くコードです。
わかりづらくてすみません。

# 知話輪最強の一人

__御社、最強の知話輪ユーザーを見つけたくはありませんか？__

知話輪熟練度・入り浸り度合いを数値化し、棒グラフで出力します。

スコアの目安は各々で決めてください。

## ファイル細説

### ビジネスロジック

1.py    - DBからデータを持ってくる

1-5.py  - DBから持ってきたデータを加工して扱いやすくする

2.py    - スコアを算出する

3.py    - グラフ描画及び画像出力

### その他プログラム

app.py             - bot本体

chiwawa_client.py  - 知話輪に接続

cosmosdb.ppy       - CosmosDB接続

### ドキュメント

README.md  - このファイル

memo.md    - 議事録など

### サンプルデータ

1to2-sample.json    - 1.pyから1-5.pyへの受け渡しデータのスキーマ

1to2-sample-2.json  - 1-5.pyから2.pyへの受け渡しデータのスキーマ

2to3-sample.json    - 2.pyから3.pyへの受け渡しデータのスキーマ

