"""
remove duplicate in the results
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess
from Levenshtein import ratio
from myUtility.corpus import Sentence
import cPickle


def get_text(index_dir,tweet_id):
    run_command = "dumpindex %s dt `dumpindex %s di docno %s`"\
            %(index_dir,index_dir,tweet_id)

    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    content = p.communicate()[0]
    m = re.search("<TEXT>(.+?)</TEXT>",content,re.DOTALL)
    if m is not None:
        return m.group(1)
    else:
        return None

def compute_term_diff(t1_model,t2_model):
    words1 =    [ x[0] for x in t1_model.model.most_common()]
    words2 = [ x[0] for x in t2_model.model.most_common()]
    common = list(set(words1).intersection(words2))
    return len(common)*1.0/max(len(words1),len(words2))


def generate_measure_computer(measure_method):
    def compute_measure(tweet_text,previous_text):
        if measure_method == "cosine-sim" :
            t1_model = Sentence(tweet_text).raw_model
            t2_model = Sentence(previous_text).raw_model
                  
            sim = t1_model.cosine_sim(t2_model)
        elif measure_method == "set-sim":
            t1_model = Sentence(tweet_text).raw_model
            t2_model = Sentence(previous_text).raw_model

            sim = compute_term_diff(t1_model,t2_model)
        elif measure_method == "edit-sim":    
            sim = ratio(tweet_text,previous_text)
        else:
            raise NotImplementedError("Measure %s is not implemented"
                                       %(measure_method))
        return sim


    return compute_measure


class PreviousResults(object):
    """class used to store previously post
    tweets for each run and query, as well as
    check novalty of the tweet
    """

    def __init__(self,clarities,differences,coeff,regr,
                 compute_measure,use_regr,debug=False):
        self._debug = debug
        self._clarities = clarities
        self._differences = differences
        self._coeff = coeff
        self._regr = regr
        self._use_regr = use_regr
        self._compute_measure = compute_measure
        self._previous_results = {}

    


    def _store_tweet(self,tweet_text,run_name,qid,day):
        if self._debug:
            print "store new tweet %s\nfor query %s run %s in day %s"\
                %(tweet_text,qid,run_name,day)
        if run_name not in self._previous_results:
            self._previous_results[run_name] = {}
        
        if qid not in self._previous_results[run_name]:
            self._previous_results[run_name][qid] = {}

        if day not in self._previous_results[run_name]:
            self._previous_results[run_name][qid][day] = []

        self._previous_results[run_name][qid][day].append(tweet_text)


    def _term_diff(self,tweet_text,t_text):
        words1 = re.findall("\w+",tweet_text)
        words2 = re.findall("\w+",t_text)
        common = list(set(words1).intersection(words2))
        return len(common)*1.0/max(len(words1),len(words2))


    def _check_tweet_redundant(self,now_tweet_text,previous_text,previous_day,day,qid):
        if self._debug:
            print "check diff between %s\nand %s" %(now_tweet_text,previous_text)
        sim = self._compute_measure(now_tweet_text,previous_text)
        threshold = self._compute_threshold(previous_day,day,qid)
        if self._debug:
            print "the metric is %f" %(sim)
            print "the thresohold is %f" %(threshold)
        if sim >= threshold:
            return True
        else:
            return False

    def _compute_threshold(self,previous_day,day,qid):
        
        previous_clarity = self._clarities[previous_day][qid]
        clarity = self._clarities[day][qid]
        try:
            lm_difference = self._differences[qid][previous_day][day]
        except KeyError:
            lm_difference = .0
        if self._use_regr:
            temp_x = [[
                    clarity,
                    previous_clarity,
                    lm_difference,
                ]]
            temp_y = self._regr.predict(temp_x)
            threshold = temp_y[0]
        else: 
            threshold = clarity * self._coeff[0]
            threshold += previous_clarity * self._coeff[1]
            threshold += lm_difference * self._coeff[2]

        return threshold



    def is_redundant(self,now_tweet_text,run_name,qid,day):
        
        if run_name not in self._previous_results:
            self._previous_results[run_name] = {}
        
        if qid not in self._previous_results[run_name]:
            self._previous_results[run_name][qid] = {}
        
        if day not in self._previous_results[run_name][qid]:
            self._previous_results[run_name][qid][day] = []

        
        
        for previous_day in self._previous_results[run_name][qid]:

            for previous_text in self._previous_results[run_name][qid][previous_day]:
                if self._check_tweet_redundant(now_tweet_text,previous_text,previous_day,day,qid):
                    if self._debug:
                        print "%s\n is redundant to\n%s" %(now_tweet_text,previous_text)
                        print "-"*20
                    return True

        self._store_tweet(now_tweet_text,run_name,qid,day)
        return False




def get_clarity(clarity_dir):
    clarities = {}
    for date in os.walk(clarity_dir).next()[2]:
        clarities[date] = {}
        day_clarity_file = os.path.join(clarity_dir,date)
        date_clarity = json.load(open(day_clarity_file))
        for qid in date_clarity:
            clarities[date][qid] = date_clarity[qid]

    return clarities

def get_lm_difference(difference_file):
    differences = json.load(open(difference_file))

    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src_file")
    parser.add_argument("dest_file")
    parser.add_argument("--clarity_dir","-cd",default="/infolab/node4/lukuang/2015-RTS/src/my_code/novalty/with_other_feature/data/clarity")
    parser.add_argument("--tweet_text_file","-ttf",default="/infolab/node4/lukuang/2015-RTS/2015-data/tweet_text_file")
    parser.add_argument("difference_file")
    parser.add_argument("training_data_dir")
    parser.add_argument("--debug","-de",action="store_true")
    parser.add_argument("--use_regr","-ur",action="store_true")
    parser.add_argument("--measure_method","-m",choices=["cosine-sim","set-sim","edit-sim"],default="cosine-sim")
    parser.add_argument("--senario_b","-b",action="store_true")
    parser.add_argument("--index_dir","-ir",default="/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/incremental/29")
    args=parser.parse_args()

    

    print "get clarity"
    clarities = get_clarity(args.clarity_dir)

    print "get language model difference"
    differences = get_lm_difference(args.difference_file)

    print "get coeff and regr"
    coeff_file = os.path.join(args.training_data_dir,"coeff")
    regr_file = os.path.join(args.training_data_dir,"regr")
    coeff = json.load(open(coeff_file))
    f = open(regr_file, 'rb')
    regr = cPickle.load(f)
    f.close()
    
    print "get compute measure function"
    compute_measure = generate_measure_computer(args.measure_method)



    previous_results = PreviousResults(clarities,differences,
                                       coeff,regr,compute_measure,
                                       args.use_regr,args.debug)
    tweet_text_map = {}
    if os.path.exists(args.tweet_text_file):
        if os.stat(args.tweet_text_file).st_size!=0:
            tweet_text_map = json.load(open(args.tweet_text_file))

    with open(args.dest_file,'w') as of:
        with open(args.src_file) as f:
            for line in f:
                parts = line.split()
                if args.senario_b:
                    day_string =  parts[0]
                    day = day_string[6:]
                    qid = parts[1]
                    tid = parts[3]
                    run_name = parts[6]
                else:
                    qid = parts[0]
                    tid = parts[1]
                    run_name = parts[3] 
                try:
                    tweet_text = tweet_text_map[tid]
                except KeyError:
                    print "need to fetch text for %s" %tid
                    tweet_text = get_text(args.index_dir,tid)

                    tweet_text_map[tid] = tweet_text

                if tweet_text is None:
                    raise RuntimeError("the tweet id %s does not have text!" %tid)
                else:
                    if not previous_results.is_redundant(tweet_text,run_name,qid,day):
                        of.write(line)

    with open(args.tweet_text_file,"w") as f:
        f.write(json.dumps(tweet_text_map))

if __name__=="__main__":
    main()

