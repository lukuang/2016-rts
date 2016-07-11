"""
build index for base line
"""

import os
import json
import sys
import re
import argparse
import codecs

from myUtility.misc import gene_indri_index_para_file

def get_day_hour_from_file_name(hour_text_file):
    m = re.search("\d+\-\d+\-(\d+)_(\d+)",hour_text_file)
    if m is None:
        raise ValueError("file name %s not supported!" %(hour_text_file))
    else:
        return int(m.group(1)),int(m.group(2))


def check_file_time(simulate,hour_text_file,method,date):
    if method == "incremental":
        if simulate:
            file_date,file_hour = get_day_hour_from_file_name(hour_text_file)
            if file_date < date:
                return True
            elif file_date==date and file_hour!=23:
                return True
        else:
            return True
    else:
        file_date,file_hour = get_day_hour_from_file_name(hour_text_file)
        if simulate:
            if file_date == date and file_hour!=23:
                return True
        else:
            if file_date == date:
                return True
    return False



def get_file_list(text_dir,date,simulate,method):
    all_files = os.walk(text_dir).next()[2]
    all_files.sort() # solely for debuging purpose
    file_list = []
    for hour_text_file in all_files:
        if check_file_time(simulate,hour_text_file,method,date):
            
            file_list.append(os.path.join(text_dir,hour_text_file))
    
    return file_list

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method_index","-m",type=int,choices=[0,1],
                        default=0, 
                        help = "the method of building index: (individual/incremental)")
    parser.add_argument("--simulate","-s",action='store_true')
    parser.add_argument("date",type=int)
    parser.add_argument("text_dir")
    parser.add_argument("index_para_top_dir")
    parser.add_argument("index_top_dir")
    args=parser.parse_args()

    METHODS = [
        "individual",
        "incremental"
        ]

    method = METHODS[args.method_index] 
    file_list = get_file_list(args.text_dir,args.date,args.simulate,method)
    index_para_file = os.path.join(args.index_para_top_dir,method,str(args.date))
    index_path = os.path.join(args.index_top_dir,method,str(date))
    field_data = [
                {"name":"date", "type":"date"}
            ]
    gene_indri_index_para_file(file_list,index_para_file,
                    index_path,field_data=field_data)


if __name__=="__main__":
    main()

