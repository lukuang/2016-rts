"""
plot the association between silent days and predictor
"""

import os
import json
import sys
import re
import argparse
import codecs
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from enum import IntEnum, unique

from silent_days import SilentDaysFromRes,SilentDaysFromJug
from predictor import Clarity, AverageIDF,StandardDeviation,NormalizedStandardDeviation,TopScore

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year



@unique
class PredictorName(IntEnum):
    clarity = 0
    average_idf = 1
    standard_deviation = 2
    n_standard_deviation = 3
    top_score = 4

@unique
class Expansion(IntEnum):
    raw = 0
    static = 1
    dynamic = 2


    


BIN_FILES = {
    PredictorName.clarity: "/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/c_code/show_clarity",
    PredictorName.average_idf: "/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/c_code/get_average_idf",
    PredictorName.standard_deviation:"",
    PredictorName.n_standard_deviation:"",
    PredictorName.top_score:""
}

Q_DIR = {
    Year.y2015:{},
    Year.y2016:{},
    Year.y2011:{}
}

Q_DIR[Year.y2015] = {
    Expansion.raw:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2015/raw/clarity_queries",
    Expansion.static:"/infolab/headnode2/lukuang/2016-rts/code/my_code/distribution/query_prediction/threshold_with_lm_difference/data/clarity_queries/original"
}

Q_DIR[Year.y2016] = {
    Expansion.raw:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2016/raw/clarity_queries",
    Expansion.static:"/infolab/headnode2/lukuang/2016-rts/code/2016/senario_b/data/reparsed/clarity_queries/static",
    Expansion.dynamic:"/infolab/headnode2/lukuang/2016-rts/code/2016/senario_b/data/reparsed/clarity_queries/dynamic"
}

Q_DIR[Year.y2011] = {
    Expansion.raw:"/infolab/node4/lukuang/2015-RTS/2011-data/generated_data/raw/clarity_queries",
    Expansion.static:"/infolab/node4/lukuang/2015-RTS/2011-data/generated_data/static/clarity_queries"
}

R_DIR = {
    Year.y2015:{},
    Year.y2016:{}, 
    Year.y2011:{} 
}

R_DIR[Year.y2015] = {
    Expansion.raw:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2015/raw/results",
    Expansion.static:"/infolab/headnode2/lukuang/2016-rts/code/my_code/distribution/query_prediction/threshold_with_lm_difference/data/results/original"
}

R_DIR[Year.y2016] = {
    Expansion.raw:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2016/raw/results",
    Expansion.static:"/infolab/headnode2/lukuang/2016-rts/code/2016/senario_b/data/reparsed/results/static",
    Expansion.dynamic:"/infolab/headnode2/lukuang/2016-rts/code/2016/senario_b/data/reparsed/results/dynamic"
}

R_DIR[Year.y2011] = {
    Expansion.raw:"/infolab/node4/lukuang/2015-RTS/2011-data/generated_data/raw/results",
    Expansion.static:"/infolab/node4/lukuang/2015-RTS/2011-data/generated_data/static/results"
}

IND_DIR = {
    Year.y2015: "/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/individual",
    Year.y2016: "/infolab/headnode2/lukuang/2016-rts/data/full_index_reparsed",
    Year.y2011: "/infolab/node4/lukuang/2015-RTS/2011-data/individual_index"
}

def generate_predictor_values(predictor_choice,qrel,
                              index_dir,query_dir,result_dir,
                              bin_file,data_storage_file):
    if predictor_choice == 0:
        predictor = Clarity(qrel,index_dir,query_dir,bin_file)
    elif predictor_choice == 1:
        predictor = AverageIDF(qrel,index_dir,query_dir,bin_file)
    elif predictor_choice == 2:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using DEV!")
        else:
            predictor = StandardDeviation(qrel,result_dir)
    elif predictor_choice == 3:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using NDEV!")
        else:
            predictor = NormalizedStandardDeviation(qrel,result_dir)
    elif predictor_choice == 4:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using Top Score!")
        else:
            predictor = TopScore(qrel,result_dir)


    # predictor.show()
    with open(data_storage_file,"w") as f:
        f.write(json.dumps(predictor.values))

    return predictor.values
    
    


