"""
generate result after silent day detection
without applying redundancy detection
"""

import os
import json
import sys
import re
import argparse
import codecs
import cPickle


sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year

R_DIR = {
    Year.y2015: "/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2015/raw/results/f2exp",
    Year.y2016: "/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2016/raw/results/f2exp", 
    Year.y2017: "/infolab/headnode2/lukuang/2017-rts/data/result/raw/"
}

YEAR_STRING_MAP = {
    "Year.y2015": Year.y2015,
    "Year.y2016": Year.y2016,
    "Year.y2017": Year.y2017
}

def year_string_to_year(year_string):
    return YEAR_STRING_MAP[year_string]

class DataSet(object):
    """Dataset
    """
    def __init__(self,dataset_dir):
        self._dataset_dir = dataset_dir
        self._load_data_set()
        self._load_model()

    def _load_data_set(self):
        self._feature_dict =  json.load(open(os.path.join(self._dataset_dir,"data","feature_dict")))
        self._feature_names = sorted(self._feature_dict.values()[0].keys())

        self._X = []
        self._years = set()
        self._index_2_info = {}
        index = 0
        for year_string in self._feature_dict:
            self._years.add(year_string_to_year(year_string))
            days = self._feature_dict[year_string].values()[0].keys()
            qids = self._feature_dict[year_string].values()[0].values()[0].keys()
            for day in days:
                for qid in qids:
                    single_x = []
                    for feature_name in self._feature_names:
                        try:
                        
                            single_x.append(self._feature_dict[year_string][feature_name][day][qid])
                        except KeyError:
                            # print "Feature: %s" %(feature_name)
                            # print "Day:%s, query:%s" %(day,qid)
                            single_x.append(0)

                    self._X.append(single_x)
                    
                    self._index_2_info[index] = {
                                                    "qid": qid,
                                                    "day": day,
                                                    "year": year_string_to_year(year_string)
                                                }
                    index += 1

    def _load_model(self):
        with open(os.path.join(self._dataset_dir,"model","clf_trained_on_others"), mode="rb") as f:
            self._model = cPickle.load(f)

        predicted = self._model.predict(self._X)
        self._prediction = {}
        for index, value in enumerate(predicted):
            qid = self._index_2_info[index]["qid"]
            day = self._index_2_info[index]["day"]
            year = self._index_2_info[index]["year"]
            if year not in self._prediction:
                self._prediction[year] = {}
            if day not in self._prediction[year]:
                self._prediction[year][day] = {}
            
            self._prediction[year][day][qid] = (value == 1)

    def is_silent_day(self,year,day,qid):
        try:
            return self._prediction[year][day][qid]
        except KeyError:
            return True

    @property
    def years(self):
        return self._years

    

def load_data(top_data_dir):
    datasets = {}
    for collection_name in os.walk(top_data_dir).next()[1]:
        # Skip year 2011
        if collection_name == "mb2011":
            continue
        collection_dir = os.path.join(top_data_dir,collection_name)
        datasets[collection_name] = DataSet(collection_dir)


    return datasets



def read_results(result_dir,sd_detector,year):
    results = {}
    for day in os.walk(result_dir).next()[2]:
        day_result_file = os.path.join(result_dir,day)
        with open(day_result_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if not sd_detector.is_silent_day(year,day,qid):
                    if day not in results:
                        results[day] = {}
                    if qid not in results[day]:
                        results[day][qid] = []
                    if (len(results[day][qid])<10):
                        results[day][qid].append(line)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("top_data_dir")
    parser.add_argument("new_result_dir")
    args=parser.parse_args()


    datasets = load_data(args.top_data_dir)

    results = {}
    for collection_name in datasets:
        for year in datasets[collection_name].years:
            print "for year %s" %(year)
            result_dir = R_DIR[year]
            results[year] = read_results(result_dir,datasets[collection_name],year)
            new_result_file = os.path.join(args.new_result_dir,year.name)
            with open(new_result_file,"w") as of:
                for day in sorted(map(int,results[year].keys())):
                    # if args.debug:
                    day = str(day)
                    print "\tprocess day %s" %(day)
                    for qid in results[year][day]:
                        if year==Year.y2016:
                            day_string = "201608%s" %(day.zfill(2))
                        elif year == Year.y2015:
                            day_string = "201507%s" %(day.zfill(2))
                        elif year == Year.y2017:
                            if int(day) < 10:
                                day_string = "201708%s" %(day.zfill(2))
                            else:
                                day_string = "201707%s" %(day.zfill(2))
                        else:
                            raise NotImplemented("year %s is not NotImplemented!" %(year.name))
                        for line in results[year][day][qid]:
                            of.write("%s %s\n" %(day_string,line))
                            



if __name__=="__main__":
    main()

