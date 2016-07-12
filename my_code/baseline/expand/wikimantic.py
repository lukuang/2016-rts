"""
code for expansion using wikimantic
"""

import os
import json
import sys
import re
import argparse
import codecs
from myUtility.corpus import Model

sys.path.append("../../")

from process_query import read_query_file





def generate_wikimantic_input(queries,wikimantic_input_dir):
     
    
    for qid in queries:
        wikimantic_input_file = os.path.join(wikimantic_input_dir,qid)

        if not os.path.exists(wikimantic_input_file):
            print "generating %s wikimantic input at: %s" %(qid,wikimantic_input_file)
            
            with codecs.open(wikimantic_input_file,"w","utf-8") as f:
                words = re.findall("\w+",queries[qid].lower())
                size = len(words)
                for i in range(size):
                    for j in range(i,size):
                        pid = "".join(map(str,range(i,j+1)))
                        phrase = "_".join(words[i:j+1])
                        #print "%s:%s" %(pid,phrase)
                        f.write("%s:%s:%s\n" %(qid,pid,phrase))
        else:
            print "input file %s already exists" %(wikimantic_input_file)
            print "skip query %s" %qid
        


def generate_wikimantic_output(
            wikimantic_jar_file,wikimantic_graph_file,
            wikimantic_input_dir,wikimantic_output_dir):
    
    for qid in os.walk(wikimantic_input_dir).next()[2]:
        wikimantic_output_file = os.path.join(wikimantic_output_dir,qid)
        
        if not os.path.exists(wikimantic_output_file):
            wikimantic_input_file = os.path.join(wikimantic_input_dir,qid)

            print "generating wikimantic output at: %s" %(wikimantic_output_file)
            os.system("java -jar %s %s %s %s" %(wikimantic_jar_file,
                                                wikimantic_graph_file,
                                                wikimantic_input_file,
                                                wikimantic_output_file))
            
        else:
            print "output file %s already exists" %(wikimantic_output_file)
            print "skip query %s" %qid

def write_expansion(wikimantic_output_dir,expansion_file):
    all_model = {}
    size = 0
    for line in f:
        line = line.rstrip()
        parts = line.split()
        qid = part[0]
        pid = part[1]

        #get the length of the query
        size = max(int(len(pid)),size)

        term = part[2]
        weight = float(part[3])
        if pid not in all_model:
            all_model[pid] = {}
        all_model[pid][term] = weight

    # remove "sub-strings of sub-strings" 
    print "original phrases:\n%s\n" %(all_model.keys())
    for a_pid in sorted(all_model.keys(),key=lambda x:len(x),reverse=True):
        for b_pid in all_model.keys():
            if a_pid != b_pid:
                if a_pid.find(b_pid) != -1:
                    all_model.pop(b_pid,None)

    print "now phrases:\n%s\n" %(all_model.keys())

    expanding_model = Model(False,text_dict={})
    for pid in all_model:
        
        model_weight = len(pid)*1.0/size
        print "for phrase %s weight is %f" %(pid,model_weight)
        single_phrase_model = Model(False,text_dict=all_model[pid])
        single_phrase_model.normalize()
        single_phrase_model *= model_weight

        
        expanding_model += single_phrase_model

        
    expanding_model.normalize()
    

    with codecs.open(wikimantic_output_dir,"r","utf8") as f:
        f.write(json.dumps(expanding_model.model,indent=4))






def generate_expansion(wikimantic_output_dir,expansion_dir):
    for qid in os.walk(wikimantic_output_dir).next()[2]:
        expansion_file = os.path.join(expansion_dir,qid)

        if not os.path.exists(expansion_file):
            wikimantic_output_file = os.path.join(wikimantic_output_dir,qid)
            write_expansion(wikimantic_output_dir,expansion_file)



        else:
            print "expansion file %s exists" %expansion_file
            print "skip query %s" %qid

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_query_file")
    parser.add_argument("query_type",choices=["2015_mb","json_mb","wt2g"])
    parser.add_argument("query_field",choices=["title","desc","combine"])
    parser.add_argument("wikimantic_input_dir")
    parser.add_argument("wikimantic_output_dir")
    parser.add_argument("wikimantic_jar_file")
    parser.add_argument("wikimantic_graph_file")
    parser.add_argument("expansion_dir")
    args=parser.parse_args()

    queries = read_query_file(args.original_query_file,args.query_type,args.query_field)
    generate_wikimantic_input(queries,args.wikimantic_input_dir)


    generate_wikimantic_output(args.wikimantic_jar_file,
                               args.wikimantic_graph_file,
                               args.wikimantic_input_dir,
                               args.wikimantic_output_dir)

    generate_expansion(args.wikimantic_output_dir,args.expansion_dir)

    




if __name__=="__main__":
    main()

