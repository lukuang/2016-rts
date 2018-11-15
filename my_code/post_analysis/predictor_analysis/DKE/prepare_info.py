"""
prepare the data for silent day prediction by using predictor
with considering RTS2017 as a separate data set
"""

import os
import json
import sys
import re
import argparse
import codecs
from enum import IntEnum, unique
from collections import defaultdict

sys.path.append("../")
from silent_days import SilentDaysFromRes,SilentDaysFromJug

from plot_silentDay_predictor import PredictorName,Expansion,R_DIR,PREDICTOR_CLASS,PredictorClass,RetrievalMethod

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year






MB2011 = [Year.y2011]
MB1516 = [Year.y2015,Year.y2016]
RTS2017 = [Year.y2017]




def try_mkdir(wanted_dir):
    if os.path.exists(wanted_dir):
        # raise RuntimeError("dir already exists: %s" %(wanted_dir))
        # print "WARNING!:dir already exists: %s" %(wanted_dir)
        pass
    else:
        os.makedirs(wanted_dir)


def convert_feature_string(feature_string):
    detail_finder_with_tn = re.search("^(\w+):(\w+):(\d+)$",feature_string)
    if detail_finder_with_tn:
        feature_string = detail_finder_with_tn.group(1)[:-1]+detail_finder_with_tn.group(3)
        feature_string += ":%s" %(detail_finder_with_tn.group(2) )
    feature_string = re.sub(":","_",feature_string)
    feature_string = feature_string[0].upper()+feature_string[1:]
    
    return feature_string

class SingleFeature(object):
    """
    class for getting data for a single feature
    for a year
    """

    

    # Note the feature format should be "PredictorChoice:Expansion"
    def __init__(self,year,feature_descrption_string,predictor_data_dir,method):

        self._year,self._feature_descrption_string, self._predictor_data_dir =\
            year, feature_descrption_string, predictor_data_dir

        self._method = method    


        self._get_feature_detail()

        self._get_data()


    def _get_feature_detail(self):
        """
        get feature detail form feature_descrption_string
        """
        # print "For year %s, the features used:" %(self._year.name)
        detail_finder = re.search("^(\w+?):(\w+)$",self._feature_descrption_string)
        if detail_finder:
            self._predictor_choice = PredictorName[ detail_finder.group(1) ]
            if detail_finder.group(2) == "raw":
                self._query_type = "raw_queries"
            else:
                self._query_type = "exp_queries"
            if (self._predictor_choice == PredictorName.coherence_binary_n or
               self._predictor_choice == PredictorName.coherence_average_n or
               self._predictor_choice == PredictorName.coherence_max_n or
               self._predictor_choice == PredictorName.cidf_binary_n or
               self._predictor_choice == PredictorName.cidf_average_n or
               self._predictor_choice == PredictorName.cidf_max_n):
                raise ValueError("Need to specify term size when using %s!" %(self._predictor_choice.name))

            self._predictor_class = PREDICTOR_CLASS[self._predictor_choice]
            # print "\t%s" %(" ".join([self._predictor_choice.name,self._predictor_class.name,self._expansion.name]))

        else:
            detail_finder_with_tn = re.search("^(\w+?):(\w+):(\d+)$",self._feature_descrption_string)
            if detail_finder_with_tn :
                self._predictor_choice = PredictorName[ detail_finder_with_tn.group(1) ]
                if detail_finder_with_tn.group(2) == "raw":
                    self._query_type = "raw_queries"
                else:
                    self._query_type = "exp_queries"
                if (self._predictor_choice == PredictorName.coherence_binary_n or
                   self._predictor_choice == PredictorName.coherence_average_n or
                   self._predictor_choice == PredictorName.coherence_max_n or
                   self._predictor_choice == PredictorName.cidf_binary_n or
                   self._predictor_choice == PredictorName.cidf_average_n or
                   self._predictor_choice == PredictorName.cidf_max_n):
                    
                    self._predictor_class = PREDICTOR_CLASS[self._predictor_choice]
                    self._term_size = int(detail_finder_with_tn.group(3))
                    # print "\t%s" %(" ".join([self._predictor_choice.name,str(self._term_size),self._predictor_class.name,self._expansion.name]))

                else:
                    raise ValueError("Cannot specify term size when using %s" %(self._predictor_choice.name))
            else:
                raise RuntimeError("Mal format feature description %s" %(self._feature_descrption_string))


    def _get_data(self):
        """
        get data from the predictor data directory according
        to feature detail and name
        """

        if (self._predictor_choice == PredictorName.coherence_binary_n or
                   self._predictor_choice == PredictorName.coherence_average_n or
                   self._predictor_choice == PredictorName.coherence_max_n or
                   self._predictor_choice == PredictorName.cidf_binary_n or
                   self._predictor_choice == PredictorName.cidf_average_n or
                   self._predictor_choice == PredictorName.cidf_max_n):
            self._data_file_path = os.path.join(
                            self._predictor_data_dir,self._predictor_class.name,
                            self._predictor_choice.name[:-1]+"%d" %(self._term_size),
                            self._year.name,
                            self._query_type,self._method,"data")
        else:
            if self._predictor_class == PredictorClass.pre:
                self._data_file_path = os.path.join(
                                self._predictor_data_dir,self._predictor_class.name,
                                self._predictor_choice.name,self._year.name,
                                self._query_type,self._method,"data")
            else:
                self._data_file_path = os.path.join(
                                self._predictor_data_dir,self._predictor_class.name,
                                self._predictor_choice.name,self._year.name,
                            self._query_type,self._method,"data")
        print "Data path:%s" %(self._data_file_path)
        self._feature_data = json.load(open(self._data_file_path))

    @property
    def feature_data(self):
        if not self._feature_data:
            error_message = "The feature data is not loaded properly\n"
            error_message += "descrption: %s\n" %(self._feature_descrption_string)
            error_message += "data_path %s\n" %(self._data_file_path)
            raise RuntimeError(error_message)
        return self._feature_data

    # @property
    # def expansion(self):
    #     if not self._expansion:
    #         error_message = "The feature data is not loaded properly\n"
    #         error_message += "descrption: %s\n" %(self._feature_descrption_string)
    #         error_message += "data_path %s\n" %(self._data_file_path)
    #         raise RuntimeError(error_message)

    #     return self._expansion
    
    



