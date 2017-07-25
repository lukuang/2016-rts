"""
get the logs of previously posted tweets
"""

import os
import json
import sys
import re
import argparse
import codecs

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run_name_file","-rf",default="/infolab/headnode2/lukuang/2017-rts/data/communication/runs")
    parser.add_argument("--basic_file","-bf",default="/infolab/headnode2/lukuang/2017-rts/data/communication/basic")
    parser.add_argument("--log_dir","-ld",default="/infolab/headnode2/lukuang/2017-rts/data/communication/logs")
    args=parser.parse_args()


    basic_info = json.load(open(args.basic_file)) 
    if basic_info is None:
        raise RuntimeError("Need to have a valid basic file %s" %basic_file)
    hostname =  basic_info["hostname"]


    run_info = json.load(open(args.run_name_file))
    for run_name in run_info:
        clientid = run_info[run_name]
        log_request_url = "%s/log/%s" %(hostname,clientid)
        dest_file = os.path.join(args.log_dir,run_name)
        os.system("curl %s > %s" %(log_request_url,dest_file))




if __name__=="__main__":
    main()

