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

from plot_silentDay_predictor import PredictorName,Expansion,R_DIR,PREDICTOR_CLASS,PredictorClass,RetrievalMethod
from silent_days import SilentDaysFromRes,SilentDaysFromJug

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
    def __init__(self,year,feature_descrption_string,predictor_data_dir,retrieval_method):


        self._year,self._feature_descrption_string, self._predictor_data_dir =\
            year, feature_descrption_string, predictor_data_dir

        self._retrieval_method = retrieval_method    


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
            
            if (self._predictor_choice == PredictorName.coherence_binary_n or
               self._predictor_choice == PredictorName.coherence_average_n or
               self._predictor_choice == PredictorName.coherence_max_n or
               self._predictor_choice == PredictorName.cidf_binary_n or
               self._predictor_choice == PredictorName.cidf_average_n or
               self._predictor_choice == PredictorName.cidf_max_n):
                raise ValueError("Need to specify term size when using %s!" %(self._predictor_choice.name))

            self._predictor_class = PREDICTOR_CLASS[self._predictor_choice]
            self._expansion = Expansion[ detail_finder.group(2) ]
            if self._year != Year.y2016 and self._expansion == Expansion.dynamic:
                self._expansion = Expansion.static
            # print "\t%s" %(" ".join([self._predictor_choice.name,self._predictor_class.name,self._expansion.name]))

        else:
            detail_finder_with_tn = re.search("^(\w+?):(\w+):(\d+)$",self._feature_descrption_string)
            if detail_finder_with_tn :
                self._predictor_choice = PredictorName[ detail_finder_with_tn.group(1) ]
                if (self._predictor_choice == PredictorName.coherence_binary_n or
                   self._predictor_choice == PredictorName.coherence_average_n or
                   self._predictor_choice == PredictorName.coherence_max_n or
                   self._predictor_choice == PredictorName.cidf_binary_n or
                   self._predictor_choice == PredictorName.cidf_average_n or
                   self._predictor_choice == PredictorName.cidf_max_n):
                    
                    self._predictor_class = PREDICTOR_CLASS[self._predictor_choice]
                    self._expansion = Expansion[ detail_finder_with_tn.group(2) ]
                    if self._year != Year.y2016 and self._expansion == Expansion.dynamic:
                        self._expansion = Expansion.static
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
        if self._predictor_class == PredictorClass.post:
            use_result_string = "with_result"
        else:
            use_result_string = "without_result"
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
                            self._expansion.name,use_result_string,"data")
        else:
            if self._predictor_class == PredictorClass.pre:
                self._data_file_path = os.path.join(
                                self._predictor_data_dir,self._predictor_class.name,
                                self._predictor_choice.name,self._year.name,
                                self._expansion.name,use_result_string,"data")
            else:
                self._data_file_path = os.path.join(
                                self._predictor_data_dir,self._predictor_class.name,
                                self._predictor_choice.name,self._year.name,
                                self._expansion.name,self._retrieval_method.name,"data")
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


    def __init__(self,predictor_data_dir,feature_descrption_list,
                 use_result,result_expansion,top_dest_dir,retrieval_method,
                 designate_dest_dir):
        self._predictor_data_dir,self._feature_descrption_list, self._retrieval_method=\
            predictor_data_dir,feature_descrption_list,retrieval_method

        self._use_result,self._result_expansion = use_result,result_expansion

        self._top_dest_dir = top_dest_dir

        self._designate_dest_dir = designate_dest_dir


    def prepare_data(self):

        # get training data
        self._mb2011_data = self._prepare_vector_data_set(MB2011)
        self._mb1516_data = self._prepare_vector_data_set(MB1516)
        self._rts2017_data = self._prepare_vector_data_set(RTS2017)
        self._save_data()

    def _prepare_vector_data_set(self,year_list):
        vector_data_set = {
            "features":{},
            "silent_days":{},
            "feature_vector":[],
            "label_vector":[]

        }

        for year in year_list:
            
            if self._use_result:
                if self._result_expansion == Expansion.raw:
                    result_dir = R_DIR[year][self._result_expansion][self._retrieval_method]
                else:
                    result_dir = R_DIR[year][self._result_expansion]
                silent_day_generator = SilentDaysFromRes(year,result_dir)
            else:
                silent_day_generator = SilentDaysFromJug(year)

            vector_data_set["silent_days"][year] = silent_day_generator.silent_days
            # print vector_data_set["silent_days"][year]


            vector_data_set["features"][year] = {}
            for feature_descrption_string in self._feature_descrption_list:
                single_feature = SingleFeature(year,feature_descrption_string,self._predictor_data_dir,self._retrieval_method)
                vector_data_set["features"][year][feature_descrption_string] = single_feature.feature_data
            
            for day in sorted(vector_data_set["silent_days"][year].keys()):
                for qid in sorted(vector_data_set["silent_days"][year][day].keys()):
                    if vector_data_set["silent_days"][year][day][qid]:
                        vector_data_set["label_vector"].append(1)        
                    else:
                        vector_data_set["label_vector"].append(0)        

                    single_feature_vector = []
                    for feature_descrption_string in sorted(self._feature_descrption_list):
                        # if vector_data_set["features"][year][feature_descrption_string][day][qid] == .0:
                        #     print "%s %s %s" %(day,qid,vector_data_set["silent_days"][year][day][qid])
                        try:
                            single_feature_vector.append(vector_data_set["features"][year][feature_descrption_string][day][qid])
                        except KeyError:
                            # print "Feature: %s" %(feature_descrption_string)
                            # print "Day:%s, query:%s" %(day,qid)
                            single_feature_vector.append(0)
                    vector_data_set["feature_vector"].append(single_feature_vector)

        return vector_data_set

    def _save_data(self):
        self._create_dirs()
        # print "Dest dir is %s" %(self._dest_dir)
        # print "Store data to:\n%s" %(self._training_data_dir)
        self._save_vectors(self._mb2011_data["feature_vector"],
                           self._mb2011_data["label_vector"],
                           self._mb2011_data_dir)

        self._save_vectors(self._mb1516_data["feature_vector"],
                           self._mb1516_data["label_vector"],
                           self._mb1516_data_dir)

        self._save_vectors(self._rts2017_data["feature_vector"],
                           self._rts2017_data["label_vector"],
                           self._rts2017_data_dir)



        self._save_feature_dict(self._mb2011_data,
                           self._mb2011_data_dir)

        self._save_feature_dict(self._mb1516_data,
                           self._mb1516_data_dir)

        self._save_feature_dict(self._rts2017_data,
                           self._rts2017_data_dir)

    def _create_dirs(self):

        if self._designate_dest_dir:
            dest_dir_name = self._designate_dest_dir
        else:
            dest_dir_name =  "_".join([convert_feature_string(i) for i in sorted(self._feature_descrption_list) ])
        if self._use_result:
            dest_dir_name += "_W_result"
        else:
            dest_dir_name += "_Wo_result"
        dest_dir_name += "_"+self._result_expansion.name.title()
        dest_dir = os.path.join(self._top_dest_dir,self._retrieval_method.name,dest_dir_name)
        
        try_mkdir(dest_dir)

        self._dest_dir = dest_dir

        mb2011_dir = os.path.join(dest_dir,"mb2011")
        try_mkdir(mb2011_dir)
        self._mb2011_data_dir = os.path.join(mb2011_dir,"data")
        self._mb2011_model_dir = os.path.join(mb2011_dir,"model")
        try_mkdir(self._mb2011_data_dir)
        try_mkdir(self._mb2011_model_dir)

        mb1516_dir = os.path.join(dest_dir,"mb1516")
        try_mkdir(mb1516_dir)
        self._mb1516_data_dir = os.path.join(mb1516_dir,"data")
        self._mb1516_model_dir = os.path.join(mb1516_dir,"model")
        try_mkdir(self._mb1516_data_dir)
        try_mkdir(self._mb1516_model_dir)

        rts2017_dir = os.path.join(dest_dir,"rts2017")
        try_mkdir(rts2017_dir)
        self._rts2017_data_dir = os.path.join(rts2017_dir,"data")
        self._rts2017_model_dir = os.path.join(rts2017_dir,"model")
        try_mkdir(self._rts2017_data_dir)
        try_mkdir(self._rts2017_model_dir)


    def _save_vectors(self,feature_vector, label_vector, dest_data_dir):
        feature_file = os.path.join(dest_data_dir,"feature")
        label_file = os.path.join(dest_data_dir,"label")

        with open(feature_file,"w") as f:
            f.write(json.dumps(feature_vector))

        with open(label_file,"w") as f:
            f.write(json.dumps(label_vector))

    def _save_feature_dict(self,dataset,dest_data_dir):
        feature_dict = os.path.join(dest_data_dir,"feature_dict")
        label_dict = os.path.join(dest_data_dir,"label_dict")

        with open(feature_dict,"w") as f:
            f.write(json.dumps(dataset["features"]))

        with open(label_dict,"w") as f:
            f.write(json.dumps(dataset["silent_days"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--use_result","-ur",action="store_true")
    parser.add_argument("--top_dest_dir","-td",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/sday_prediction_data_with_2017")
    parser.add_argument("--predictor_data_dir","-pd",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/predictor_data")
    parser.add_argument("--result_expansion","-re",choices=list(map(int, Expansion)),default=0,type=int,
        help="""
            Choose the expansion:
                0:raw
                1:static:
                2:dynamic
        """)
    parser.add_argument("--retrieval_method","-rm",choices=list(map(int, RetrievalMethod)),default=0,type=int,
        help="""
            Choose the retrieval method:
                0:f2exp
                1:dirichlet
                2:pivoted
                3:bm25
        """)
    parser.add_argument("--feature_descrption_list","-f",nargs='+')
    parser.add_argument("--designate_dest_dir","-dr")
    args=parser.parse_args()


    args.result_expansion = Expansion(args.result_expansion)
    args.retrieval_method = RetrievalMethod(args.retrieval_method)

    print args.feature_descrption_list
    data_preparor = DataPreparor(
                        args.predictor_data_dir, args.feature_descrption_list,
                        args.use_result, args.result_expansion,args.top_dest_dir,args.retrieval_method,
                        args.designate_dest_dir)


    data_preparor.prepare_data()
    



if __name__=="__main__":
    main()