class DataPreparor(object):
    """
    Prepare predictor data for one year given a list of predictors
    """


    def __init__(self, predictor_data_dir, feature_descrption_list,
                 use_raw, all_methods, top_dest_dir,
                 designate_dest_dir,performances):
        self._predictor_data_dir,self._feature_descrption_list =\
            predictor_data_dir,feature_descrption_list

        self._use_raw,self._all_methods = use_raw,all_methods

        self._top_dest_dir = top_dest_dir

        self._designate_dest_dir = designate_dest_dir

        self._performances = performances

    def prepare_data(self):

        # get training data
        self._mb2011_data = self._prepare_vector_data_set(MB2011)
        print "2011 done!"
        self._mb1516_data = self._prepare_vector_data_set(MB1516)
        print "2015/16 done!"
        self._rts2017_data = self._prepare_vector_data_set(RTS2017)
        print "2017 done!"
        self._save_data()

    def _prepare_vector_data_set(self,year_list):

        info = []
        for year in year_list:
            
            silent_day_generator = SilentDaysFromJug(year)

            silent_days = silent_day_generator.silent_days
            # print vector_data_set["silent_days"][year]

            year_performance = self._performances[year]
            year_features = {}
            for feature_descrption_string in self._feature_descrption_list:
                year_features[feature_descrption_string] = {}
                for method in self._all_methods:
                    single_feature = SingleFeature(year,feature_descrption_string,self._predictor_data_dir,method)

                    year_features[feature_descrption_string][method] = single_feature.feature_data
            for day in sorted(silent_days.keys()):
                for qid in sorted(silent_days[day].keys()):
                    if not silent_days[day][qid]:
                        # only train on non-silent days
                        performance_dict = {}
                        method_fearures = {}
                        for method in self._all_methods:
                            try:
                                performance_dict[method] = year_performance[method][day][qid] 
                            except KeyError:
                                print "Wrong keys: %s %s %s %s" %(year.name,method,day,qid)
                                print year_performance[method][day]
                                sys.exit()
                            method_fearures[method] = []

                            for feature_descrption_string in sorted(self._feature_descrption_list):
                                try:
                                    method_fearures[method].append((feature_descrption_string, year_features[feature_descrption_string][method][day][qid]))
                                except KeyError:
                                    # print "Feature: %s" %(feature_descrption_string)
                                    # print "Day:%s, query:%s" %(day,qid)
                                    method_fearures[method].append((feature_descrption_string, 0))
                        single_info = {}
                        single_info['year'] = year.name
                        single_info['day'] = day
                        single_info['qid'] = qid
                        single_info['performance'] = performance_dict
                        single_info['features'] = method_fearures
                        info.append(single_info)

        return info

    def _save_data(self):
        self._create_dirs()
        # print "Dest dir is %s" %(self._dest_dir)
        # print "Store data to:\n%s" %(self._training_data_dir)
        self._save_info()





    def _create_dirs(self):

        if self._designate_dest_dir:
            dest_dir_name = self._designate_dest_dir
        else:
            dest_dir_name =  "_".join([convert_feature_string(i) for i in sorted(self._feature_descrption_list) ])
        if self._use_raw:
            dest_dir_name += "_raw_queries"
        else:
            dest_dir_name += "_exp_queries"

        dest_dir = os.path.join(self._top_dest_dir,dest_dir_name)
        
        try_mkdir(dest_dir)

        self._dest_dir = dest_dir

        mb2011_dir = os.path.join(dest_dir,"mb2011")
        try_mkdir(mb2011_dir)
        self._mb2011_data_dir = os.path.join(mb2011_dir,"data")
        try_mkdir(self._mb2011_data_dir)

        mb1516_dir = os.path.join(dest_dir,"mb1516")
        try_mkdir(mb1516_dir)
        self._mb1516_data_dir = os.path.join(mb1516_dir,"data")
        try_mkdir(self._mb1516_data_dir)

        rts2017_dir = os.path.join(dest_dir,"rts2017")
        try_mkdir(rts2017_dir)
        self._rts2017_data_dir = os.path.join(rts2017_dir,"data")
        try_mkdir(self._rts2017_data_dir)


    def _save_info(self):
        info_file = os.path.join(self._mb2011_data_dir,"info")

        with open(info_file,"w") as f:
            f.write(json.dumps(self._mb2011_data,indent=2))

        info_file = os.path.join(self._mb1516_data_dir,"info")

        with open(info_file,"w") as f:
            f.write(json.dumps(self._mb1516_data,indent=2))

        info_file = os.path.join(self._rts2017_data_dir,"info")

        with open(info_file,"w") as f:
            f.write(json.dumps(self._rts2017_data,indent=2))

    


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--use_raw","-ur",action="store_true")
    parser.add_argument("--top_dest_dir","-td",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/DKE/info")
    parser.add_argument("--predictor_data_dir","-pd",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/DKE/predictor_data")
    parser.add_argument("--all_method_file","-mf", default="/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/DKE/all_methods.json",
        help="""
            file that stores all the methods need to be used
        """)
    parser.add_argument("--performance_dir","-pfd", default="/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/DKE/performances/raw",
        help="""
            directory that stores performances for all methods
        """)
    parser.add_argument("--feature_descrption_list","-f",nargs='+')
    parser.add_argument("--designate_dest_dir","-dr")
    args=parser.parse_args()

    performances = {}
    for year in Year:
        year_string = year.name
        performance_file = os.path.join(args.performance_dir,year_string)
        performances[year] = json.load(open(performance_file))

    all_methods = json.load(open(args.all_method_file))
    print args.feature_descrption_list
    data_preparor = DataPreparor(
                        args.predictor_data_dir, args.feature_descrption_list,
                        args.use_raw, all_methods,args.top_dest_dir,
                        args.designate_dest_dir,performances)

    data_preparor.prepare_data()
    



if __name__=="__main__":
    main()

