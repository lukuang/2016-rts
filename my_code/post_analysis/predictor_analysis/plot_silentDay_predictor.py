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
from predictor import *

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year



@unique
class PredictorName(IntEnum):
    clarity = 0
    average_idf = 1
    standard_deviation = 2
    n_standard_deviation = 3
    top_score = 4
    coherence_binary = 5
    coherence_average = 6
    coherence_max = 7
    coherence_binary_n = 8
    coherence_average_n = 9
    coherence_max_n = 10
    query_length = 11
    avg_pmi = 12
    max_pmi = 13
    coherence_idf_weighted_binary = 14
    coherence_idf_weighted_average = 15
    coherence_idf_weighted_max = 16
    coherence_idf_weighted_binary_n = 17
    coherence_idf_weighted_average_n = 18
    coherence_idf_weighted_max_n = 19
    coherence_pmi_weighted_binary = 20
    coherence_pmi_weighted_average = 21
    coherence_pmi_weighted_max =22
    mst_term_relatedness = 23
    link_term_relatedness = 24
    scq = 25
    var = 26
    nqc = 27
    wig = 28
    pwig = 29
    local_avg_pmi = 30
    local_max_pmi = 31

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
    PredictorName.top_score:"",
    PredictorName.coherence_binary:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_unweighted_local_coherence",
    PredictorName.coherence_average:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_unweighted_local_coherence",
    PredictorName.coherence_max:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_unweighted_local_coherence",
    PredictorName.coherence_binary_n:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_unweighted_local_coherence",
    PredictorName.coherence_average_n:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_unweighted_local_coherence",
    PredictorName.coherence_max_n:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_unweighted_local_coherence",
    PredictorName.query_length:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_query_length",
    PredictorName.avg_pmi:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_term_relatedness",
    PredictorName.max_pmi:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_term_relatedness",
    PredictorName.coherence_idf_weighted_binary:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_weighted_local_coherence",
    PredictorName.coherence_idf_weighted_average:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_weighted_local_coherence",
    PredictorName.coherence_idf_weighted_max:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_weighted_local_coherence",
    PredictorName.coherence_idf_weighted_binary_n:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_weighted_local_coherence",
    PredictorName.coherence_idf_weighted_average_n:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_weighted_local_coherence",
    PredictorName.coherence_idf_weighted_max_n:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_weighted_local_coherence",
    PredictorName.coherence_pmi_weighted_binary:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_weighted_local_coherence",
    PredictorName.coherence_pmi_weighted_average:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_weighted_local_coherence",
    PredictorName.coherence_pmi_weighted_max:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_weighted_local_coherence",
    PredictorName.mst_term_relatedness:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_mst_term_relatedness",
    PredictorName.link_term_relatedness:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_link_term_relatedness",
    PredictorName.scq:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_scq",
    PredictorName.var:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_var",
    PredictorName.nqc:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_collection_f2exp_score",
    PredictorName.wig:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_wig",
    PredictorName.pwig:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_pwig",
    PredictorName.local_avg_pmi:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_local_term_relatedness",
    PredictorName.local_max_pmi:"/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/c_code/get_local_term_relatedness",

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

LINK_DIR = {
    Year.y2015:{},
    Year.y2016:{},
    Year.y2011:{}
}

LINK_DIR[Year.y2015] = {
    Expansion.raw:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2015/raw/link_queries",
}

LINK_DIR[Year.y2016] = {
    Expansion.raw:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2016/raw/link_queries",
}

