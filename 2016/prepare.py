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
    def __init__(self,dest_query_dir,index_dir,runid):
        self._dest_query_dir, self._index_dir, self._runid\
            =  dest_query_dir, index_dir, runid
        self._retrieval_method = "method:f2exp,s:0.1"


    @abstractmethod
    def prepare(self,new_queries,date):
        pass

    @abstractmethod
    def _generate_query():
        pass


class OriginalPreparator(Preparator):
    """class used for generate original queries
    """

    def __init__(self,dest_query_dir,index_dir,runid):
        super(OriginalPreparator,self).__init__(dest_query_dir,index_dir,runid)
        self._setup()


    def _setup(self):
        self._query_builder = IndriQueryFactory(count=10,
                                    rule=self._retrieval_method)
        self._queries = {}



    def prepare(self,new_queries,date):
        for qid in new_queries:
            self._queries[qid] = new_queries[qid]

        self._generate_query(date)


    def _generate_query(self,date):
        output_file = os.path.join(self._dest_query_dir,"original_%s"%date)

        date_index_dir = os.path.join(self._index_dir,date)
        self._query_builder.gene_normal_query(output_file,
                                self._queries,date_index_dir,run_id=self._runid)


class SnippetPreparator(Preparator):
    """class used for snippet expansion data
    crawling and query generation
    """
    def __init__(self,dest_query_dir,index_dir,runid,snippets_dir,beta):
        super(SnippetPreparator,self).__init__(dest_query_dir,index_dir,runid)
        self._snippets_dir,self._beta = snippets_dir,beta
        self._queries = {}

        self._setup()
        

    def _setup(self):
        """set up the paths
        """
        self._raw_dir = os.path.join(self._snippets_dir,"raw")
        if not os.path.exists(self._raw_dir):
            os.mkdir(self._raw_dir)

        self._trec_dir = os.path.join(self._snippets_dir,"trec")
        if not os.path.exists(self._trec_dir):
            os.mkdir(self._trec_dir)

        self._temp_dir = os.path.join(self._snippets_dir,"temp")
        if not os.path.exists(self._temp_dir):
            os.mkdir(self._temp_dir)

        self._snippet_result_dir = os.path.join(self._snippets_dir,"result")
        if not os.path.exists(self._snippet_result_dir):
            os.mkdir(self._snippet_result_dir)

        self._snippet_index_dir = os.path.join(self._snippets_dir,"index")
        if not os.path.exists(self._snippet_index_dir):
            os.mkdir(self._snippet_index_dir)

        self._para_dir = os.path.join(self._snippets_dir,"para")
        if not os.path.exists(self._para_dir):
            os.mkdir(self._para_dir)


        self._index_para = os.path.join(self._para_dir,"index_para")

        self._temp_query_para = os.path.join(self._para_dir,"temp_query_para")

        self._index_list = os.path.join(self._snippets_dir,"index_list")
        
        self._orf = os.path.join(self._snippet_result_dir,"orf")

        self._oqf = os.path.join(self._temp_dir,"oqf")
        
        self._temp_output = os.path.join(self._temp_dir,"temp_output")

        with open(self._index_list,"w") as f:
            f.write(self._snippet_index_dir+"\n")

        self._temp_query_builder = IndriQueryFactory(count=10000,
                                    rule=self._retrieval_method)

        self._oqf_builder = IndriQueryFactory(count=10,
                            rule=self._retrieval_method)


    def prepare(self,new_queries,date):
        new_queries = self.process_original_qid(new_queries)
        for qid in new_queries:
            q_string = new_queries[qid]
            snippets_crawler(qid,q_string,self._raw_dir).start_crawl()
            create_snippet_single_trec_file(self._raw_dir,self._trec_dir,qid)
            self._queries[qid] = q_string

        self._cleanup()

        self._build_snippet_index()

        self._generate_query(date)



    def _cleanup(self):
        """clean up previous index,oqf,orf,output

        """
        os.system("rm -r %s/*" %(self._snippet_index_dir))
        os.system("rm  %s/*" %(self._para_dir))
        os.system("rm  %s/*" %(self._temp_dir))
        os.system("rm  %s/*" %(self._snippet_result_dir))


    def _build_snippet_index(self):
        snippet_build_index(self._trec_dir,self._snippet_index_dir,self._index_para)
        os.system("IndriBuildIndex %s" %self._index_para)



    def process_original_qid(self,original_queries):
        processed_queries= {}
        for qid in original_queries:
            q_data = original_queries[qid]
            qid = re.sub("MB","",qid)
            processed_queries[qid] = q_data

        return processed_queries

    def _generate_query(self,date):
        self._temp_query_builder.gene_normal_query(self._temp_query_para,
                            self._queries,self._snippet_index_dir)
        
        date_index_dir = os.path.join(self._index_dir,date)
        self._oqf_builder.gene_normal_query(self._oqf,
                            self._queries,date_index_dir,run_id=self._runid )

        os.system("IndriRunQuery %s > %s" %(self._temp_query_para,self._orf))

        os.system("axio_expansion -oqf=%s -output=%s -index_list=%s -orf=%s -beta=%f" 
                  %(self._oqf,self._temp_output,self._index_list,
                    self._orf,self._beta))

        output_file = os.path.join(self._dest_query_dir,"snippet_%s" %(date) )


        with open(output_file,'w') as of:
            print "write to %s" %output_file,
            with open(self._temp_output) as f:

                text_finder = re.compile("<text>(.+?)</text>")
                qid_finder = re.compile("<number>")
                index_finder = re.compile("<index>(.+?)</index>")
                query_words_finder = re.compile("<text>#weight\((.+?)\)</text>")
                qid = ""
                for line in f:
                    found_expanding_tag = re.search("(<beta>)|(<index_list>)|(<oqf>)|(<orf>)|(<output>)",line)
                    #remove expanding tag generated by axiomatic expanding code    
                    
                    if found_expanding_tag is not None:
                        print "skip line:",line
                        continue


                    else:
                        #add MB prefix back
                        if qid_finder.search(line):
                            m = re.search("<number>(\d+)",line)
                            qid = m.group(1)
                            line = qid_finder.sub("<number>MB",line)
                                            
                          
                        elif index_finder.search(line):
                            line = "<index>%s</index>\n"%date_index_dir

                        elif query_words_finder.search(line):
                            m = query_words_finder.search(line)
                            query_words = m.group(1)
                            if not re.search("\w",query_words):
                                line = "<text>%s</text>\n" %(self._queries[qid])

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
        default="/infolab/headnode2/lukuang/2016-rts/data/query_expansion/snippet")
    parser.add_argument(
        "--communication_dir","-cr",
        default="/infolab/headnode2/lukuang/2016-rts/data/communication")
    parser.add_argument("--index_dir","-ir")
    parser.add_argument("--query_dir","-qr")
    parser.add_argument("--beta","-b",type=float,default=2.4)
    # parser.add_argument(
    #     "--trec_tex_dir","-tr",
    #     default="/infolab/headnode2/lukuang/2016-rts/data/query_expansion/snippet/trec")
    # parser.add_argument(
    #     "--index_dir","-ir",
    #     default="/infolab/headnode2/lukuang/2016-rts/data/query_expansion/snippet/index")
    # parser.add_argument(
    #     "--index_para_dir","-ipr",
    #     default="/infolab/headnode2/lukuang/2016-rts/data/query_expansion/snippet/para/index_para")
    
    
    # parser.add_argument("basic_file")
    # parser.add_argument("run_name_file")
    # parser.add_argument("topic_file")
    
    args=parser.parse_args()

    #prepare communication 
    basic_file = os.path.join(args.communication_dir,"basic")
    run_name_file = os.path.join(args.communication_dir,"runs")
    topic_file = os.path.join(args.communication_dir,"topics")

    runs = [
        "UDInfoORI",
        "UDInfoSNI"
    ]

    communicator = BrokerCommunicator(basic_file,
                        run_name_file,topic_file)
    
    # prepare warning log
    logger = logging.getLogger('prepareLogger')
    warningHandler = logging.FileHandler('prepare_warning.log')
    warningHandler.setLevel(logging.WARN)
    logger.addHandler(warningHandler)
    logging.captureWarnings(True);

    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.WARN)
    logger.addHandler(consoleHandler)

    logger.setLevel(logging.WARN)


    print "Start at %s" %now()
    print "register runs:"
    for name in runs:
        communicator.register_run(name)


    print "initialize preparator"
    original_preparator = OriginalPreparator(args.query_dir,args.index_dir,"UDInfoORI")
    snippet_preparator = SnippetPreparator(args.query_dir,args.index_dir,
                                              "UDInfoSNI",args.snippets_dir,args.beta)

    old_topics = {}

    while True:
        try:
            new_queries = {}
            communicator.poll_topics()
            topics = communicator.topics
            for a_topic in topics:
                qid = a_topic["topid"]
                q_string = a_topic['title']
                q_string = re.sub("\&"," ",q_string)
                if qid not in old_topics:
                    new_queries[qid] = q_string
                    old_topics[qid] = q_string


            date = str(time.gmtime().tm_mday)
            original_preparator.prepare(new_queries,date)
            snippet_preparator.prepare(new_queries,date)
            



            total_secs = need_wait()    
            time.sleep(total_secs)
        except Exception as ex:
            now_time = now()
            logger.warn("%s: %s\n" %(now_time,str(ex)) )

        


if __name__=="__main__":
    main()

