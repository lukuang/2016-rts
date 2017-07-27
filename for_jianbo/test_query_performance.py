"""
test jianbo's queries performance
"""

import os
import json
import sys
import re
import argparse
import codecs
from string import Template


query_template = Template("""
<query>
\t<number>$qid</number>
\t<text>$q_string</text>
</query>
""")


structure_template = Template("""
<parameters>
<index>$index</index>
<trecFormat>true</trecFormat>
<runID>$run_id</runID>
<count>$count</count>
$query_body
$rule
$stopper
$psr
</parameters>""")

index_para_template = Template("""
<parameters>
<index>$index_path</index>
<memory>$memory</memory>
$corpora
<stemmer><name>$stemmer</name></stemmer>
$fields
$stopper
</parameters>""")

corpus_template = Template("""
<corpus>
\t<path>$path</path>
\t<class>trectext</class>
</corpus>
""")

text_template = Template("""
<DOC>
\t<DOCNO>$did</DOCNO>
\t<TEXT>$text</TEXT>$fields
</DOC>""")

class Query(object):
    """Base query class
    """
    def __init__(self,qid,query_text):
        self._qid = qid
        self._text = query_text
        self._text_struct = Text(query_text)

    @property
    def original_model(self):
        return self._text_struct.raw_model()

    @property
    def text(self):
        return "%s" %self._text

class ExpandedQuery(Query):
    """Queries with expansion
    """

    def __init__(self,qid,query_text,para_lambda):
        self._para_lambda =  para_lambda
        super(ExpandedQuery,self).__init__(qid,query_text)
        self._expanding_model = None

    
    def expand(self,expanding_term_weights):
        self._expanding_model = Model(False,text_dict=expanding_term_weights)

    @property
    def expanding_model(self):
        if not self._expanding_model:
            raise RuntimeError("Not expanded yet!")
        return self._expanding_model.model


    @property
    def para_lambda(self):
        return self._para_lambda


class IndriQueryFactory(object):
    """Take in query related parameters for indri and
    generate indri query file
    """
    def __init__(self,count,rule=None,
            use_stopper=False,date_when=None,
            numeric_compare=None, psr=False):

        self._count,self._rule,self._use_stopper,self._psr = count,rule,use_stopper,psr

        

        if date_when:
            if date_when not in ["dateafter","datebefore", "datebetween","dateequals"]:
                raise ValueError("When value %s is not supported" %(date_when))

        if numeric_compare is not None:
            if numeric_compare not in ["less","greater","between","equals"]:
                raise ValueError("Compare value %s is not supported" %(numeric_compare))


        self._date_when,self._numeric_compare = date_when,numeric_compare


    def _gene_query(self,file_path,queries,index,run_id,
                date_value=None,numeric_value=None,
                numeric_field_name=None,fbDocs=None,
                fbTerms=None,fbOrigWeight=None):

        query_body = ""
        if self._rule is None:
            rule = ""
        else:
            rule = "<rule>%s</rule>" %self._rule

        if self._use_stopper:
            stopper = "<stopper>\n"
            stopwords = get_stopwords()
            for stopword in stopwords:
                stopper += "<word>%s</word>\n" %stopword 
            stopper += "</stopper>"
        else:
            stopper = ""



        for qid in queries: 
            sinlge_query_data = queries[qid]
            
            if isinstance(sinlge_query_data,Query):
                original_text = re.sub("[^\w]"," ",sinlge_query_data.text)
                if isinstance(sinlge_query_data,ExpandedQuery):
                    original_weight = sinlge_query_data.para_lambda
                    expanding_weight =  1-sinlge_query_data.para_lambda
                    expanding_string = ""
                    for term in sinlge_query_data.expanding_model:
                        term_weight = sinlge_query_data.expanding_model[term]
                        expanding_string += "%f %s " %(term_weight,term)
                    if len(expanding_string) == 0:
                        q_string = "#combine( %s )" %(original_text)
                    else:
                        q_string = "#weight( %f #combine( %s) %f #weight( %s ) )" \
                                        %(original_weight,original_text,
                                          expanding_weight,expanding_string)

                else:
                    q_string = "#combine( %s )" %(original_text)

            elif isinstance(sinlge_query_data,str) or isinstance(sinlge_query_data,unicode):
                q_string = sinlge_query_data.lower()
                q_string = re.sub("[^\w]"," ",q_string)
                q_string = "#combine( %s )" %(q_string)

            elif isinstance(sinlge_query_data,list):
                q_string = " ".join(sinlge_query_data)
                q_string = "#combine( %s )" %(q_string)
            
            elif isinstance(sinlge_query_data,dict):
                q_string = ""
                for term in sinlge_query_data:
                    weight = sinlge_query_data[term]
                    q_string += "%f %s " %(weight,term)

                q_string = "#weight( %s )" %(q_string)
            else:
                raise TypeError("unsupported value type %s for query data" %type(sinlge_query_data))

            
            if self._date_when:
                q_string = "#filreq( #%s( %s ) %s)" %(self._date_when,date_value,
                                                        q_string)
            
            if self._numeric_compare is not None:
                q_string = "#filreq( #%s( %s %d ) %s)" %(self._numeric_compare,
                                            numeric_field_name,numeric_value,q_string)

            psr = ""
            if self._psr :
                if not (fbDocs and fbTerms and fbOrigWeight):
                    raise ValueError("need valid fbDocs and fbTerms and fbOrigWeight!")
                psr += "<fbDocs>%d</fbDocs>" %(fbDocs)
                psr += "<fbTerms>%d</fbTerms>" %(fbTerms)
                psr += "<fbOrigWeight>%f</fbOrigWeight>" %(fbOrigWeight)

            query_body+=query_template.substitute(
                qid=qid,q_string=q_string)

        with codecs.open(file_path, 'w','utf-8') as f:
            f.write(structure_template.substitute(query_body=query_body,index=index,
                                                  run_id=run_id,count=str(self._count),
                                                  rule=rule,stopper=stopper,psr=psr))


    def gene_query_with_date_filter(self,file_path,queries,index,
                date_value,run_id="test",fbDocs=None,
                fbTerms=None,fbOrigWeight=None):

        self._gene_query(file_path,queries,index,run_id=run_id,date_value=date_value,
                fbDocs=fbDocs,fbTerms=fbTerms,fbOrigWeight=fbOrigWeight)


    def gene_query_with_numeric_filter(self,file_path,queries,index,
            numeric_value,numeric_field_name,run_id="test",
            fbDocs=None,fbTerms=None,fbOrigWeight=None):

        self._gene_query(file_path,queries,index,run_id,numeric_value=numeric_value,
                numeric_field_name=numeric_field_name,fbDocs=fbDocs,fbTerms=fbTerms,
                fbOrigWeight=fbOrigWeight)

    def gene_normal_query(self,file_path,queries,index,run_id="test"):
        
        self._gene_query(file_path,queries,index,run_id=run_id)


