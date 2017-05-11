/* generate query for  query feedback predictor
*/


#include "indri/Repository.hpp"
#include "indri/CompressedCollection.hpp"
#include "indri/LocalQueryServer.hpp"
#include "indri/ScopedLock.hpp"
#include "indri/Parameters.hpp"
#include "indri/QueryEnvironment.hpp"
#include <dirent.h>
#include <iostream>
#include <string>
#include <sstream>
#include <typeinfo>
#include <algorithm>
#include <map>
#include <math.h>
#include <fstream>
#include <dirent.h>
#include "utility.hpp"
using namespace std;


template<typename A, typename B>
std::pair<B,A> flip_pair(const std::pair<A,B> &p)
{
    return std::pair<B,A>(p.second, p.first);
}

template<typename A, typename B>
std::multimap<B,A> flip_map(const std::map<A,B> &src)
{
    std::multimap<B,A> dst;
    std::transform(src.begin(), src.end(), std::inserter(dst, dst.begin()), 
                   flip_pair<A,B>);
    return dst;
}


map<string, vector<string> > get_results(char* result_file, const int& tune_documents){
    ifstream f;
    string line;
    string qid="";
    map<string, vector<string> > results;
    f.open(result_file);
    if(f.is_open()){
        while(getline(f,line)){
            size_t qid_founder = line.find_first_of(" ");
            if (qid_founder!=string::npos){
                qid = line.substr(0,qid_founder);
                if(results.find( qid ) == results.end()){
                    results[qid] = vector<string>();
                }
                line = line.substr(qid_founder+4);
                size_t docid_finder = line.find_first_of(" ");
                if(docid_finder != string::npos){
                    if(results[qid].size()==tune_documents){
                        continue;
                    }
                    else{
                        string docid = line.substr(0,docid_finder);
                        results[qid].push_back(docid);
                    }
                    
                }

            }
        }
    }
    return results;
}

lemur::api::DOCID_T get_internal_did( indri::collection::Repository& r, const string& ex_docid ) {
  indri::collection::CompressedCollection* collection = r.collection();
  std::string attributeName = "docno";
  std::vector<lemur::api::DOCID_T> documentIDs;

  documentIDs = collection->retrieveIDByMetadatum( attributeName, ex_docid );

  return documentIDs[0];

}


map<string , int> get_term_map(indri::collection::Repository& r,const string& ex_docid){
    lemur::api::DOCID_T internal_did = get_internal_did(r,ex_docid);
    map <string, int> term_map;
    indri::server::LocalQueryServer local(r);

    std::vector<lemur::api::DOCID_T> documentIDs;
    documentIDs.push_back(internal_did);
    indri::server::QueryServerVectorsResponse* response = local.documentVectors( documentIDs );

    if( response->getResults().size() ) {
        indri::api::DocumentVector* docVector = response->getResults()[0];

        for( size_t i=0; i<docVector->positions().size(); i++ ) {
          int position = docVector->positions()[i];
          const std::string& stem = docVector->stems()[position];

          if(term_map.find(stem)==term_map.end()){
            term_map[stem] = 0;
          }
          term_map[stem] += 1;
        }
        delete docVector;
    }

    delete response;
    return term_map;
}


map<string, vector< map<string,int> > > get_result_term_map(indri::collection::Repository& r, const map<string, vector<string> >& results){
    map<string, vector< map<string,int> > > result_term_map;
    for(map<string, vector<string> >::const_iterator it=results.begin();it!=results.end(); ++it ){
        vector< map<string,int> > one_result_term_map;
        for(vector<string>::const_iterator sid=it->second.begin(); sid!=it->second.end(); ++sid){
            map<string , int> doc_term_map = get_term_map(r,*sid);
            one_result_term_map.push_back(doc_term_map);
        }

        result_term_map[it->first] = one_result_term_map;
    }
    return result_term_map;
}

float compute_alpha(const int& tune_documents){
    float  alpha = 2.0/(tune_documents*(tune_documents+1)); 
    return alpha;
}

string get_reversed_stem(indri::collection::Repository& r,const string & term){
    string reversed_term;
    if (term == r.processTerm(term) ){

        reversed_term = term;
    }
    else{
        reversed_term = term +"e";
        if (term != r.processTerm(reversed_term) ){
            reversed_term = term + "ing";
            if (term != r.processTerm(reversed_term) ){
                string end_chara = term.substr(term.size()-1);
                reversed_term = term + end_chara;
                if (term != r.processTerm(reversed_term) ){
                    cerr<<"Cannot find reversed_term for "<<term<<"!"<<endl;
                    return "";
                }
            }
        }
        // cout<<"reversed term for "<<term<<" is "<<reversed_term<<endl;
    }
    return reversed_term;
}

