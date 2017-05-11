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

from disk45_plot_silentDay_predictor import PredictorName,R_DIR,PREDICTOR_CLASS,PredictorClass,RetrievalMethod,load_silent_day,Q_DIR,IndexType

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")











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
    for a subset
    """

    

    # Note the feature format should be "PredictorChoice:Expansion"
    def __init__(self,feature_descrption_string,predictor_data_dir,retrieval_method,index_type):


        self._feature_descrption_string, self._predictor_data_dir =\
             feature_descrption_string, predictor_data_dir

        self._retrieval_method = retrieval_method    
        self._index_type = index_type

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
                            "data")
        else:
            if self._predictor_class == PredictorClass.pre:
                self._data_file_path = os.path.join(
                                self._predictor_data_dir,self._predictor_class.name,
                                self._predictor_choice.name,
                                "data")
            else:
                self._data_file_path = os.path.join(
                                self._predictor_data_dir,self._predictor_class.name,
                                self._predictor_choice.name,
                                self._index_type.name,
                                self._retrieval_method.name,"data")
        # print "Data path:%s" %(self._data_file_path)
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
                 top_dest_dir,retrieval_method,silent_query_info_file,
                 index_type,title_only):
        self._predictor_data_dir,self._feature_descrption_list, self._retrieval_method=\
            predictor_data_dir,feature_descrption_list,retrieval_method
        self._index_type = index_type


        self._top_dest_dir = top_dest_dir
        self._silent_query_info_file = silent_query_info_file
        self._title_only = title_only

    def prepare_data(self):

        # get training data
        self._training_data = self._prepare_vector_data_set()
        self._save_data()

    def _prepare_vector_data_set(self):
        vector_data_set = {
            "features":{},
            "silent_days":{},
            "feature_vector":[],
            "label_vector":[]

        }

            
            

        vector_data_set["silent_days"] = load_silent_day(self._silent_query_info_file)

        # print vector_data_set["silent_days"]
        vector_data_set["features"] = {}
        for feature_descrption_string in self._feature_descrption_list:
            single_feature = SingleFeature(feature_descrption_string,self._predictor_data_dir,self._retrieval_method,self._index_type)
            vector_data_set["features"][feature_descrption_string] = single_feature.feature_data
        
        for day in sorted(vector_data_set["silent_days"].keys()):
            for qid in sorted(vector_data_set["silent_days"][day].keys()):
                if self._title_only:
                    if "title" not in qid:
                        continue
                if vector_data_set["silent_days"][day][qid]:
                    vector_data_set["label_vector"].append(1)        
                else:
                    vector_data_set["label_vector"].append(0)        

                single_feature_vector = []
                for feature_descrption_string in sorted(self._feature_descrption_list):
                    # if vector_data_set["features"][year][feature_descrption_string][day][qid] == .0:
                    #     print "%s %s %s" %(day,qid,vector_data_set["silent_days"][year][day][qid])
                    try:
                        single_feature_vector.append(vector_data_set["features"][feature_descrption_string][day][qid])
                    except KeyError:
                        print "Feature: %s" %(feature_descrption_string)
                        print "Day:%s, query:%s" %(day,qid)
                        single_feature_vector.append(0)
                vector_data_set["feature_vector"].append(single_feature_vector)

        return vector_data_set

    def _save_data(self):
        self._create_dirs()
        print "Store data to:\n%s" %(self._training_data_dir)
        self._save_vectors(self._training_data["feature_vector"],
                           self._training_data["label_vector"],
                           self._training_data_dir)

        # self._save_vectors(self._testing_data["feature_vector"],
        #                    self._testing_data["label_vector"],
        #                    self._testing_data_dir)

        # self._save_feature_dict(self._testing_data,
        #                    self._testing_data_dir)

        self._save_feature_dict(self._training_data,
                           self._training_data_dir)

    def _create_dirs(self):

        dest_dir_name =  "_".join([convert_feature_string(i) for i in sorted(self._feature_descrption_list) ])
        if self._title_only:
            dest_dir = os.path.join(self._top_dest_dir,self._index_type.name,"title_only",self._retrieval_method.name,dest_dir_name)
        else:
            dest_dir = os.path.join(self._top_dest_dir,self._index_type.name,self._retrieval_method.name,dest_dir_name)
        
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

    def _save_feature_dict(self,dataset,dest_data_dir):
        feature_dict = os.path.join(dest_data_dir,"feature_dict")
        label_dict = os.path.join(dest_data_dir,"label_dict")

        with open(feature_dict,"w") as f:
            f.write(json.dumps(dataset["features"]))

        with open(label_dict,"w") as f:
            f.write(json.dumps(dataset["silent_days"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top_dest_dir","-td",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/disk4-5/sday_prediction_data")
    parser.add_argument("--predictor_data_dir","-pd",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/disk4-5/predictor_data")
    parser.add_argument("--silent_query_info_file","-sf",default="/infolab/node4/lukuang/2015-RTS/disk4-5/eval/silent_query_info")
    parser.add_argument("--retrieval_method","-rm",choices=list(map(int, RetrievalMethod)),default=0,type=int,
        help="""
            Choose the retrieval method:
                0:f2exp
                1:dirichlet
                2:pivoted
                3:bm25
        """)
    parser.add_argument("--title_only","-to",action="store_true")
    parser.add_argument("--index_type","-it",choices=list(map(int, IndexType)),default=0,type=int,
        help="""
            Choose the index type:
                0:full
                1:processed
        """)
    parser.add_argument("--feature_descrption_list","-f",nargs='+')
    args=parser.parse_args()


    args.retrieval_method = RetrievalMethod(args.retrieval_method)
    args.index_type = IndexType(args.index_type)

    print args.feature_descrption_list
    data_preparor = DataPreparor(
                        args.predictor_data_dir, args.feature_descrption_list,
                        args.top_dest_dir,args.retrieval_method,
                        args.silent_query_info_file,args.index_type,args.title_only)


    data_preparor.prepare_data()
    



if __name__=="__main__":
    main()

