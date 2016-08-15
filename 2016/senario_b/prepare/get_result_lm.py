"""
get language model for each query each day using result file
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess

from myUtility.corpus  import Model


def get_text(index_dir,tweet_id):
    run_command = "dumpindex %s dt `dumpindex %s di docno %s`"\
            %(index_dir,index_dir,tweet_id)

    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    content = p.communicate()[0]
    m = re.search("<TEXT>(.+?)</TEXT>",content,re.DOTALL)
    if m is not None:
        return m.group(1)
    else:
        return None

def get_results(result_dir,name_pattern,num_of_results):
    # return the result as {qid: {day: [tid]} }
    results = {}
    for file_name in os.walk(result_dir).next()[2]:
        m = name_pattern.search(file_name)
        if m:
            day = m.group(1)

            result_file = os.path.join(result_dir,file_name)
            with open(result_file) as f:
                count = {}
                for line in f:
                    parts = line.split()
                    qid = parts[0]
                    
                    
                    if qid not in count:
                        count[qid] = 0
                    if count[qid] == num_of_results:
                        continue

                    count[qid] += 1
                    tid = parts[2]
                    if qid not in results:
                        results[qid] = {}
                    if day not in results[qid]:
                        results[qid][day] = []
                    results[qid][day].append(tid)
    return results


def get_models(results,index_dir):
    models = {}
    for qid in results:
        if qid not in models:
            models[qid] = {}
        for day in results[qid]:
            single_model = Model(True,need_stem=True)
            for tid in results[qid][day]:
                text = get_text(index_dir,tid)
                if text:
                    single_model.update(text_string=text)
            single_model.normalize()     
            models[qid][day] = single_model.model
    
    return models





def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir")
    parser.add_argument("--index_dir","-id",default="/infolab/headnode2/lukuang/2016-rts/data/incremental_index")
    parser.add_argument("--num_of_results","-n",type=int,default=100)
    parser.add_argument("--pattern","-p",default="(\d+)")
    parser.add_argument("dest_file")
    args=parser.parse_args()
    name_pattern = re.compile("%s" %args.pattern)
    results = get_results(args.result_dir,name_pattern,args.num_of_results)
    #print results
    models = get_models(results,args.index_dir)
    with open(args.dest_file,'w') as f:
        f.write(json.dumps(models))

if __name__=="__main__":
    main()

