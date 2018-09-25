import json
import pprint
import datetime

from step2 import RawDataPrettifier    #RawDataPrettifier
from step3 import ScoreCalculator    #ScoreCalculator
from step4 import Figure

def p(obj):
    pprint.pprint(obj)

def test():
    rdp = RawDataPrettifier()
    sc = ScoreCalculator()
    with open("./sample-data-schema/2to4-sample.json") as f:
        data = json.load(f)
        Figure.ranking2(data)


test()