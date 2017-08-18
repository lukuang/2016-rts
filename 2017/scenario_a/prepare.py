"""
read topics from server and prepare expansion data/query
"""

import os
import json
import sys
import re
import argparse
import codecs
import time
from datetime import timedelta
from abc import ABCMeta,abstractmethod
import logging
import logging.handlers

from myUtility.indri import IndriQueryFactory

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.baseline.snippets import *
from my_code.crawler import snippets_crawler
from my_code.broker_communication import BrokerCommunicator


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) 

def need_wait():
    # compute how many secs need to wait before next update
    # queries
    time_struct =  time.gmtime() 
    wait_hours = 23 - time_struct.tm_hour
    wait_minutes = 60 - time_struct.tm_min
    total_secs = timedelta(hours=wait_hours,minutes=wait_minutes).total_seconds()
    print "now is %s" %(now())
    print "need to wait %d hours %d minutes, which is %f seconds" %(wait_hours,wait_minutes,total_secs)
    return int(total_secs)



class Preparator(object):
    """Base class for preparation of 
    different type of runs
    """
    __metaclass__ = ABCMeta
    def __init__(self,dest_query_dir,index_dir,runid,crawl_limit):
        self._dest_query_dir, self._index_dir, self._runid, self._crawl_limit\
            =  dest_query_dir, index_dir, runid,crawl_limit

        self._retrieval_method = "method:f2exp,s:0.1"


    @abstractmethod
    def prepare(self,new_queries,date):
        pass

    @abstractmethod
    def _generate_query():
        pass


class StaticPreparator(Preparator):
    """class used for generate Static queries
    """

    def __init__(self,dest_query_dir,index_dir,runid,snippets_dir,beta,crawl_limit):
        super(StaticPreparator,self).__init__(dest_query_dir,index_dir,runid,crawl_limit)
        self._snippets_dir,self._beta = snippets_dir,beta
        self._queries = {}
        self._setup()


    def _setup(self):
        """set up the paths
        """
        self._raw_dir = os.path.join(self._snippets_dir,"raw","static")
        if not os.path.exists(self._raw_dir):
            os.mkdir(self._raw_dir)

        self._trec_dir = os.path.join(self._snippets_dir,"trec","static")
        if not os.path.exists(self._trec_dir):
            os.mkdir(self._trec_dir)

        self._temp_dir = os.path.join(self._snippets_dir,"temp","static")
        if not os.path.exists(self._temp_dir):
            os.mkdir(self._temp_dir)

        self._para_dir = os.path.join(self._snippets_dir,"para","static")
        if not os.path.exists(self._para_dir):
            os.mkdir(self._para_dir)

        self._snippet_result_dir = os.path.join(self._snippets_dir,"result","static")
        if not os.path.exists(self._snippet_result_dir):
            os.mkdir(self._snippet_result_dir)

        self._snippet_index_dir = os.path.join(self._snippets_dir,"index","static")
        if not os.path.exists(self._snippet_index_dir):
            os.mkdir(self._snippet_index_dir)

        


        self._index_para = os.path.join(self._para_dir,"index_para")

        self._temp_query_para = os.path.join(self._para_dir,"temp_query_para")

        self._index_list = os.path.join(self._para_dir,"static_index_list")
        
        self._orf = os.path.join(self._snippet_result_dir,"orf")

        self._oqf = os.path.join(self._temp_dir,"oqf")
        
        self._temp_output = os.path.join(self._temp_dir,"temp_output")

        with open(self._index_list,"w") as f:
            f.write(self._snippet_index_dir+"\n")

        self._temp_query_builder = IndriQueryFactory(count=10000,
                                    rule=self._retrieval_method)

        self._oqf_builder = IndriQueryFactory(count=30,
                            rule=self._retrieval_method)



    def prepare(self,new_queries,dates):
        if new_queries:
            new_queries = self._process_original_qid(new_queries)
            for qid in new_queries:
                q_string = new_queries[qid]
                snippets_crawler(qid,q_string,self._raw_dir,self._crawl_limit).start_crawl()
                create_snippet_single_trec_file(self._raw_dir,self._trec_dir,qid)
                self._queries[qid] = q_string
            #self._cleanup()

            self._build_snippet_index()

        self._generate_query(dates)


    def _process_original_qid(self,original_queries):
        processed_queries= {}
        self._query_mapping = {}

        for original_qid in original_queries:
            q_data = original_queries[original_qid]
            m = re.search("^([a-zA-Z]+)?(\d+)$",original_qid)
            if m is not None:
                qid = m.group(2)
                

            else:
                raise ValueError("the qid %s is malformated!" %original_qid)
            # qid = re.sub("MB","",qid)
            processed_queries[qid] = q_data
            self._query_mapping[qid] = original_qid 


        return processed_queries

    def _build_snippet_index(self):
        snippet_build_index(self._trec_dir,self._snippet_index_dir,self._index_para)
        os.system("IndriBuildIndex %s" %self._index_para)



    def _generate_query(self,dates):
        self._gene_part_queries(dates,self._queries,"expanded")

    def _gene_part_queries(self,dates,queries,prefix):
        self._temp_query_builder.gene_normal_query(self._temp_query_para,
                            queries,self._snippet_index_dir)
        
        self._oqf_builder.gene_normal_query(self._oqf,
                            queries,self._snippet_index_dir,run_id=self._runid )

        os.system("IndriRunQuery %s > %s" %(self._temp_query_para,self._orf))

        os.system("axio_expansion -oqf=%s -output=%s -index_list=%s -orf=%s -beta=%f" 
                  %(self._oqf,self._temp_output,self._index_list,
                    self._orf,self._beta))

        

        for date in dates:
            output_file = os.path.join(self._dest_query_dir,"%s_%s" %(prefix,date) )

            date_index_dir = os.path.join(self._index_dir,date)


            with open(output_file,'w') as of:
                print "write to %s\n" %output_file,
                with open(self._temp_output) as f:

                    qid_finder = re.compile("<number>")
                    index_finder = re.compile("<index>(.+?)</index>")
                    empty_query_finder = re.compile("<text>#weight\(\s+\)</text>")
                    qid = ""
                    for line in f:
                        found_expanding_tag = re.search("(<beta>)|(<index_list>)|(<oqf>)|(<orf>)|(<output>)",line)
                        found_empty_query = empty_query_finder.search(line)
                        #remove expanding tag generated by axiomatic expanding code    
                        
                        if found_expanding_tag is not None:
                            #print "skip line:",line
                            continue

                        elif found_empty_query is not None:
                            print "Found empty query %s" %(qid)
                            of.write("\t\t<text>#combine(%s)</text>\n" %(self._queries[qid]))

                        else:
                            #add MB prefix back
                            if qid_finder.search(line):
                                m = re.search("<number>(\d+)",line)
                                qid = m.group(1)
                                #line = qid_finder.sub("<number>MB",line)
                                line = "<number>%s</number>\n" %(self._query_mapping[qid])               
                              
                            elif index_finder.search(line):
                                line = "<index>%s</index>\n"%date_index_dir

                            
                            of.write(line)

