import json
import copy

from step2 import RawDataPrettifier    #RawDataPrettifier
from step3 import ScoreCalculator    #ScoreCalculator
from step4 import Figure

#############################################################
# test 2 ~ 4
#############################################################
inputFile = open('./sample-data-schema/1to2-sample.json','r')
raw = json.load(inputFile)

# step2
rdp = RawDataPrettifier()
prettified = rdp.prettify_from(raw)

# step3
sc = ScoreCalculator()
scores = sc.calc_scores(prettified)

# step4
scores2 = copy.deepcopy(scores)
scores2["userId"] = "user555"
scores2["activeRate"] = 500
data = {
    "period": {
        "start": "2018-02-05",
        "end": "2018-03-05"
    },
    "scores": [scores, scores2]
}
Figure.ranking(data)
#############################################################