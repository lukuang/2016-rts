"""
generate queries for 2015
"""

import os
import json
import sys
import re
import argparse
import codecs
sys.path.append("../../")

from myUtility.indri import IndriQueryFactory
from myUtility.corpus import Query,ExpandedQuery

def get_mb_queries(original_file):
    title_queries = {}
    desc_queries = {}
    qid = ""
    in_desc = False
    in_title = False
    with open(original_file) as f:
        for line in f:
            line = line.rstrip()
            mn = re.search("<num> Number: (\w+)",line)
            
            if mn is not None:
                qid = mn.group(1)
                title_queries[qid] = ""
                desc_queries[qid] = ""
            else:
                mt = re.search("<title>",line)
                if mt is not None:
                    in_title = True
                    continue
                else:
                    md = re.search("<desc> Description:",line)
                    if md is not None:
                        in_desc = True
                        continue
                    else:
                        ma = re.search("<narr> Narrative:",line)
                        if ma is not None:
                            in_desc = False
            
            if in_desc:
                desc_queries[qid] += line+"\n"
            elif in_title:
                title_queries[qid] = line+"\n"
                in_title = False
    return title_queries,desc_queries

def get_original_queries(original_query_file):
    title_queries,desc_queries = get_mb_queries(original_query_file)
    queries = {}
    for qid in title_queries:
        
        q_text = title_queries[qid]
        queries[qid] = Query(qid,q_text)

    return queries

def get_wiki_expansion_model(wiki_expand_dir,top):
    expansion_model = {}
    for qid in os.walk(wiki_expand_dir).next()[2]:
        expansion_model[qid] = {}
        query_expanding_file = os.path.join(wiki_expand_dir,qid)
        temp_model = json.load(open(query_expanding_file))
        sorted_model = sorted(temp_model.items(),key=lambda x:x[1],reverse=True)[:top]
        q_weight_sum = .0
        for (t,w) in sorted_model:
            expansion_model[qid][t] = w
            q_weight_sum += w
        for t in expansion_model[qid]:
            expansion_model[qid][t] /= q_weight_sum
    return expansion_model


def get_expanded_query(original_queries,expansion_model,para_lambda):
    expanded_queries = {}
    for qid in original_queries:
        expanded_queries[qid] = ExpandedQuery(qid,original_queries[qid].text,para_lambda)
        expanded_queries[qid].expand(expansion_model[qid])
    return expanded_queries

def get_judged_qid(qrel_file):
    judged_qids = []
    with open(qrel_file) as f:
        for line in f:
            parts= line.rstrip().split()
            qid = parts[0]
            if qid not in judged_qids:
                judged_qids.append(qid)
    return judged_qids

def process_original_qid(original_queries):
    processed_queries= {}
    for qid in original_queries:
        q_data = original_queries[qid]
        qid = re.sub("MB","",qid)
        processed_queries[qid] = q_data

    return processed_queries


