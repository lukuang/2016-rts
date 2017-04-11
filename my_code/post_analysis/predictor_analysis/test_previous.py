"""
test all the combination of the previously proposed features
"""

import os
import json
import sys
import re
import argparse
import codecs
import itertools  
from enum import IntEnum, unique
from sklearn.metrics import f1_score as f1
import cPickle

from plot_silentDay_predictor import PredictorName,Expansion,R_DIR,PREDICTOR_CLASS,RetrievalMethod
from silent_days import SilentDaysFromRes,SilentDaysFromJug

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year



@unique
class PredictorClass(IntEnum):
    post = 0
    pre = 1


class DataSet(object):
    """Dataset
    """
    def __init__(self,dataset_dir):
        self._dataset_dir = dataset_dir
        self._load_data_set()

    def _load_data_set(self):
        self._X = json.load(open(os.path.join(self._dataset_dir,"feature")))
        self._y = json.load(open(os.path.join(self._dataset_dir,"label")))

    @property
    def X(self):
        return self._X
    
    @property
    def y(self):
        return self._y
    

def load_data(top_data_dir):
    training_dir = os.path.join(top_data_dir,"training","data")
    dataset_11 = DataSet(training_dir)

    testing_dir = os.path.join(top_data_dir,"testing","data")
    dataset_1516 = DataSet(testing_dir)

    return dataset_11, dataset_1516


def get_classifier(method):
    if method == 0:
        from sklearn.svm import SVC
        classifier = SVC(kernel="linear",C=1)
        # classifier = SVC()
    elif method == 1:
        from sklearn import linear_model
        classifier = linear_model.LogisticRegression(C=1e5)
    elif method == 2:
        from sklearn.naive_bayes import GaussianNB
        classifier = GaussianNB()
    elif method == 3:
        from sklearn import tree
        classifier = tree.DecisionTreeClassifier()
    elif method == 4:
        from sklearn.ensemble import ExtraTreesClassifier
        classifier = ExtraTreesClassifier()
    else:
        from sklearn.ensemble import RandomForestClassifier
        classifier = RandomForestClassifier()

    return classifier



