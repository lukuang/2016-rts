"""
prepare the data for silent day prediction by using predictor
"""

import os
import json
import sys
import re
import argparse
import codecs
from enum import IntEnum, unique

from plot_silentDay_predictor import PredictorName,Expansion,R_DIR
from silent_days import SilentDaysFromRes,SilentDaysFromJug

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year



@unique
class PredictorClass(IntEnum):
    post = 0
    pre = 1


TRAINING_YEAR = [Year.y2011, Year.y2015]
TESTING_YEAR = [Year.y2016]

# predictor class dictionary used for getting predictor class
# from predictor name
PREDICTOR_CLASS = {
    PredictorName.clarity : PredictorClass.post,
    PredictorName.standard_deviation : PredictorClass.post,
    PredictorName.n_standard_deviation : PredictorClass.post,
    PredictorName.top_score : PredictorClass.post,
    PredictorName.average_idf : PredictorClass.pre

}


def try_mkdir(wanted_dir):
    if os.path.exists(wanted_dir):
        # raise RuntimeError("dir already exists: %s" %(wanted_dir))
        print "WARNING!:dir already exists: %s" %(wanted_dir)
    else:
        os.mkdir(wanted_dir)


def convert_feature_string(feature_string):
    feature_string = re.sub(":","_",feature_string)
    feature_string = feature_string[0].upper()+feature_string[1:]
    
    return feature_string

class SingleFeature(object):
    """
    class for getting data for a single feature
    for a year
    """

    

    # Note the feature format should be "PredictorChoice:Expansion"
    def __init__(self,year,feature_descrption_string,predictor_data_dir):


        self._year,self._feature_descrption_string, self._predictor_data_dir =\
            year, feature_descrption_string, predictor_data_dir

        self._get_feature_detail()

        self._get_data()


    def _get_feature_detail(self):
        """
        get feature detail form feature_descrption_string
        """
        detail_finder = re.search("^(\w+?):(\w+)$",self._feature_descrption_string)
        print "For year %s, the features used:" %(self._year.name)
        if detail_finder:
            self._predictor_choice = PredictorName[ detail_finder.group(1) ]
            self._predictor_class = PREDICTOR_CLASS[self._predictor_choice]
            self._expansion = Expansion[ detail_finder.group(2) ]
            print "\t%s" %(" ".join([self._predictor_choice.name,self._predictor_class.name,self._expansion.name]))

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
        self._data_file_path = os.path.join(
                            self._predictor_data_dir,self._predictor_class.name,
                            self._predictor_choice.name,self._year.name,
                            self._expansion.name,use_result_string,"data")
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
                 use_result,result_expansion,top_dest_dir):
        self._predictor_data_dir,self._feature_descrption_list, =\
            predictor_data_dir,feature_descrption_list

        self._use_result,self._result_expansion = use_result,result_expansion

        self._top_dest_dir = top_dest_dir

    def prepare_data(self):

        # get training data
        self._training_data = self._prepare_vector_data_set(TRAINING_YEAR)
        self._testing_data = self._prepare_vector_data_set(TESTING_YEAR)
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
                result_dir = R_DIR[year][self._result_expansion]
                silent_day_generator = SilentDaysFromRes(year,result_dir)
            else:
                silent_day_generator = SilentDaysFromJug(year)

            vector_data_set["silent_days"][year] = silent_day_generator.silent_days
            # print vector_data_set["silent_days"][year]


            vector_data_set["features"][year] = {}
            for feature_descrption_string in self._feature_descrption_list:
                single_feature = SingleFeature(year,feature_descrption_string,self._predictor_data_dir)
                vector_data_set["features"][year][feature_descrption_string] = single_feature.feature_data
            
            for day in vector_data_set["silent_days"][year]:
                for qid in vector_data_set["silent_days"][year][day]:
                    if vector_data_set["silent_days"][year][day][qid]:
                        vector_data_set["label_vector"].append(1)        
                    else:
                        vector_data_set["label_vector"].append(0)        

                    single_feature_vector = []
                    for feature_descrption_string in sorted(self._feature_descrption_list):
                        single_feature_vector.append(vector_data_set["features"][year][feature_descrption_string][day][qid])
                    
                    vector_data_set["feature_vector"].append(single_feature_vector)

        return vector_data_set

    def _save_data(self):
        self._create_dirs()

        self._save_vectors(self._training_data["feature_vector"],
                           self._training_data["label_vector"],
                           self._training_data_dir)

        self._save_vectors(self._testing_data["feature_vector"],
                           self._testing_data["label_vector"],
                           self._testing_data_dir)

    def _create_dirs(self):

        dest_dir_name =  "_".join([convert_feature_string(i) for i in sorted(self._feature_descrption_list) ])
        if self._use_result:
            dest_dir_name += "_W_result"
        else:
            dest_dir_name += "_Wo_result"
        dest_dir_name += "_"+self._result_expansion.name.title()
        dest_dir = os.path.join(self._top_dest_dir,dest_dir_name)
        
        try_mkdir(dest_dir)

        training_dir = os.path.join(dest_dir,"training")
        try_mkdir(training_dir)
        self._training_data_dir = os.path.join(training_dir,"data")
        self._training_model_dir = os.path.join(training_dir,"model")
        try_mkdir(self._training_data_dir)
        try_mkdir(self._training_model_dir)

        testing_dir = os.path.join(dest_dir,"testing")
        try_mkdir(testing_dir)
        self._testing_data_dir = os.path.join(testing_dir,"data")
        try_mkdir(self._testing_data_dir)


    def _save_vectors(self,feature_vector, label_vector, dest_data_dir):
        feature_file = os.path.join(dest_data_dir,"feature")
        label_file = os.path.join(dest_data_dir,"label")

        with open(feature_file,"w") as f:
            f.write(json.dumps(feature_vector))

        with open(label_file,"w") as f:
            f.write(json.dumps(label_vector))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--use_result","-ur",action="store_true")
    parser.add_argument("--top_dest_dir","-td",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/sday_prediction_data")
    parser.add_argument("--predictor_data_dir","-pd",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/predictor_data")
    parser.add_argument("--result_expansion","-re",choices=list(map(int, Expansion)),default=0,type=int,
        help="""
            Choose the expansion:
                0:raw
                1:static:
                2:dynamic
        """)
    parser.add_argument("--feature_descrption_list","-f",nargs='+')
    args=parser.parse_args()


    args.result_expansion = Expansion(args.result_expansion)

    print args.feature_descrption_list
    data_preparor = DataPreparor(
                        args.predictor_data_dir, args.feature_descrption_list,
                        args.use_result, args.result_expansion,args.top_dest_dir)


    data_preparor.prepare_data()
    



if __name__=="__main__":
    main()