def add_filter_time_wrapper(time_string):
    def _add_filter_time(m):
        return "<text>#filreq(#dateequals(%s) %s)</text>" %(time_string,m.group(1))
    
    return _add_filter_time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_query_file")
    parser.add_argument("top_index_dir")
    parser.add_argument("top_query_para_dir")
    parser.add_argument("index_method",choices=["individual","incremental"])
    parser.add_argument("--retrieval_method","-rm",default="method:f2exp")
    parser.add_argument("--result_count","-rc",type=int,default=10)
    parser.add_argument("--wiki_expand_dir","-we")
    parser.add_argument("--snippet_expand_dir","-sr")
    parser.add_argument("--fbDocs","-fd",type=int,default=10)
    parser.add_argument("--fbTerms","-ft",type=int,default=10)
    parser.add_argument("--fbOrigWeight","-fw",type=float,default=0.5)
    parser.add_argument("--expansion_method","-em",type=int,choices=[0,1,2,3],
            default=0,
            help="""methodes for expansion. Options:
                    original,
                    snippet,
                    wiki,
                    pseudo 
                """)
    parser.add_argument("--qrel_file","-qf")
    parser.add_argument("--tune","-t",action="store_true")
    args=parser.parse_args()

    METHODS = [
        "original",
        "snippet",
        "wiki",
        "pseudo"
    ]

    dates = range(20,30)
    year = 2015
    month = 7


    expansion_method = METHODS[args.expansion_method]
    
    original_queries =  get_original_queries(args.original_query_file)

    if args.qrel_file:
        print "remove unjudged queries"
        print "# queries before %d" %(len(original_queries))
        judged_qids = get_judged_qid(args.qrel_file)
        for qid in original_queries.keys():
            if qid not in judged_qids:
                original_queries.pop(qid,None)
        print "# queries after %d" %(len(original_queries))



    print args.top_query_para_dir,args.index_method,args.expansion_method
    query_root_dir =  os.path.join(
                            args.top_query_para_dir,
                            args.index_method,expansion_method)
    if not os.path.exists(query_root_dir):    
        os.makedirs(query_root_dir)


    for date in dates:
        date = str(date)
        query_file = os.path.join(query_root_dir,date)

        index_dir = os.path.join(args.top_index_dir,args.index_method,date)

        date_when_str = "%s/%s/%d" %(str.zfill(str(month),2),
                                        str.zfill(date,2),
                                        year)
        date_when_str = "%s" %(date_when_str)

        if expansion_method == "original" or expansion_method == "pseudo":
            if expansion_method == "original":
                if args.tune:
                    for s in range(4):
                        s = (s+1)*0.1
                        tune_retrieval_method = args.retrieval_method +",s:%f" %(s)
                        tune_run_id = "original_%f" %(s)
                        tune_query_file = '%s_%f' %(query_file,s)
                        if args.index_method == "individual":
                            query_builder = IndriQueryFactory(count=args.result_count,
                                    rule=tune_retrieval_method)
                    

                            query_builder.gene_normal_query(tune_query_file,
                                original_queries,index_dir,run_id=tune_run_id)
                        else:
                            query_builder = IndriQueryFactory(count=args.result_count,
                            rule=tune_retrieval_method,use_stopper=False,
                            date_when="dateequals",psr=False)

                            query_builder.gene_query_with_date_filter(tune_query_file,
                                original_queries,index_dir,date_when_str,run_id=tune_run_id )
            else:
                if args.tune:
                    for s in range(3):
                        s = (s+1)*0.3
                        tune_retrieval_method = args.retrieval_method +",s:%f" %(s)
                        
                        for tune_fbDocs in [5,10,15]:
                            for tune_fbTerms in [5,10,15]:
                                for tune_fbOrigWeight in [0.3,0.6,0.9]:

                                    tune_run_id = "pseudo_%f_%d_%d_%f" %(s,tune_fbDocs,
                                                                         tune_fbTerms,
                                                                         tune_fbOrigWeight)

                                    tune_query_file = '%s_%f_%d_%d_%f' %(query_file,s,
                                                                         tune_fbDocs,
                                                                         tune_fbTerms,
                                                                         tune_fbOrigWeight)
                                    if args.index_method == "individual":
                                        query_builder = IndriQueryFactory(count=args.result_count,
                                                rule=tune_retrieval_method,psr=True)
                    

                                        query_builder.gene_normal_query(tune_query_file,
                                            original_queries,index_dir,run_id=tune_run_id,
                                            fbDocs=tune_fbDocs,fbTerms=tune_fbTerms,
                                            fbOrigWeight=tune_fbOrigWeight)
                                    else:
                                        query_builder = IndriQueryFactory(count=args.result_count,
                                            rule=tune_retrieval_method,use_stopper=False,
                                            date_when="dateequals",psr=True)

                                        query_builder.gene_query_with_date_filter(tune_query_file,
                                            original_queries,index_dir,date_when_str,run_id=tune_run_id,
                                            fbDocs=tune_fbDocs,fbTerms=tune_fbTerms,
                                            fbOrigWeight=tune_fbOrigWeight)
        elif expansion_method == "wiki":
            if not args.wiki_expand_dir:
                raise RuntimeError("need wiki_expand_dir when using wiki expansion!")
            if args.tune:
                for s in [0.3,0.6,0.9]:
                    tune_retrieval_method = args.retrieval_method +",s:%f" %(s)

                    for top in [5,10,15]:
                        wiki_expansion_model = get_wiki_expansion_model(args.wiki_expand_dir,top)

                        for para_lambda in [0.3,0.6,0.9]:
                            tune_run_id = "wiki_%f_%d_%f" %(s,top,para_lambda)

                            tune_query_file = '%s_%f_%d_%f' %(query_file,s,top,para_lambda)
                                
                            expanded_queries = get_expanded_query(original_queries,wiki_expansion_model,para_lambda)

                            if args.index_method == "individual":
                                query_builder = IndriQueryFactory(count=args.result_count,
                                    rule=tune_retrieval_method)
                    

                                query_builder.gene_normal_query(tune_query_file,
                                    expanded_queries,index_dir,run_id=tune_run_id)

                            else:
                                query_builder = IndriQueryFactory(count=args.result_count,
                                        rule=tune_retrieval_method,use_stopper=False,
                                        date_when="dateequals",psr=False)
                                
                                query_builder.gene_query_with_date_filter(
                                            tune_query_file,expanded_queries,
                                            index_dir,date_when_str,run_id=tune_run_id)

        elif expansion_method == "snippet":
            if not args.snippet_expand_dir:
                raise RuntimeError("need snippet_expand_dir when using snippet expansion!")
            if args.tune:

                # remove the prefix "MB" of original queries' qids

                original_queries = process_original_qid(original_queries)
                
                snippet_index = os.path.join(args.snippet_expand_dir,"index")
                snippet_query_dir = os.path.join(args.snippet_expand_dir,"para","query_para")
                snippet_result_dir = os.path.join(args.snippet_expand_dir,"result")
                index_list = os.path.join(args.snippet_expand_dir,"index_list")
                for s in [0.1,0.2,0.3,0.6]:
                    tune_retrieval_method = args.retrieval_method +",s:%f" %(s)
                    temp_query_file = os.path.join(snippet_query_dir,"%f" %s)
                    
                    if not os.path.exists(temp_query_file):
                    
                        temp_query_builder = IndriQueryFactory(count=10000,
                                    rule=tune_retrieval_method)
                    
                        #build snippet temp query file and temp result file (orf)
                        # note that the index here should be the index of the snippet corpus

                        temp_query_builder.gene_normal_query(temp_query_file,
                            original_queries,snippet_index)
                    
                    orf = os.path.join(snippet_result_dir,"orf_%f" %s)
                    
                    if not os.path.exists(orf):
                    
                        os.system("IndriRunQuery %s > %s" %(temp_query_file,orf)) 

                    for i in range(1,14):
                        beta = 0.3*i
                        suffix = "_%f_%f" %(s,beta)
                        tune_run_id = "snippet%s" %suffix
                        oqf = os.path.join(args.snippet_expand_dir,"temp","oqf%s"%suffix)
                        
                        if not os.path.exists(oqf):
                            oqf_builder = IndriQueryFactory(count=args.result_count,
                            rule=tune_retrieval_method)

                            oqf_builder.gene_normal_query(oqf,
                            original_queries,index_dir,run_id=tune_run_id )

                        temp_expanded_query_file = os.path.join(args.snippet_expand_dir,"temp","output%s"%suffix)
                        
                        if not os.path.exists(temp_expanded_query_file):
                            os.system("axio_expansion -oqf=%s -output=%s -index_list=%s -orf=%s -beta=%f" 
                                    %(oqf,temp_expanded_query_file,index_list,orf,beta))

                        tune_query_file = '%s%s' %(query_file,suffix)

                        if args.index_method == "incremental":
                            add_filter_time = add_filter_time_wrapper(date_when_str)
                        
                        with open(tune_query_file,'w') as of:
                            with open(temp_expanded_query_file) as f:

                                text_finder = re.compile("<text>(.+?)</text>")
                                qid_finder = re.compile("<number>")
                                index_finder = re.compile("<index>(.+?)</index>")
                                for line in f:
                                    found_expanding_tag = re.search("(<beta>)|(<index_list>)|(<oqf>)|(<orf>)|(<output>)",line)
                                    #remove expanding tag generated by axiomatic expanding code    
                                    
                                    if found_expanding_tag is not None:
                                        print "skip line:",line
                                        continue


                                    else:
                                        #add MB prefix back
                                        if qid_finder.search(line):
                                            line = qid_finder.sub("<number>MB",line)
                                                            
                                        elif args.index_method == "incremental":
                                            line = text_finder.sub(add_filter_time,line)
                                          
                                        if index_finder.search(line):
                                            line = "<index>%s</index>\n"%index_dir
 
                                        of.write(line)

                                        
                                        





                        #tune_query_file = '%s%s' %(query_file,suffix)
                        #output = tune_query_file
                        #os.system("axio_expansion -oqf=%s -output=%s -index_list=%s -orf=%s -beta=%f" 
                        #            %(oqf,output,index_list,orf,beta))
                        #if index_method == "increment":





        else:
            raise RuntimeError("method not implemented yet!")




if __name__=="__main__":
    main()