TRAINING_YEAR = [Year.y2011]
TESTING_YEAR = [Year.y2015,Year.y2016]




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
                 use_result,result_expansion,top_dest_dir,retrieval_method):
        self._predictor_data_dir,self._feature_descrption_list, self._retrieval_method=\
            predictor_data_dir,feature_descrption_list,retrieval_method

        self._use_result,self._result_expansion = use_result,result_expansion

        self._top_dest_dir = top_dest_dir


    def prepare_data(self):

        # get training data
        existed = self._create_dirs()

        if not existed:
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
                result_dir = R_DIR[year][self._result_expansion][self._retrieval_method.name]
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
        
        # print "Store data to:\n%s" %(self._training_data_dir)
        self._save_vectors(self._training_data["feature_vector"],
                           self._training_data["label_vector"],
                           self._training_data_dir)

        self._save_vectors(self._testing_data["feature_vector"],
                           self._testing_data["label_vector"],
                           self._testing_data_dir)

        self._save_feature_dict(self._testing_data,
                           self._testing_data_dir)

        self._save_feature_dict(self._training_data,
                           self._training_data_dir)

    def _create_dirs(self):

        dest_dir_name =  "_".join([convert_feature_string(i) for i in sorted(self._feature_descrption_list) ])
        if self._use_result:
            dest_dir_name += "_W_result"
        else:
            dest_dir_name += "_Wo_result"
        dest_dir_name += "_"+self._result_expansion.name.title()
        dest_dir = os.path.join(self._top_dest_dir,self._retrieval_method.name,dest_dir_name)
        self._dest_dir = dest_dir
        
        if os.path.exists(dest_dir):
            return True
        else:
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
            return False


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

    @property
    def dest_dir(self):
        return self._dest_dir
    

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--use_result","-ur",action="store_true")
    parser.add_argument("--top_dest_dir","-td",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/sday_prediction_data")
    parser.add_argument("--predictor_data_dir","-pd",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/predictor_data")
    parser.add_argument("--retrieval_method","-rm",choices=list(map(int, RetrievalMethod)),default=0,type=int,
        help="""
            Choose the retrieval method:
                0:f2exp
                1:dirichlet
                2:pivoted
                3:bm25
        """)
    parser.add_argument("--result_expansion","-re",choices=list(map(int, Expansion)),default=0,type=int,
        help="""
            Choose the expansion:
                0:raw
                1:static:
                2:dynamic
        """)
    args=parser.parse_args()


    args.result_expansion = Expansion(args.result_expansion)
    args.retrieval_method = RetrievalMethod(args.retrieval_method)

    previous_features = {
        "clarity:raw":"post",
        "average_idf:raw":"pre",
        "dev:raw":"post",
        "ndev:raw":"post",
        "top_score:raw":"post",
        "query_length:raw":"pre",
        "avg_pmi:raw":"pre",
        "max_pmi:raw":"pre",
        "scq:raw":"pre",
        "var:raw":"pre",
        "nqc:raw":"post",
        "wig:raw":"post",
        "qf:raw":"post",
    }

    if args.retrieval_method == RetrievalMethod.dirichlet:
        previous_features.pop("ndev:raw",None)

    f_positive_max = .0
    f_avg_max = .0
    f_avg_features = ""
    f_positive_features = ""
    # f_avg_method_id = 0

    # f_silent_max = .0
    # f_silent_features = ""
    # f_silent_method_id = 0

    for i in range( len(previous_features) ):
        feature_size = i+1
        for feature_set in itertools.combinations(previous_features.keys(),feature_size):
            feature_descrption_list = []
            # use_result = False
            for feature_string in feature_set:
                feature_descrption_list.append(feature_string)

                #decide whether the result needs to be used
                # if(previous_features[feature_string] == "post"):
                #     use_result = True
            # print feature_descrption_list
            # print use_result



            # print feature_descrption_list
            data_preparor = DataPreparor(
                                args.predictor_data_dir, feature_descrption_list,
                                args.use_result, args.result_expansion,
                                args.top_dest_dir,args.retrieval_method)


            data_preparor.prepare_data()

            dest_dir = data_preparor.dest_dir

            dataset_11, dataset_1516 = load_data(dest_dir)
            # method_ids = range(6)

            clf_11 = get_classifier(2)
            clf_11.fit(dataset_11.X,dataset_11.y)
            predicted_1516 = clf_11.predict(dataset_1516.X)

            clf_11_file = os.path.join(dest_dir,"training","model","clf")
            with open(clf_11_file,'w') as f:
                cPickle.dump(clf_11, f, protocol=cPickle.HIGHEST_PROTOCOL)

            clf_1516 = get_classifier(2)
            clf_1516.fit(dataset_1516.X,dataset_1516.y)
            predicted_11 = clf_1516.predict(dataset_11.X)
            f1_1516 = f1(dataset_1516.y, predicted_1516)
            f1_11 = f1(dataset_11.y, predicted_11)
            # if f_silent > f_silent_max:
            #     f_silent_max = f_silent
            #     f_silent_features = feature_descrption_list

            # f_non_silent = f1(dataset_1516.y, test_predicted,average='binary',pos_label=0)
            f_positive = (f1_1516 + f1_11)/2.0

            f1_1516_macro = f1(dataset_1516.y, predicted_1516,average="macro")

            f1_11_macro = f1(dataset_11.y, predicted_11,average="macro")
            f1_macro_average = (f1_1516_macro+f1_11_macro)/2.0


            print "Features:\t%s" %(" ".join(feature_descrption_list) )
            print "15 f1:%f, 11 f1:%f" %(f1_1516,f1_11)
            print "positive f1:\t %f" %(f_positive)
            if f_positive > f_positive_max:
                f_positive_max = f_positive
                f_positive_features = feature_descrption_list

            print "average f1:\t %f" %(f1_macro_average) 
            if f1_macro_average > f_avg_max:
                f_avg_max = f1_macro_average
                f_avg_features = feature_descrption_list

    print "-"*20
    print "The best f1 positive:"
    print "f1:%f" %(f_positive_max)
    print "features: %s" %(f_positive_features)

    print "-"*20
    print "The best f1 avg:"
    print "f1:%f" %(f_avg_max)
    print "features: %s" %(f_avg_features)



if __name__=="__main__":
    main()

