"""
tune the parameters of post retrieval predictors
"""

import os
import json
import sys
import re
import argparse
import codecs
from sklearn.metrics import roc_auc_score


from silent_days import SilentDaysFromRes,SilentDaysFromJug
from predictor import *
from plot_silentDay_predictor import PredictorName,Expansion,R_DIR,PREDICTOR_CLASS,PredictorClass,RetrievalMethod,BIN_FILES,Q_DIR,IND_DIR

def generate_predictor_values_for_tune(predictor_choice,qrel,
                              index_dir,query_dir,result_dir,
                              bin_file,link_dir,
                              term_size,tune_documents=None, tune_terms=None,
                              of_lambda=None,retrieval_method=None):
    if predictor_choice == PredictorName.clarity:
        if(not tune_documents) or (not tune_terms):
            raise RuntimeError("Need to specify tune_documents and tune_terms when tuning Clarity!") 
        elif retrieval_method is None:
            raise RuntimeError("Need to specify retrieval method when using clarity!")
        else:
            predictor = Clarity(qrel,index_dir,query_dir,bin_file,tune_documents=tune_documents,tune_terms=tune_terms,retrieval_method=retrieval_method)
    elif predictor_choice == PredictorName.average_idf:
        predictor = AverageIDF(qrel,index_dir,query_dir,bin_file)
    elif predictor_choice == PredictorName.dev:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using DEV!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using DEV!")
        else:
            predictor = StandardDeviation(qrel,result_dir,tune_documents=tune_documents)
    elif predictor_choice == PredictorName.ndev:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using NDEV!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using NDEV!")
        else:
            predictor = NormalizedStandardDeviation(qrel,result_dir,tune_documents=tune_documents)
    elif predictor_choice == PredictorName.top_score:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using Top Score!")
        else:
            predictor = TopScore(qrel,result_dir)
    
    elif predictor_choice == PredictorName.coherence_binary:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_binary!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using coherence_binary!")
        else:
            predictor = LocalCoherenceUnweighetedBinary(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)

    elif predictor_choice == PredictorName.coherence_average:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_average!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using coherence_average!")
        else:
            predictor = LocalCoherenceUnweighetedAverage(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)

    elif predictor_choice == PredictorName.coherence_max:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_max!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using coherence_max!")
        else:
            predictor = LocalCoherenceUnweighetedMax(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    
    elif predictor_choice == PredictorName.coherence_binary_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_binary_n!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using coherence_binary_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using coherence_binary_n!")
        else:
            predictor = LocalCoherenceUnweighetedBinaryN(qrel,index_dir,query_dir,bin_file,result_dir,term_size,tune_documents=tune_documents)

    elif predictor_choice == PredictorName.coherence_average_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_average_n!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using coherence_average_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using coherence_average_n!")
        else:
            predictor = LocalCoherenceUnweighetedAverageN(qrel,index_dir,query_dir,bin_file,result_dir,term_size,tune_documents=tune_documents)

    elif predictor_choice == PredictorName.coherence_max_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using coherence_max_n!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using coherence_max_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using coherence_max_n!")    
        else:
            predictor = LocalCoherenceUnweighetedMaxN(qrel,index_dir,query_dir,bin_file,result_dir,term_size,tune_documents=tune_documents)


    elif predictor_choice == PredictorName.query_length:
        predictor = QueryLength(qrel,index_dir,query_dir,bin_file)

    elif predictor_choice == PredictorName.avg_pmi:
        predictor = AvgPMI(qrel,index_dir,query_dir,bin_file)

    elif predictor_choice == PredictorName.max_pmi:
        predictor = MaxPMI(qrel,index_dir,query_dir,bin_file)

    elif predictor_choice == PredictorName.cidf_binary:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using cidf_binary!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using cidf_binary!")
        else:
            predictor = LocalCoherenceIDFWeighetedBinary(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    elif predictor_choice == PredictorName.cidf_average:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using cidf_average!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using cidf_average!")
        else:
            predictor = LocalCoherenceIDFWeighetedAverage(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    elif predictor_choice == PredictorName.cidf_max:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using cidf_max!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using cidf_max!")
        else:
            predictor = LocalCoherenceIDFWeighetedMax(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)


    elif predictor_choice == PredictorName.cidf_binary_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using cidf_binary_n!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using cidf_binary_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using cidf_binary_n!")
        else:
            predictor = LocalCoherenceIDFWeighetedBinaryN(qrel,index_dir,query_dir,bin_file,result_dir,term_size,tune_documents=tune_documents)

    elif predictor_choice == PredictorName.cidf_average_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using cidf_average_n!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using cidf_average_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using cidf_average_n!")
        else:
            predictor = LocalCoherenceIDFWeighetedAverageN(qrel,index_dir,query_dir,bin_file,result_dir,term_size,tune_documents=tune_documents)

    elif predictor_choice == PredictorName.cidf_max_n:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using cidf_max_n!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using cidf_max_n!")
        elif not term_size:
            raise RuntimeError("Need to specify term size when using cidf_max_n!")    
        else:
            predictor = LocalCoherenceIDFWeighetedMaxN(qrel,index_dir,query_dir,bin_file,result_dir,term_size,tune_documents=tune_documents)
    
    elif predictor_choice == PredictorName.cpmi_binary:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using cpmi_binary!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using cpmi_binary!")
        else:
            predictor = LocalCoherencePMIWeighetedBinary(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    elif predictor_choice == PredictorName.cpmi_average:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using cpmi_average!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using cpmi_average!")
        else:
            predictor = LocalCoherencePMIWeighetedAverage(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    elif predictor_choice == PredictorName.cpmi_max:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using cpmi_max!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when using cpmi_max!")
        else:
            predictor = LocalCoherencePMIWeighetedMax(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    
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
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when tuning nqc!")
        elif (retrieval_method is None):
            raise RuntimeError("Need to specify retrieval_method when using nqc!")
        
        else:
            predictor = NQC(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents,retrieval_method=retrieval_method)

    elif predictor_choice == PredictorName.wig:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using wig!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when tuning wig!")
        else:
            predictor = WIG(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    
    elif predictor_choice == PredictorName.pwig:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using pwig!")
        if ( tune_documents is None) or  (of_lambda is None):
            # print tune_documents
            # print of_lambda
            raise RuntimeError("Need to specify tune_documents and of_lambda when using pwig!")
        else:
            predictor = PWIG(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents,of_lambda)
    
    elif predictor_choice == PredictorName.local_avg_pmi:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using local_avg_pmi!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when tuning local_avg_pmi!")
        else:
            predictor = LocalTermRelatednessAverage(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    
    elif predictor_choice == PredictorName.local_max_pmi:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using local_max_pmi!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when tuning local_max_pmi!")
        else:
            predictor = LocalTermRelatednessMax(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    
    elif predictor_choice == PredictorName.tree_estimator:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using tree_estimator!")
        else:
            predictor = TreeEstimator(qrel,index_dir,query_dir,bin_file,result_dir)
    
    elif predictor_choice == PredictorName.aidf_pmi:
        predictor = AvgIDFWeightedPMI(qrel,index_dir,query_dir,bin_file)

    elif predictor_choice == PredictorName.midf_pmi:
        predictor = MaxIDFWeightedPMI(qrel,index_dir,query_dir,bin_file)

    elif predictor_choice == PredictorName.candidate_size:
        predictor = CandidateSize(qrel,index_dir,query_dir,bin_file)

    elif predictor_choice == PredictorName.qf:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using qf!")
        elif(not tune_documents) or (not tune_terms):
            raise RuntimeError("Need to specify tune_documents and tune_terms when tuning qf!") 
        elif retrieval_method is None:
            raise RuntimeError("Need to specify retrieval method when using qf!")
        else:
            predictor = QF(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents,tune_terms=tune_terms,retrieval_method=retrieval_method)
    elif predictor_choice == PredictorName.sized_coherence_binary:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using sized_coherence_binary!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when tuning sized_coherence_binary!")
        else:
            predictor = LocalSizedCoherenceUnweighetedBinary(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)

    elif predictor_choice == PredictorName.sized_coherence_average:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using sized_coherence_average!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when tuning sized_coherence_average!")
        else:
            predictor = LocalSizedCoherenceUnweighetedAverage(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)

    elif predictor_choice == PredictorName.sized_coherence_max:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using sized_coherence_max!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when tuning sized_coherence_max!")
        else:
            predictor = LocalSizedCoherenceUnweighetedMax(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)

    elif predictor_choice == PredictorName.qtc_average:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using qtc_average!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when tuning qtc_average!")
        else:
            predictor = QueryTermCoverageAverage(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    elif predictor_choice == PredictorName.qtc_median:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using qtc_median!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when tuning qtc_median!")
        else:
            predictor = QueryTermCoverageMedian(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    elif predictor_choice == PredictorName.qtc_upper:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using qtc_upper!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when tuning qtc_upper!")
        else:
            predictor = QueryTermCoverageUpper(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    elif predictor_choice == PredictorName.qtc_lower:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using qtc_lower!")
        elif not tune_documents:
            raise RuntimeError("Need to specify tune_documents when tuning qtc_lower!")
        else:
            predictor = QueryTermCoverageLower(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents)
    

    elif predictor_choice == PredictorName.ttc_average:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using ttc_average!")
        elif(not tune_documents) or (not tune_terms):
            raise RuntimeError("Need to specify tune_documents and tune_terms when tuning ttc_average!") 
        elif retrieval_method is None:
            raise RuntimeError("Need to specify retrieval method when using ttc_average!")
        else:
            predictor = TopTermCoverageAverage(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents,tune_terms=tune_terms)
    elif predictor_choice == PredictorName.ttc_median:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using ttc_median!")
        elif(not tune_documents) or (not tune_terms):
            raise RuntimeError("Need to specify tune_documents and tune_terms when tuning ttc_median!") 
        elif retrieval_method is None:
            raise RuntimeError("Need to specify retrieval method when using ttc_median!")
        else:
            predictor = TopTermCoverageMedian(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents,tune_terms=tune_terms)
    elif predictor_choice == PredictorName.ttc_upper:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using ttc_upper!")
        elif(not tune_documents) or (not tune_terms):
            raise RuntimeError("Need to specify tune_documents and tune_terms when tuning ttc_upper!") 
        elif retrieval_method is None:
            raise RuntimeError("Need to specify retrieval method when using ttc_upper!")
        else:
            predictor = TopTermCoverageUpper(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents,tune_terms=tune_terms)
    elif predictor_choice == PredictorName.ttc_lower:
        if not result_dir:
            raise RuntimeError("Need to specify result dir when using ttc_lower!")
        elif(not tune_documents) or (not tune_terms):
            raise RuntimeError("Need to specify tune_documents and tune_terms when tuning ttc_lower!") 
        elif retrieval_method is None:
            raise RuntimeError("Need to specify retrieval method when using ttc_lower!")
        else:
            predictor = TopTermCoverageLower(qrel,index_dir,query_dir,bin_file,result_dir,tune_documents=tune_documents,tune_terms=tune_terms)
        

    return predictor.values


def prepare_for_auc(predictor_values,silent_day_values):
    y_true = []
    y_score = []
    val = .0
    for day in silent_day_values:
        for qid in silent_day_values[day]:
            try: 
                y_score.append( -1*predictor_values[day][qid] )
            except KeyError:
                y_score.append(0)
            if silent_day_values[day][qid]:
                y_true.append(1)
                # if predictor_values[day][qid] == 5.93344:
                #     print "%s,%s" %(qid,day)
            else:
                y_true.append(0)

    return y_true, y_score


def main():

    parser = argparse.ArgumentParser(description=__doc__)
    # parser.add_argument("--index_dir","-id",default="/infolab/headnode2/lukuang/2016-rts/data/full_index_reparsed/")
    # parser.add_argument("--query_dir","-qr",default="/infolab/headnode2/lukuang/2016-rts/code/2016/senario_b/data/reparsed/clarity_queries/static/")
    parser.add_argument("--retrieval_method","-rm",choices=list(map(int, RetrievalMethod)),default=0,type=int,
        help="""
            Choose the retrieval method:
                0:f2exp
                1:dirichlet
                2:pivoted
                3:bm25
        """)
    parser.add_argument("--use_result","-ur",action="store_true")
    parser.add_argument("--debug","-de",action="store_true")
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
                1:static
                2:dynamic
        """)
    parser.add_argument("--predictor_choice","-pc",choices=list(map(int, PredictorName)),default=0,type=int,
        help="""
            Choose the predictor:
                0: clarity
                1: average idf
                2: dev
                3: ndev
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
                14: cidf_binary
                15: cidf_average
                16: cidf_max
                17: cidf_binary_n
                18: cidf_average_n
                19: cidf_max_n 
                20: cpmi_binary
                21: cpmi_average
                22: cpmi_max
                23: mst_term_relatedness
                24: link_term_relatedness
                25: scq
                26: var
                27: nqc
                28: wig
                29: pwig
                30: local_avg_pmi
                31: local_max_pmi
                32: tree_estimator
                33: aidf_pmi
                34: midf_pmi
                35: candidate_size
                36: qf
                37: sized_coherence_binary 
                38: sized_coherence_average
                39: sized_coherence_max
                40: qtc_average
                41: qtc_median
                42: qtc_upper
                43: qtc_lower
                44: ttc_average
                45: ttc_median
                46: ttc_upper
                47: ttc_lower
        """)
    parser.add_argument("--term_size","-tn",type=int,
        help="""
            The number of terms used for generating
            coherence feature
        """)
    args=parser.parse_args()



    T_DOCUMENTS = [
                    PredictorName.wig,
                    PredictorName.dev,
                    PredictorName.ndev,
                    PredictorName.coherence_average,
                    PredictorName.coherence_max,
                    PredictorName.coherence_binary,
                    PredictorName.coherence_average_n,
                    PredictorName.coherence_max_n,
                    PredictorName.coherence_binary_n,
                    PredictorName.cidf_max,
                    PredictorName.cidf_average,
                    PredictorName.cidf_binary,
                    PredictorName.cidf_max_n,
                    PredictorName.cidf_average_n,
                    PredictorName.cidf_binary_n,
                    PredictorName.cpmi_max,
                    PredictorName.cpmi_average,
                    PredictorName.cpmi_binary,
                    PredictorName.nqc,
                    PredictorName.local_avg_pmi,
                    PredictorName.local_max_pmi,
                    PredictorName.sized_coherence_binary,
                    PredictorName.sized_coherence_average,
                    PredictorName.sized_coherence_max,
                    PredictorName.qtc_average,
                    PredictorName.qtc_median,
                    PredictorName.qtc_upper,
                    PredictorName.qtc_lower,
                  ]

    args.predictor_choice = PredictorName(args.predictor_choice)
    if PREDICTOR_CLASS[args.predictor_choice] != PredictorClass.post:
        raise RuntimeError("The predictor should be post retrieval predictor!") 
    args.expansion = Expansion(args.expansion)
    args.retrieval_method = RetrievalMethod(args.retrieval_method)
    tuning_info_strcut = { }
    para_string_list = []
    for year in [Year.y2015,Year.y2016, Year.y2011]:
        
        if args.expansion == Expansion.dynamic and year != Year.y2016:
            raise RuntimeError("If use dynamic expansion, it cannot be year other than 2016!")

        if args.expansion != Expansion.raw and args.predictor_choice == PredictorName.link_term_relatedness:
            raise RuntimeError("If use link_term_relatedness, the expansion can only be raw!")

        # get bin file based on the predictor
        bin_file = BIN_FILES[args.predictor_choice]
        query_dir = Q_DIR[year][args.expansion]
        index_dir = IND_DIR[year]
        link_dir = None
        if args.predictor_choice == PredictorName.link_term_relatedness:
            link_dir = LINK_DIR[year][args.expansion]
        # print query_dir
        # print index_dir

        printing_message = "Predictor Choice:\n\t%s %s\n" %(args.predictor_choice.name,args.term_size)

        # form the grapth file based on the data used

        printing_message += "Data:\n\tyear:%s\n" %(year.name)

        
        printing_message += "\texpansion:%s\n" %(args.expansion.name)

        if args.expansion == Expansion.raw:
            printing_message += "\tretrieval method:%s\n" %(args.retrieval_method.name) 
            result_dir = R_DIR[year][args.expansion][args.retrieval_method]
        else:
            result_dir = R_DIR[year][args.expansion]
        



        

        

        if args.use_result:
            silent_day_generator = SilentDaysFromRes(year,result_dir)
            printing_message += "\ttune using result-related silent-day\n"
        else:
            silent_day_generator = SilentDaysFromJug(year)
            printing_message += "\ttune NOT using result-related silent-day\n"


        silent_day_values = silent_day_generator.silent_days
        
        if args.debug:
            print printing_message
        # print silent_day_values
        # print silent_day_values.keys()

        

        # print "Start Tuning:"
        if(args.predictor_choice in T_DOCUMENTS):
            for tune_documents in [5,10,25,50,75,100]:
                
                predictor_values = generate_predictor_values_for_tune(
                                        args.predictor_choice,silent_day_generator.qrel,
                                        index_dir,query_dir,result_dir,
                                        bin_file,link_dir,
                                        args.term_size,tune_documents=tune_documents,
                                        retrieval_method=args.retrieval_method)
                y_true, y_score = prepare_for_auc(predictor_values,silent_day_values)

                score = roc_auc_score(y_true, y_score)

                para_string = "document=%d" %(tune_documents)
                if para_string not in tuning_info_strcut:
                    tuning_info_strcut[para_string] = {}
                    para_string_list.append(para_string)
                tuning_info_strcut[para_string][ year.name[1:] ] = score
                if args.debug:
                    print "\tfor n %d, the score is %.3f" %(tune_documents,score)
        elif(args.predictor_choice == PredictorName.clarity 
                or args.predictor_choice == PredictorName.ttc_average
                or args.predictor_choice == PredictorName.ttc_median
                or args.predictor_choice == PredictorName.ttc_upper
                or args.predictor_choice == PredictorName.ttc_lower
                or args.predictor_choice == PredictorName.qf):
                
            for tune_documents in [5,10,15,20]:
                for tune_terms in [5,10,15,20]:
                    para_string = "document=%d,term=%d" %(tune_documents,tune_terms)
                    predictor_values = generate_predictor_values_for_tune(
                                            args.predictor_choice,silent_day_generator.qrel,
                                            index_dir,query_dir,result_dir,
                                            bin_file,link_dir,
                                            args.term_size,tune_documents=tune_documents,
                                            tune_terms=tune_terms,retrieval_method=args.retrieval_method)
                    y_true, y_score = prepare_for_auc(predictor_values,silent_day_values)
                    score = roc_auc_score(y_true, y_score)

                    if para_string not in tuning_info_strcut:
                        tuning_info_strcut[para_string] = {}
                        para_string_list.append(para_string)
                    tuning_info_strcut[para_string][ year.name[1:] ] = score
                    if args.debug:
                        print "\tfor tune_documents %d tune_terms %d, the score is %.3f" %(tune_documents,tune_terms,score)
        elif(args.predictor_choice == PredictorName.pwig):
            for tune_documents in [5,10,15,20]:
                for of_lambda in [0.0,0.2,0.4,0.6,0.8,1.0]:
                    para_string = "document=%d,of_lambda=%f" %(tune_documents,of_lambda)
                    predictor_values = generate_predictor_values_for_tune(
                                            args.predictor_choice,silent_day_generator.qrel,
                                            index_dir,query_dir,result_dir,
                                            bin_file,link_dir,
                                            args.term_size,tune_documents=tune_documents,
                                            of_lambda=of_lambda,retrieval_method=args.retrieval_method)
                    y_true, y_score = prepare_for_auc(predictor_values,silent_day_values)
                    score = roc_auc_score(y_true, y_score)

                    if para_string not in tuning_info_strcut:
                        tuning_info_strcut[para_string] = {}
                        para_string_list.append(para_string)
                    tuning_info_strcut[para_string][ year.name[1:] ] = score
                    if args.debug:
                        print "\tfor tune_documents %d of_lambda %.3f, the score is %.3f" %(tune_documents,of_lambda,score)
        else:
            raise NotImplementedError("The tuning for %s is not implemented!" %(args.predictor_choice.name))
        
    if args.term_size:
        output_string_prefix = "|| %s ||" %(args.predictor_choice.name[:-1]+str(args.term_size))

    else:
        output_string_prefix = "|| %s ||" %(args.predictor_choice.name)
    for para_string in para_string_list:
        output_string = "%s %s ||" %(output_string_prefix,para_string)
        for year_string in ["2015","2016","2011"]:
            value = tuning_info_strcut[para_string][year_string]
            output_string = "%s %.3f ||" %(output_string, value)
        print output_string
if __name__=="__main__":
    main()

