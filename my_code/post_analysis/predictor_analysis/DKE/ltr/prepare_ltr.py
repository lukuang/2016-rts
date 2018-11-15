"""
prepare for ltr from the info files
"""

import os
import json
import sys
import re
import argparse
import codecs

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--info_dir","-id",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/DKE/info")
    parser.add_argument("ltr_dir")
    args=parser.parse_args()

    for dn in os.listdir(args.info_dir):
        top_info_dir = os.path.join(args.info_dir,dn)
        if os.path.isdir(top_info_dir):
            print 'process {}'.format(dn)
            top_ltr_dir = os.path.join(args.ltr_dir,dn)
            if not os.path.exists(top_ltr_dir):
                os.makedirs(top_ltr_dir)
            for y_dn in os.listdir(top_info_dir):
                year_info_dir =  os.path.join(top_info_dir,y_dn)
                if os.path.isdir(year_info_dir):
                    info_file = os.path.join(year_info_dir,'data','info')
                    year_info = json.load(open(info_file))
                    year_ltr_file = os.path.join(top_ltr_dir,y_dn)
                    with open(year_ltr_file,'w') as f:
                        for single_info in year_info:
                            year = single_info['year']
                            day = single_info['day']
                            qid  = single_info['qid'] 
                            new_qid = "{}_{}_{}".format(year,day,qid)
                            performance_dict = single_info['performance']
                            method_fearures = single_info['features']
                            first = True
                            for method, performance in sorted(performance_dict.items(),
                                                              key=lambda x:x[1],
                                                              reverse=True):
                                # if first and performance == 0:
                                #     break
                                train_performance = round(performance*5,4)
                                sample_string = "{} qid:{}".format(train_performance,new_qid)
                                for i in xrange(len(method_fearures[method])):
                                    sample_string += " {}:{}".format(i+1,method_fearures[method][i][1] )
                                sample_string += " #method={} performance={}\n".format(method, round(performance,4))
                                # sample_string += " #method={}\n".format(method, performance)
                                f.write(sample_string)
if __name__=="__main__":
    main()

