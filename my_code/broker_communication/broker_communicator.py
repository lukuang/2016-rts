"""
class for communicate to the broker
"""

import os
import json
import sys
import re
import argparse
import codecs
import requests
from time import gmtime, strftime

def now():
    return strftime("%Y-%m-%d %H:%M:%S", gmtime()) 


class BrokerCommunicator(object):
    def __init__(self,basic_file,run_name_file,topic_file,debug=False):
        self.hostname,self.port,self.groupid = \
            self.process_basic_file(basic_file)

        self.run_name_file,self.topic_file,self.debug = \
            run_name_file,topic_file,debug
        
        self.runids = self.process_run_name_file(run_name_file)
        self._topics = self.process_topic_file(topic_file)
        self.base_end_point = "http://%s:%s" %(self.hostname,self.port)
        self.register_end_point = "%s/register/system" %(self.base_end_point)
        

        




    
    def load_json(self,file_name):
        if os.path.exists(file_name):
            f_size = os.stat(file_name).st_size
            if f_size!=0:
                return json.load(open(file_name))
        else:
            return None
    
    def process_basic_file(self,basic_file):
        data= self.load_json(basic_file) 
        if data is None:
            raise RuntimeError("Need to have a valid basic file %s" %basic_file)
        return data["hostname"],data["port"],data["groupid"]


    
    def process_run_name_file(self,run_name_file):
        runids = self.load_json(run_name_file)
        if runids is None:
            runids = {}
        return runids
        

    
    def process_topic_file(self,topic_file):
        topics = self.load_json(topic_file)
        if topics is None:
            topics = []
        return 

    def register_run(self,run_name):
        if run_name not in self.runids:
            print "Register new run",run_name
            r = requests.post(self.register_end_point,
                     json = {'groupid':self.groupid,
                             'alias':run_name
                            }
                )
            if r.status_code == requests.codes.ok:
                self.clientid = r.json()["clientid"]
                print "clientid: %s" %(self.clientid)
                self.runids[run_name] = self.clientid
                with open(self.run_name_file,"w") as f:
                    f.write(json.dumps(self.runids,indent=4))
            else:
                raise RuntimeError("get error when requesting %s with error code %s" 
                                    %(r.url, r.status_code)
                                    )
        else:
            self.clientid = self.runids[run_name]
            print "run already exists with id %s" %(self.clientid)

        self.poll_topic_end_point = "%s/topics/%s" %(self.base_end_point,
                                                     self.clientid)

    def poll_topics(self):
        r = requests.get(self.poll_topic_end_point)
        print "poll topics at %s" %(now())
        if r.status_code == requests.codes.ok:
            topics = r.json()
            if len(topics)!=self._topics:
                for t in topics:
                    if t not in self._topics:
                        self._topics.append(t)
                with open(self.topic_file,"w") as f:
                    f.write(json.dumps(self._topics,indent=4))

        else:
            raise RuntimeError("get error when requesting %s with error code %s" 
                                %(r.url, r.status_code)
                                )


    
    @property
    def topics(self):
        return self._topics
    

    def post_tweet(self,topic_id,tweet_id):
        post_tweet_end_point = "%s/tweet/%s/%s/%s" %(self.base_end_point,
                                                     topic_id,
                                                     tweet_id,
                                                     self.clientid)

        r = requests.post(post_tweet_end_point) 
        if r.status_code == requests.codes.no_content:
            if self.debug:
                print "Successfully post tweet %s for topic %s" %(tweet_id,topic_id)
        else:
            raise RuntimeError("get error when requesting %s with error code %s" 
                                %(r.url, r.status_code)
                                )



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("basic_file")
    parser.add_argument("run_name_file")
    parser.add_argument("topic_file")
    parser.add_argument("run_name")
    parser.add_argument("--tweet_id","-tw",default="738418531520352258")
    parser.add_argument("--topic_id","-to",default="MB226")
    parser.add_argument("--debug","-de",action='store_true')
    args=parser.parse_args()

    communicator = BrokerCommunicator(args.basic_file,args.run_name_file,\
                        args.topic_file,args.debug)
    communicator.register_run(args.run_name)
    communicator.poll_topics()
    communicator.post_tweet(args.topic_id,args.tweet_id)

if __name__=="__main__":
    main()

