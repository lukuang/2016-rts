"""
from model files, generate the difference between day
models
"""

import os
import json
import sys
import re
import argparse
import codecs

from myUtility.corpus import Model



class BackGround(object):
    """class to store background
    language model
    """

    def __init__(self,background_file,para_lambda,possible_words):
        self._file = background_file
        temp_model = json.load(open(self._file))
        self._model = {}
        for w in temp_model:
            if w in possible_words:
                self._model[w] = temp_model[w]
        del temp_model
        self._para_lambda = para_lambda
        self._my_model = None

    def get_smoothed_model(self,input_model):
        output_model = {}
        for w in self._model:
            try:
                p = input_model[w]
            except KeyError:
                p = .0
            output_model[w] = self._para_lambda*p\
                                + (1-self._para_lambda)*self._model[w]
        return output_model

    @property
    def model(self):
        if self._my_model:
            return self._my_model
        else:
            self._my_model = Model(True,need_stem=True,
                                     input_stemmed=True,
                                     text_dict=self._model)
            return self._my_model
    


def get_possible_words(model_file):
    possible_word_set = set()
    model_data = json.load(open(model_file))
    for qid in model_data:
         for day in model_data[qid]:
            possible_word_set.update(model_data[qid][day].keys())
    possible_words = {}
    for w in possible_word_set:
        possible_words[w] = 0

    return possible_words


def load_models(model_file,background,measure):
    models = {}
    model_data = json.load(open(model_file))
    for qid in model_data:
        models[qid] = {}
        for day in model_data[qid]:
            if measure == "kl-divergence" or measure == "cosine-dis":
                day_model = background.get_smoothed_model(model_data[qid][day])
            else:
                day_model = model_data[qid][day]
                
            models[qid][day] = Model(True,need_stem=True,
                                     input_stemmed=True,
                                     text_dict=day_model)
    return models            


def compute_differences(models,measure,background):
    dates = range(21,30)
    differences = {}
    for qid in models.keys():
        print "process query %s" %qid
        differences[qid] = {}
        for day in dates:
            today = str(day)
            previous_day = str(day-1)
            if today in models[qid]:
                today_model = models[qid][today]
            else:
                today_model = background.model
            if previous_day in models[qid]:
                previous_day_model = models[qid][previous_day]
            else:
                previous_day_model = background.model

            if measure == "kl-divergence":
                # print "query %s day %s" %(qid,today)
                # print  models[qid][previous_day].model
                # print  models[qid][today].model
                differences[qid][today] =\
                    previous_day_model.kl_divergence(today_model)  

            elif measure == "cosine-dis":
                # since we need 'distance' here, use 1-
                differences[qid][today] =\
                    1 - previous_day_model.cosine_sim(today_model)  
            elif measure == "set-dis":
                differences[qid][today] =\
                    1 - previous_day_model.set_sim(today_model)  
            else:
                raise NotImplementedError("measure %s is not implemented" %measure)
        models.pop(qid,None) 
    return differences

def compute_all_differences(models,measure,background):
    dates = range(20,30)
    differences = {}
    for qid in models.keys():
        print "process query %s" %qid
        differences[qid] = {}
        for i in range(len(dates)):
            for j in range(i+1,len(dates)):

                today = str(dates[j])
                previous_day = str(dates[i])
                if previous_day not in differences[qid]:
                    differences[qid][previous_day] = {}
                if today in models[qid]:
                    today_model = models[qid][today]
                else:
                    today_model = background.model
                if previous_day in models[qid]:
                    previous_day_model = models[qid][previous_day]
                else:
                    previous_day_model = background.model

                if measure == "kl-divergence":
                    # print "query %s day %s" %(qid,today)
                    # print  models[qid][previous_day].model
                    # print  models[qid][today].model
                    differences[qid][previous_day][today] =\
                        previous_day_model.kl_divergence(today_model)  

                elif measure == "cosine-dis":
                    # since we need 'distance' here, use 1-
                    differences[qid][previous_day][today] =\
                        1 - previous_day_model.cosine_sim(today_model)  
                elif measure == "set-dis":
                    differences[qid][previous_day][today] =\
                        1 - previous_day_model.set_sim(today_model)  
                else:
                    raise NotImplementedError("measure %s is not implemented" %measure)
            


        models.pop(qid,None) 
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_file")
    parser.add_argument("dest_file")
    parser.add_argument("background_file")
    parser.add_argument("--para_lambda","-p",type=float,default=0.4)
    parser.add_argument("--compute_all","-a",action="store_true",
                        help="if specified, compute difference between any two days")
    parser.add_argument("--measure","-m",
                        choices=["kl-divergence","cosine-dis","set-dis"]
                        default="set-dis")
                    
    args=parser.parse_args()

    possible_words = get_possible_words(args.model_file)
    print "There are %d possible words" %len(possible_words.keys())
    background = BackGround(args.background_file,args.para_lambda,possible_words)
    models = load_models(args.model_file,background,args.measure)

    if args.compute_all:
        differences = compute_all_differences(models,args.measure,background)

    else:
        differences = compute_differences(models,args.measure,background)

    with open(args.dest_file,"w") as f:
        f.write(json.dumps(differences))

if __name__=="__main__":
    main()