LINK_DIR[Year.y2011] = {
    Expansion.raw:"/infolab/node4/lukuang/2015-RTS/2011-data/generated_data/raw/link_queries",
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
                              bin_file,link_dir,data_storage_file,term_size):
    if predictor_choice == PredictorName.clarity:
        predictor = Clarity(qrel,index_dir,query_dir,bin_file)
    elif predictor_choice == PredictorName.average_idf:
        predictor = AverageIDF(qrel,index_dir,query_dir,bin_file)
    elif predictor_choice == PredictorName.standard_deviation:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using DEV!")
        else:
            predictor = StandardDeviation(qrel,result_dir)
    elif predictor_choice == PredictorName.n_standard_deviation:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using NDEV!")
        else:
            predictor = NormalizedStandardDeviation(qrel,result_dir)
    elif predictor_choice == PredictorName.top_score:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using Top Score!")
        else:
            predictor = TopScore(qrel,result_dir)
    
    elif predictor_choice == PredictorName.coherence_binary:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_binary!")
        else:
            predictor = LocalCoherenceUnweighetedBinary(qrel,index_dir,query_dir,bin_file,result_dir)

    elif predictor_choice == PredictorName.coherence_average:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_average!")
        else:
            predictor = LocalCoherenceUnweighetedAverage(qrel,index_dir,query_dir,bin_file,result_dir)

    elif predictor_choice == PredictorName.coherence_max:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_max!")
        else:
            predictor = LocalCoherenceUnweighetedMax(qrel,index_dir,query_dir,bin_file,result_dir)
    
    elif predictor_choice == PredictorName.coherence_binary_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_binary_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using coherence_binary_n!")
        else:
            predictor = LocalCoherenceUnweighetedBinaryN(qrel,index_dir,query_dir,bin_file,result_dir,term_size)

    elif predictor_choice == PredictorName.coherence_average_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_average_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using coherence_average_n!")
        else:
            predictor = LocalCoherenceUnweighetedAverageN(qrel,index_dir,query_dir,bin_file,result_dir,term_size)

    elif predictor_choice == PredictorName.coherence_max_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_max_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using coherence_max_n!")    
        else:
            predictor = LocalCoherenceUnweighetedMaxN(qrel,index_dir,query_dir,bin_file,result_dir,term_size)


    elif predictor_choice == PredictorName.query_length:
        predictor = QueryLength(qrel,index_dir,query_dir,bin_file)

    elif predictor_choice == PredictorName.avg_pmi:
        predictor = AvgPMI(qrel,index_dir,query_dir,bin_file)

    elif predictor_choice == PredictorName.max_pmi:
        predictor = MaxPMI(qrel,index_dir,query_dir,bin_file)

    elif predictor_choice == PredictorName.coherence_idf_weighted_binary:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_idf_weighted_binary!")
        else:
            predictor = LocalCoherenceIDFWeighetedBinary(qrel,index_dir,query_dir,bin_file,result_dir)
    elif predictor_choice == PredictorName.coherence_idf_weighted_average:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_idf_weighted_average!")
        else:
            predictor = LocalCoherenceIDFWeighetedAverage(qrel,index_dir,query_dir,bin_file,result_dir)
    elif predictor_choice == PredictorName.coherence_idf_weighted_max:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_idf_weighted_max!")
        else:
            predictor = LocalCoherenceIDFWeighetedMax(qrel,index_dir,query_dir,bin_file,result_dir)


    elif predictor_choice == PredictorName.coherence_idf_weighted_binary_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_idf_weighted_binary_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using coherence_idf_weighted_binary_n!")
        else:
            predictor = LocalCoherenceIDFWeighetedBinaryN(qrel,index_dir,query_dir,bin_file,result_dir,term_size)

    elif predictor_choice == PredictorName.coherence_idf_weighted_average_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_idf_weighted_average_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using coherence_idf_weighted_average_n!")
        else:
            predictor = LocalCoherenceIDFWeighetedAverageN(qrel,index_dir,query_dir,bin_file,result_dir,term_size)

    elif predictor_choice == PredictorName.coherence_idf_weighted_max_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_idf_weighted_max_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using coherence_idf_weighted_max_n!")    
        else:
            predictor = LocalCoherenceIDFWeighetedMaxN(qrel,index_dir,query_dir,bin_file,result_dir,term_size)
    
    elif predictor_choice == PredictorName.coherence_pmi_weighted_binary:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_pmi_weighted_binary!")
        else:
            predictor = LocalCoherencePMIWeighetedBinary(qrel,index_dir,query_dir,bin_file,result_dir)
    elif predictor_choice == PredictorName.coherence_pmi_weighted_average:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_pmi_weighted_average!")
        else:
            predictor = LocalCoherencePMIWeighetedAverage(qrel,index_dir,query_dir,bin_file,result_dir)
    elif predictor_choice == PredictorName.coherence_pmi_weighted_max:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_pmi_weighted_max!")
        else:
            predictor = LocalCoherencePMIWeighetedMax(qrel,index_dir,query_dir,bin_file,result_dir)
    
    elif predictor_choice == PredictorName.mst_term_relatedness:
        predictor = MSTTermRelatedness(qrel,index_dir,query_dir,bin_file)
   
    elif predictor_choice == PredictorName.link_term_relatedness:
        predictor = LinkTermRelatedness(qrel,index_dir,query_dir,link_dir,bin_file)
    
    elif predictor_choice ==  PredictorName.scq:
        predictor = SCQ(qrel,index_dir,query_dir,bin_file)

    elif predictor_choice ==  PredictorName.var:
        predictor = VAR(qrel,index_dir,query_dir,bin_file)

    elif predictor_choice == PredictorName.nqc:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using nqc!")
        else:
            predictor = NQC(qrel,index_dir,query_dir,bin_file,result_dir)

    elif predictor_choice == PredictorName.wig:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using wig!")
        else:
            predictor = WIG(qrel,index_dir,query_dir,bin_file,result_dir)
    
    elif predictor_choice == PredictorName.pwig:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using pwig!")
        else:
            predictor = PWIG(qrel,index_dir,query_dir,bin_file,result_dir)
    
    elif predictor_choice == PredictorName.local_avg_pmi:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using local_avg_pmi!")
        else:
            predictor = LocalTermRelatednessAverage(qrel,index_dir,query_dir,bin_file,result_dir)
    
    elif predictor_choice == PredictorName.local_max_pmi:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using local_max_pmi!")
        else:
            predictor = LocalTermRelatednessMax(qrel,index_dir,query_dir,bin_file,result_dir)
    

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
                2: standard_deviation
                3: n_standard_deviation
                4: top_score
                5: coherence_binary
                6: coherence_average
                7: coherence_max
                8: coherence_binary_n
                9: coherence_average_n
                10: coherence_max_n 
                11: query_length
                12: avg_pmi
                13: max_pmi
                14: coherence_idf_weighted_binary
                15: coherence_idf_weighted_average
                16: coherence_idf_weighted_max
                17: coherence_idf_weighted_binary_n
                18: coherence_idf_weighted_average_n
                19: coherence_idf_weighted_max_n 
                20: coherence_pmi_weighted_binary
                21: coherence_pmi_weighted_average
                22: coherence_pmi_weighted_max
                23: mst_term_relatedness
                24: link_term_relatedness
                25: scq
                26: var
                27: nqc
                28: wig
                29: pwig
                30: local_avg_pmi
                31: local_max_pmi
        """)
    parser.add_argument("--term_size","-tn",type=int,
        help="""
            The number of terms used for generating
            coherence feature
        """)
    args=parser.parse_args()

    args.predictor_choice = PredictorName(args.predictor_choice)
    args.expansion = Expansion(args.expansion)
    args.year = Year(args.year)

    if args.expansion == Expansion.dynamic and args.year != Year.y2016:
        raise RuntimeError("If use dynamic expansion, it cannot be year other than 2016!")

    if args.expansion != Expansion.raw and args.predictor_choice == PredictorName.link_term_relatedness:
        raise RuntimeError("If use link_term_relatedness, the expansion can only be raw!")

    # get bin file based on the predictor
    bin_file = BIN_FILES[args.predictor_choice]
    query_dir = Q_DIR[args.year][args.expansion]
    index_dir = IND_DIR[args.year]
    link_dir = None
    if args.predictor_choice == PredictorName.link_term_relatedness:
        link_dir = LINK_DIR[args.year][args.expansion]
    # print query_dir
    # print index_dir

    printing_message = "Predictor Choice:\n\t%s %s\n" %(args.predictor_choice.name,args.term_size)

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
                                bin_file,link_dir,data_storage_file,args.term_size)
    
    else:
        predictor_values = json.load(open(data_storage_file))


    plot_predictor_values(predictor_values,silent_day_values,graph_file)




if __name__=="__main__":
    main()

