"""
classes for handling data (queries)
"""

import os
import json
import sys
import re
import argparse
import codecs
from myUtility.indri import *


class RTSIndriQueryFactory(IndriQueryFactory):
    def __init__(self,count=10,rule=None,
            use_stopper=False,numeric_compare="equals"):


# def main():
#     parser = argparse.ArgumentParser(description=__doc__)
#     parser.add_argument("")
#     args=parser.parse_args()

# if __name__=="__main__":
#     main()