map<string, float> get_top_terms(indri::collection::Repository& r,vector< map<string,int> > & query_result_list,const int& tune_terms, const float& alpha) {
    map<string, float> top_terms ;
    map<string, float> p_wl;
    map<string, float> weights;
    int n = query_result_list.size();

    for(int i=0;i<n;i++){
        float p_dl = alpha * (n-i);
        map <string, int> term_map = query_result_list[i];
        int d_size = 0;
        for(map <string, int>::iterator tit=term_map.begin();tit!=term_map.end();++tit){
            
            d_size +=  tit->second;

        }

        for(map <string, int>::iterator tit=term_map.begin();tit!=term_map.end();++tit){
            string term = tit->first;
            int df =  tit->second;
            float p_wd = df*1.0/d_size;
            if(p_wl.find(term) == p_wl.end()){
                p_wl[term] = .0;
            }
            p_wl[term] += p_wd*p_dl;

        }
    }
    indri::server::LocalQueryServer local(r);
    int c_size = local.termCount();
    for(map <string, float>::iterator tit=p_wl.begin();tit!=p_wl.end();++tit){
        string term = tit->first;
        float term_p_wl = tit->second;
        int f_ct = local.stemCount(term);
        if(f_ct!=0){
            float p_wc = f_ct*1.0/c_size;
            weights[term] = term_p_wl* log( term_p_wl/p_wc );
        }
        
        
        // cout<<"weight for term "<<term<<" is "<<to_string( weights[term] )<<endl;

    }

    std::multimap<float, string> dst = flip_map(weights);

    int count = 0;
    for(map <float, string>::reverse_iterator dit=dst.rbegin();dit!=dst.rend();++dit){
        top_terms[dit->second] = dit->first;
        count++;
        if (count >= tune_terms) break;
    }

    return top_terms;
}


string get_top_term_string(indri::collection::Repository& r,map<string, float>& top_terms){
    string top_term_string = "#weight( ";
    for(map <string, float>::iterator it=top_terms.begin();it!=top_terms.end();++it){
        string reversed_term = get_reversed_stem(r,it->first);
        if(reversed_term.length()==0){
            continue;
        }
        top_term_string += " "+to_string(it->second);

        top_term_string += " "+reversed_term;
    }   
    top_term_string += " )";
    return top_term_string;

}


map<string, string> get_feedback_queries(indri::collection::Repository& r,map<string, vector< map<string,int> > >& result_term_map,const int& tune_terms, const float& alpha){
    map<string, string> feedback_queries;
    for(map<string, vector< map<string,int> > >::iterator it=result_term_map.begin();it!=result_term_map.end(); ++it ){
        string qid = it->first;

        vector< map<string,int> > query_result_list = it->second;
        map<string, float> top_terms = get_top_terms(r,query_result_list,tune_terms,alpha) ;
        feedback_queries[qid] = get_top_term_string(r,top_terms);
    }
    return feedback_queries;
}





static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query") ) || 
      !( param.exists( "index") ) ||
      !( param.exists( "result"))  )  {
   std::cerr << "get_qf_query usage: " << std::endl
             << "   get_qf_query -query=myquery -index=myindex -result=myresult" << std::endl;
   exit(-1);
  }
  
}


int main(int argc, char** argv){
    indri::collection::Repository r;
    try {
        indri::api::Parameters& param = indri::api::Parameters::instance();
        param.loadCommandLine( argc, argv );
    
        usage( param );
        bool debug = false;
        if (param.exists( "debug" )){
            debug = true;
            // cout<<"YES!!!!"<<endl;
        }

        
        std::string result_file_string = param[ "result" ];
        char* result_file = new char[result_file_string.length()+1];
        memcpy(result_file, result_file_string.c_str(), result_file_string.length()+1);

        string rep_name = param[ "index" ];
        //int percent_threshold = atoi(argv[2]);
        //string idf_term  = argv[3];
        //float variance_threshold = atof(argv[4]);


        r.openRead( rep_name );
        // output(idf,dest_dir);

        // convert queries to queer sub word vectors to prepare 
        // for cooccurrence cvomputation.
        // For example, for a query {qid: [w1,w2,w3]}
        // the result would be {qid: [ [w1,w2],[w1,w2],[w1,w3],[w1,w2,w3] ]}
        int tune_documents = param.get("tune_documents",10);
        int tune_terms = param.get("tune_terms",5);
        
        map<string, vector<string> > results = get_results(result_file,tune_documents);
        // cout<<"finished geting results"<<endl;
        map<string, vector< map<string,int> > > result_term_map = get_result_term_map(r,results);

        float  alpha = compute_alpha(tune_documents);
        map<string, string> feedback_queries = get_feedback_queries(r,result_term_map, tune_terms, alpha);



        for(map<string,string>:: iterator it=feedback_queries.begin(); it!=feedback_queries.end(); ++it){

            cout<<it->first<<" "<<it->second<<endl;
        }
        r.close();
    } catch( lemur::api::Exception& e ) {
        LEMUR_ABORT(e);
    } catch( ... ) {
        std::cout << "Caught an unhandled exception" << std::endl;
    }
    return 0;
}