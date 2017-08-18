
"""
generate runs using word embedding vectors for novelty detection
"""

import os
import json
import sys
import re
import argparse
import codecs
# import subprocess
import numpy as np

from model import ModelType,EmbeddingModel

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year


FULL_IND_DIR = {
    Year.y2015:"/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/incremental/29",
    Year.y2016:"/infolab/headnode2/lukuang/2016-rts/data/incremental_index"
}

def get_text(all_text,tid):
    try: 
        text = all_text[tid]
        return text

    except KeyError:
        print "Cannot find text for %s" %(tid)
        return None


class PreviousResults(object):
    """class used to store previously post
    tweets for each run and query, as well as
    check novalty of the tweet
    """

    def __init__(self,sim_treshold,model_file,model_type,debug=False):
        self._sim_treshold, self._debug = sim_treshold, debug
        self._previous_results = {}
        self._embedding_model = EmbeddingModel(model_file,model_type)
        

    

    def _store_tweet(self,new_tweet_vector,run_name,qid):
        if self._debug:
            print "store new tweet for query %s run %s"\
                %(qid,run_name)
        if run_name not in self._previous_results:
            self._previous_results[run_name] = {}
        
        if qid not in self._previous_results[run_name]:
            self._previous_results[run_name][qid] = []
        
        self._previous_results[run_name][qid].append(new_tweet_vector)





    def _check_tweet_redundant(self,new_tweet_vector,tweet_vector):
        vector_sim = self._embedding_model.similarity(new_tweet_vector,tweet_vector)
        if self._debug:
            print "the metric is %f" %(term_diff)
        if vector_sim >= self._sim_treshold:
            return True
        else:
            return False



    def is_redundant(self,tweet_text,run_name,qid):
        sentence_list = re.findall("\w+",tweet_text.lower())
        new_tweet_vector = self._embedding_model.get_sentence_vector(sentence_list)

        if run_name not in self._previous_results:
            self._previous_results[run_name] = {}
            self._previous_results[run_name][qid] = []
            
        elif qid not in self._previous_results[run_name]:
            self._previous_results[run_name][qid] = []

        
        else:
            if np.count_nonzero(new_tweet_vector) == 0:
                print "Warning: tweet does not have any matching words:"
                print tweet_text
                return False
            for tweet_vector in self._previous_results[run_name][qid]:
                if self._check_tweet_redundant(new_tweet_vector,tweet_vector):
                    if self._debug:
                        print "%s is redundant" %(tweet_text)
                        print "-"*20
                    return True

        self._store_tweet(new_tweet_vector,run_name,qid)
        return False

    


def gene_result_for_year(year,model_type,model_file,
                         sim_treshold,src_result_dir,
                         new_result_dir,debug,all_text,
                         previous_results):

    src_file = os.path.join(src_result_dir,year.name)
    dest_file = os.path.join(new_result_dir,year.name)
    year_index_dir = FULL_IND_DIR[year]
    run_name = year.name
    
    print "Generate result"

    
    with open(dest_file,"w") as of:
        with open(src_file) as f:
            for line in f:
                parts = line.split()
                qid = parts[1]
                tid = parts[3]
                t_text = get_text(all_text,tid)
                if not previous_results.is_redundant(t_text,run_name,qid):
                    of.write(line)

    # previous_results._embedding_model.print_unseen_words_info()




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug","-de",action="store_true")
    parser.add_argument("--model_type","-mt",choices=list(map(int, ModelType)),default=0,type=int,
        help="""
            Choose the model type:
                0:glove
                1:word2vec
        """)
    parser.add_argument("model_file")
    parser.add_argument("-amf","--another_model_file")
    parser.add_argument("--all_text_file","-at",default="/infolab/node4/lukuang/2015-RTS/src/2017/use_word_embedding/all_text")
    parser.add_argument("--sim_treshold","-st",type=float,default=0.5)
    parser.add_argument("src_result_dir")
    parser.add_argument("new_result_dir")
    args=parser.parse_args()


    args.model_type = ModelType(args.model_type)

    all_text = json.load(open(args.all_text_file))

    print "Initiate model"
    previous_results = PreviousResults(args.sim_treshold,args.model_file,args.model_type,args.debug)

    print "Process 2015:"
    gene_result_for_year(Year.y2015,args.model_type,args.model_file,
                         args.sim_treshold,args.src_result_dir,
                         args.new_result_dir,args.debug,all_text,previous_results)


    print '-'*20
    if args.another_model_file:
        print "load another model for 2016"
        previous_results = PreviousResults(args.sim_treshold,args.another_model_file,args.model_type,args.debug)


    print "Process 2016:"
    gene_result_for_year(Year.y2016,args.model_type,args.model_file,
                         args.sim_treshold,args.src_result_dir,
                         args.new_result_dir,args.debug,all_text,previous_results)


if __name__=="__main__":
    main()