def plot_predictor_values(predictor_values,silent_day_values,dest_file):
    silent_predictor_values = []
    non_silent_predictor_values = []
    val = .0
    for day in silent_day_values:
        for qid in silent_day_values[day]:
            
            if silent_day_values[day][qid]:
                silent_predictor_values.append(predictor_values[day][qid])
                # if predictor_values[day][qid] == 5.93344:
                #     print "%s,%s" %(qid,day)
            else:
                non_silent_predictor_values.append(predictor_values[day][qid])

    # print silent_predictor_values
    # print max(silent_predictor_values)
    # print non_silent_predictor_values
    # print max(non_silent_predictor_values)
    plt.plot(silent_predictor_values, np.zeros_like(silent_predictor_values) + 1.0, 'ro', label='silent days')
    plt.plot(non_silent_predictor_values,np.zeros_like(non_silent_predictor_values) + -1.0,'bx', label='non-silent days')
    plt.ylim([-2,2])
    plt.legend()
    plt.savefig(dest_file)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    # parser.add_argument("--index_dir","-id",default="/infolab/headnode2/lukuang/2016-rts/data/full_index_reparsed/")
    # parser.add_argument("--query_dir","-qr",default="/infolab/headnode2/lukuang/2016-rts/code/2016/senario_b/data/reparsed/clarity_queries/static/")
    parser.add_argument("--use_result","-ur",action="store_true")
    parser.add_argument("data_dir")
    parser.add_argument("--year","-y",choices=list(map(int, Year)),default=0,type=int,
        help="""
            Choose the year:
                0:2015
                1:2016
                2:2011
        """)
    parser.add_argument("--expansion","-e",choices=list(map(int, Expansion)),default=0,type=int,
        help="""
            Choose the expansion:
                0:raw
                1:static:
                2:dynamic
        """)
    parser.add_argument("--force","-f",action="store_true")
    parser.add_argument("--predictor_choice","-pc",choices=list(map(int, PredictorName)),default=0,type=int,
        help="""
            Choose the predictor:
                0: clarity
                1: average idf
                2: DEV
                3: NDEV
                4: Top Score
        """)
    args=parser.parse_args()

    args.predictor_choice = PredictorName(args.predictor_choice)
    args.expansion = Expansion(args.expansion)
    args.year = Year(args.year)

    if args.expansion == Expansion.dynamic and args.year != Year.y2016:
        raise RuntimeError("If use dynamic expansion, it cannot be year other than 2016!")


    # get bin file based on the predictor
    bin_file = BIN_FILES[args.predictor_choice]
    query_dir = Q_DIR[args.year][args.expansion]
    index_dir = IND_DIR[args.year]
    # print query_dir
    # print index_dir

    printing_message = "Predictor Choice:\n\t%s\n" %(args.predictor_choice.name)

    # form the grapth file based on the data used

    year_dir = os.path.join(args.data_dir,args.year.name)
    printing_message += "Data:\n\tyear:%s\n" %(args.year.name)

    
    expansion_dir = os.path.join(year_dir,args.expansion.name)
    printing_message += "\texpansion:%s\n" %(args.expansion.name)

    if args.use_result:
        dest_dir = os.path.join(expansion_dir,"with_result")
        result_dir = R_DIR[args.year][args.expansion]
        printing_message += "\twith result\n"
    else:
        dest_dir = os.path.join(expansion_dir,"without_result")
        result_dir = None
        printing_message += "\twithout result\n"

    print printing_message


    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    graph_file = os.path.join(dest_dir,"plot.png")
    data_storage_file = os.path.join(dest_dir,"data")

    if args.use_result:
        silent_day_generator = SilentDaysFromRes(args.year,result_dir)
    else:
        silent_day_generator = SilentDaysFromJug(args.year)

    silent_day_values = silent_day_generator.silent_days
    # print silent_day_values
    # print silent_day_values.keys()


    if (not os.path.exists(data_storage_file) ) or args.force:
        predictor_values = generate_predictor_values(
                                args.predictor_choice,silent_day_generator.qrel,
                                index_dir,query_dir,result_dir,
                                bin_file,data_storage_file)
    
    else:
        predictor_values = json.load(open(data_storage_file))


    plot_predictor_values(predictor_values,silent_day_values,graph_file)




if __name__=="__main__":
    main()