def prepare_snippet(qid,snippets_dir):
    raw_dir = os.path.join(snippets_dir,"raw")
    trec_dir = os.path.join(snippets_dir,"trec")
    snippet_index_dir = os.path.join(snippets_dir,"trec")
    index_para = os.path.join(snippets_dir,"para","index_para")
    query_para_dir = os.path.join(snippets_dir,"para","query_para_dir")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snippets_dir","-sr",
        default="/infolab/headnode2/lukuang/2017-rts/data/query_expansion/snippet")
    parser.add_argument(
        "--communication_dir","-cr",
        default="/infolab/headnode2/lukuang/2017-rts/data/communication")
    parser.add_argument("--clarity_query_dir","-cqr",default="/infolab/headnode2/lukuang/2017-rts/data/clarity_queries")
    parser.add_argument("--index_dir","-ir",default="/infolab/headnode2/lukuang/2017-rts/data/index")
    parser.add_argument("--query_dir","-qr",default="/infolab/headnode2/lukuang/2017-rts/data/queries")
    parser.add_argument("--beta","-b",type=float,default=2.4)
    # parser.add_argument(
    #     "--trec_tex_dir","-tr",
    #     default="/infolab/headnode2/lukuang/2017-rts/data/query_expansion/snippet/trec")
    # parser.add_argument(
    #     "--index_dir","-ir",
    #     default="/infolab/headnode2/lukuang/2017-rts/data/query_expansion/snippet/index")
    # parser.add_argument(
    #     "--index_para_dir","-ipr",
    #     default="/infolab/headnode2/lukuang/2017-rts/data/query_expansion/snippet/para/index_para")
    
    
    # parser.add_argument("basic_file")
    # parser.add_argument("run_name_file")
    # parser.add_argument("topic_file")
    
    args=parser.parse_args()

    #prepare communication 
    # basic_file = os.path.join(args.communication_dir,"basic")
    # run_name_file = os.path.join(args.communication_dir,"runs")
    topic_file = os.path.join(args.communication_dir,"topics")

    # runs = [
    #     "UDInfoSPP"
    # ]

    # communicator = BrokerCommunicator(basic_file,
    #                     run_name_file,topic_file)
    
    # prepare warning log



    print "Start at %s" %now()
    # print "register runs:"
    # for name in runs:
    #     communicator.register_run(name)


    print "initialize preparator"
    

    queries = {}
    #communicator.poll_topics()
    topics = json.load(open(topic_file))
    for a_topic in topics:
        qid = a_topic["topid"]
        q_string = a_topic['title']
        q_string = re.sub("[^\w ]"," ",q_string)
        
        queries[qid] = q_string

    

    
    date = str(time.gmtime().tm_mday)
    dates = ["22","23","24","25","26","27","28","29","30","31",'1','2','3','4','5']
    dates.append(date)


    print "prepare clarity queries:"
    for date in dates:
        date_clarity_query_file = os.path.join(args.clarity_query_dir,date)
        with open(date_clarity_query_file,"w") as f:
            for qid in queries:
                q_string = queries[qid]
                clarity_query_string = " ".join(re.findall("\w+",q_string))
                f.write("%s:%s\n" %(qid,clarity_query_string))

    print "prepare raw indri queries:"
    for date in dates:
        date_index_dir = os.path.join(args.index_dir,date)
        dest_file = os.path.join(args.query_dir,"%s_%s" %("raw",date))
        retrieval_method = "method:f2exp,s:0.1"

        temp_query_builder = IndriQueryFactory(count=10,
                                        rule=retrieval_method)
        temp_query_builder.gene_normal_query(dest_file,
                                queries,date_index_dir)

    

    print "prepare static expanded indri queries:"

    static_preparator = StaticPreparator(args.query_dir,args.index_dir,
                                              "UDInfoEXP",args.snippets_dir,
                                              args.beta,100)
    static_preparator.prepare(queries,dates)
    
    # while True:
        #try:
        # date = str(time.gmtime().tm_mday)

        # dynamic_preparator.prepare(date)
            
            



        # total_secs = need_wait()    
        # time.sleep(total_secs)
        # except Exception as ex:
        #     print type(ex)
        #     now_time = now()
        #     logger.warn("%s: %s\n" %(now_time,str(ex)) )

        


if __name__=="__main__":
    main()