#
#-------------------before are utility code----------------------------
#-------------------below are the code that SHOULD be modified---------
#

def read_qrels(eval_dir):
    qrel_file = os.path.join(eval_dir,"qrels.txt")
    qrels = {}
    with open(qrel_file) as f:
        for line in f:
            line = line.rstrip()
            parts = line.split()
            qid = parts[0]
            docid = parts[2]
            jud = max(0,int(parts[3]) )
            if qid not in qrels:
                qrels[qid] = {}
            qrels[qid][docid] = jud

    return qrels


def read_query_file(query_file,qrels):
    queries = {}
    data = json.load(open(query_file))
    for single_query in data:
        qid = single_query["topid"]
        if qid not in qrels:
            continue
        # text = re.sub("[^\w ]+"," ",single_query["title"])
        # queries[qid] = text
        queries[qid] = single_query["title"]
    return queries




def build_temp_query(queries,temp_query_para_file,index_dir):
    retrieval_method = "method:f2exp,s:0.1"
    temp_query_builder = IndriQueryFactory(count=100,
                                    rule=retrieval_method)
    temp_query_builder.gene_normal_query(temp_query_para_file,
                            queries,index_dir)

def run_query(temp_query_para_file,temp_result_file):
    os.system("IndriRunQuery %s > %s" %(temp_query_para_file,temp_result_file))



def evaluate_temp_result(temp_result_file,qrels):
    

    performance = {}
    with open(temp_result_file) as f:
        for line in f:
            line = line.rstrip()
            parts = line.split() 
            qid = parts[0]
            docid = parts[2]
            if qid not in qrels:
                # print "query %s does not have judgement" %(qid)
                continue 
            else:
                if qid not in performance:
                    performance[qid] = .0

                if docid in qrels[qid]:
                    performance[qid] += qrels[qid][docid]*1.0/100
    final_performance = sum(performance.values())*1.0/len(qrels)
    print "the number of queries evaluated %d" %(len(qrels))
    print "the final performance is %f" %(final_performance)




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query_file")
    parser.add_argument("--index_dir","-ir",default="/infolab/headnode2/lukuang/2016-rts/data/incremental_index")
    parser.add_argument("--eval_dir","-er",default="/infolab/node4/lukuang/2015-RTS/src/2016/eval")
    args=parser.parse_args()


    temp_dir = "/tmp"
    prefix  = "jianbo_mb_test_"
    temp_query_para_file = os.path.join(temp_dir,prefix+"temp_query_para")
    temp_result_file = os.path.join(temp_dir,prefix+"temp_result")

    qrels = read_qrels(args.eval_dir)
    "Got qrels"
    queries = read_query_file(args.query_file,qrels)
    print "Got queries"
    build_temp_query(queries,temp_query_para_file,args.index_dir)
    print "Built Indri queries"
    run_query(temp_query_para_file,temp_result_file)
    print "Ran query and got results"
    evaluate_temp_result(temp_result_file,qrels)

if __name__=="__main__":
    main()

