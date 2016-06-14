"""
compare id lists
"""

import os
import json
import sys
import re
import argparse
import codecs
from collections import namedtuple

START = "622918845364219905"
END = "626542493325205504"
CHECK_TIME = False

def get_line(f):
    if CHECK_TIME:
        while True:
            line = f.readline().rstrip()
            if len(line)==0:
                return line
            elif START<=line<=END:
                return line
    else:
        return f.readline().rstrip()



def compare(list1,list2,dest_dir):
    common = []
    unique = {
        "1":[],
        "2":[],
    }
    stop1 = False
    stop2 = False
    i = 0
    found = False
    with open(list1) as f1, \
            open(list2) as f2:
        line1 = get_line(f1)
        line2 = get_line(f2)
        print line1,line2
        while len(line1)!=0 and len(line2)!=0:
            #if found:
            #    print line1, line2
            if len(line2)==0:
                
                unique["1"].append(line1)
                line1 = get_line(f1)
            elif len(line1)==0:
                

                unique["2"].append(line2)
                line2 = get_line(f2)
            else:
                #print line1,line2
                if line2 < line1:
                    

                    #print "unque2"
                    unique["2"].append(line2)
                    line2 = get_line(f2)
                elif line2 == line1:
                    #print "common"
                    

                    common.append(line1)
                    line1 = get_line(f1)
                    line2 = get_line(f2)
                else:
                    #print "unique1"
                    
                    unique["1"].append(line1)
                    line1 = get_line(f1)

            i += 1
            #if i==100:
            #    break
            if i%100000==0:
                #print "processed %d lines" %(i)
                #print line1, line2
                #print len(common),len(unique["1"]),len(unique["2"])
                with open(os.path.join(dest_dir, "common"),"a" ) as f:
                    for line in common:
                        f.write(line+"\n")


                with open(os.path.join(dest_dir, "unqiue1"),"a" ) as f:
                    for line in unique["1"]:
                        f.write(line+"\n")

                with open(os.path.join(dest_dir, "unqiue2"),"a" ) as f:
                    for line in unique["2"]:
                        f.write(line+"\n")
                common = []
                unique = {
                            "1":[],
                            "2":[],
                        }
        with open(os.path.join(dest_dir, "common"),"a" ) as f:
                    for line in common:
                        f.write(line+"\n")


        with open(os.path.join(dest_dir, "unqiue1"),"a" ) as f:
            for line in unique["1"]:
                f.write(line+"\n")

        with open(os.path.join(dest_dir, "unqiue2"),"a" ) as f:
            for line in unique["2"]:
                f.write(line+"\n")




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("list1")
    parser.add_argument("list2")
    parser.add_argument("dest_dir")
    args=parser.parse_args()
    compare(args.list1,args.list2,args.dest_dir)

if __name__=="__main__":
    main()

