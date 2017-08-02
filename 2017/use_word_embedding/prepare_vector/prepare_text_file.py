"""
prepare vector training text file from trec format text files
"""

import os
import json
import sys
import re
import argparse
import codecs
from datetime import date, timedelta
# sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
# from my_code.distribution.data import Year

def find_inclusive_intermediate_days(begin_month,begin_date,
                                     end_month,end_date,year):
    intermediate_days = []
    begin = date(year,begin_month,begin_date)
    end = date(year,end_month,end_date)
    delta = end - begin
    for i in range(delta.days+1):
        month = (begin + timedelta(days=i)).month
        day = (begin + timedelta(days=i)).day
        intermediate_days.append( [month,day] )

    return intermediate_days

def check_file_name(year,intermediate_days,file_name):
    if year == "2015":
        m = re.search("(\d+)-(\d+)",file_name)
        now_day = int(m.group(2))
        for date in intermediate_days:
            if now_day ==  date[1]:
                return True

        return False
    elif year == "2016":
        return False


def get_file_list(src_dir,year,intermediate_days):
    file_list = []
    for file_name in os.walk(src_dir).next()[2]:
        if check_file_name(year,intermediate_days,file_name):
            file_list.append( os.path.join(src_dir,file_name) )
    return file_list



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("begin_month",type=int)
    parser.add_argument("begin_date",type=int)
    parser.add_argument("end_month",type=int)
    parser.add_argument("end_date",type=int)
    parser.add_argument("year",choices=["2015","2016","2017"],
        help="""
            Choose the year:
                2015
                2016
                2017
        """)
    parser.add_argument("src_dir")
    parser.add_argument("dest_file")
    args=parser.parse_args()


    year_value = int(args.year)
    intermediate_days = find_inclusive_intermediate_days(
                            begin_month,begin_date,
                            end_month,end_date,year_value
                        )
    file_list = get_file_list(args.src_dir,args.year,intermediate_days)

    text_string_for_all = ""

    in_text = False
    for single_file in file_list:
        with open(single_file) as f:
            print "Process file: %s" %(single_file)
            for line in f:
                if not in_text:
                    m = re.search("<TEXT>(.+)",line)
                    if m is not None:
                        in_text = True
                        text_string_for_all += " "+m.group(1).strip()
                else:
                    m2 = re.search("^(.+?)</TEXT>",line)
                    if m2 is not None:
                        in_text = False
                        text_string_for_all += " "+m2.group(1).strip()
                    else:
                        text_string_for_all += " "+line.strip()

    with open(args.dest_file,"w") as of:
        of.write(text_string_for_all)




if __name__=="__main__":
    main()

