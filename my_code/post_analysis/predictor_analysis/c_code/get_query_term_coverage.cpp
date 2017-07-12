/* get unweight local coherence of queries
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
        // cout<<"For qid "<<it->first<<":"<<endl;
        for(vector<string>::const_iterator sid=it->second.begin(); sid!=it->second.end(); ++sid){
            // cout<<"\tProcess "<<*sid<<endl;
            map<string , int> doc_term_map = get_term_map(r,*sid);
            one_result_term_map.push_back(doc_term_map);
        }

        result_term_map[it->first] = one_result_term_map;
    }
    return result_term_map;
}




map<string, vector<float> >  get_query_term_coverage(map<string, vector< map<string,int> > > result_term_map, map<string, vector<string> > queries){
    map<string, vector<float> >  query_term_coverage;
    for(map<string, vector<string> >::iterator it=queries.begin();it!=queries.end(); ++it ){
        
        vector<float> single_query_term_coverage;
        string qid = it->first;
        int q_size = it->second.size();

        for(int i=0;i<result_term_map[qid].size();i++){
            map<string , int> doc_term_map = result_term_map[qid][i];
            int match_count = 0;
            for(int j=0;j<q_size;j++){
                string term = it->second[j];
                if(doc_term_map.find(term)!=doc_term_map.end()){
                    match_count++;
                }  
            }
            single_query_term_coverage.push_back(match_count*1.0/q_size);
            
        }
        query_term_coverage[qid] = single_query_term_coverage;
    }
    return query_term_coverage;
}

float get_right_value(vector<float> v, string cu){
    float final_value=.0;
    if(cu=="max"){
        final_value = *max_element(v.begin(), v.end());
    }
    else if(cu == "min"){
        final_value = *min_element(v.begin(), v.end());
    }
    else if(cu == "average"){
        int s = v.size();
        for(int i=0;i<s;i++){
            final_value += v[i]/s;
        }
    }
    else if(cu == "median"){
        sort (v.begin(), v.end());
        int pos = v.size()/2;
        final_value = v[pos];
    }
    else if(cu == "upper"){
        sort (v.begin(), v.end());
        int pos = int(ceil(v.size()*0.9 - 1) );
        final_value = v[pos];
    }
    else if(cu == "lower"){
        sort (v.begin(), v.end());
        int pos = int(ceil(v.size()*0.1 - 1) );
        final_value = v[pos];
    }
    return final_value;
}

void show_query_term_coverage(map<string, vector<float> > query_term_coverage,string cu){
    map<string,float> final_output;
    for(map<string, vector<float> >::iterator it=query_term_coverage.begin();it!=query_term_coverage.end(); ++it ){
        string qid = it->first;
        float final_value = get_right_value(it->second,cu);
        cout << qid<<" "<<final_value<<endl;
    }
}


static void usage( indri::api::Parameters param ) {
  if( !param.exists( "query" ) || 
      !( param.exists( "index" ) ) ||
      !( param.exists( "result") ) ||
      !( param.exists( "cu") )) {
   std::cerr << "get_query_term_coverage usage: " << std::endl
             << "   get_query_term_coverage -query=myquery -index=myindex -result=myresult -cu=cu_choice" << std::endl;
   exit(-1);
  }
  string cu = param[ "cu" ];
  if(   cu!="min" &&
        cu!="average" &&
        cu!="median" &&
        cu!="upper" &&
        cu!="lower" &&
        cu!="max" ){
    std::cerr << "cu must be one of the values below: " << std::endl
             << "   min average max median upper lower" << std::endl;
    exit(-1);

  }
  
}


int main(int argc, char** argv){
    indri::collection::Repository r;
    try {
        indri::api::Parameters& param = indri::api::Parameters::instance();
        param.loadCommandLine( argc, argv );
    
        usage( param );
        string cu = param[ "cu" ];
        bool debug = false;
        if (param.exists( "debug" )){
            debug = true;
            // cout<<"YES!!!!"<<endl;
        }

        int tune_documents = (int) param.get( "tune_documents", 10 );

        std::string query_file_string = param[ "query" ];
        char* query_file = new char[query_file_string.length()+1];
        memcpy(query_file, query_file_string.c_str(), query_file_string.length()+1);

        std::string result_file_string = param[ "result" ];
        char* result_file = new char[result_file_string.length()+1];
        memcpy(result_file, result_file_string.c_str(), result_file_string.length()+1);

        string rep_name = param[ "index" ];
        //int percent_threshold = atoi(argv[2]);
        //string idf_term  = argv[3];
        //float variance_threshold = atof(argv[4]);

        map<string, vector<string> > queries;

        r.openRead( rep_name );
        vector<string> query_words = get_query_words(r,query_file,queries);
        // output(idf,dest_dir);

        // convert queries to queer sub word vectors to prepare 
        // for cooccurrence cvomputation.
        // For example, for a query {qid: [w1,w2,w3]}
        // the result would be {qid: [ [w1,w2],[w1,w2],[w1,w3],[w1,w2,w3] ]}
        if (debug) cout<<"Finished geting query words"<<endl;
        map<string, vector<string> > results = get_results(result_file,tune_documents);
        if (debug) cout<<"Finished geting results"<<endl;
        // cout<<"finished geting results"<<endl;
        map<string, vector< map<string,int> > > result_term_map = get_result_term_map(r,results);
        if (debug) cout<<"Finished geting result map"<<endl;
        map<string, vector<float> > query_term_coverage = get_query_term_coverage(result_term_map,queries);
        if (debug) cout<<"Finished geting query term coverage vector"<<endl;
        show_query_term_coverage(query_term_coverage,cu);


        // for(map<string,float>:: iterator it=average_idf.begin(); it!=average_idf.end(); ++it){

        //     cout<<it->first<<" "<<it->second<<endl;
        // }
        r.close();
    } catch( lemur::api::Exception& e ) {
        LEMUR_ABORT(e);
    } catch( ... ) {
        std::cout << "Caught an unhandled exception" << std::endl;
    }
    return 0;
}