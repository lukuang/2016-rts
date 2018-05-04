/* get whether the results have any tweets
that contain all query terms
*/


#include "indri/Repository.hpp"
#include "indri/CompressedCollection.hpp"
#include "indri/LocalQueryServer.hpp"
#include "indri/ScopedLock.hpp"
#include "indri/Parameters.hpp"
#include "indri/QueryEnvironment.hpp"
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
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


vector< vector<int> > get_index_vector(const int& begin,const int& end,const int& size){
    vector< vector<int> > index_vector;
    int range = end-begin+1;
    if(range >= size){
        for(int i = begin; i<= end; i++){
            if(size>1){
                int sub_size = size-1;
                vector< vector<int> > sub_index_vector = get_index_vector(i+1,end,sub_size);
                
                for(vector< vector<int> >::iterator iit=sub_index_vector.begin(); iit!=sub_index_vector.end();++iit){
                    (*iit).push_back(i);
                    index_vector.push_back(*iit);
                }

                // vector< vector<int> > sub_index_vector_full_size = get_index_vector(i+2,end,size);
                // for(vector< vector<int> >::iterator iit=sub_index_vector_full_size.begin(); iit!=sub_index_vector_full_size.end();++iit){
                //     index_vector.push_back(*iit);
                // }
            }
            else{
                std::vector<int> single_word;
                single_word.push_back(i);
                index_vector.push_back(single_word);
            }
        }
    }
    return index_vector;
}


int get_internal_did( indri::collection::Repository& r, const string& ex_did ) {
  indri::collection::CompressedCollection* collection = r.collection();
  std::string attributeName = "docno";
  std::vector<lemur::api::DOCID_T> documentIDs;

  documentIDs = collection->retrieveIDByMetadatum( attributeName, ex_did );

  return documentIDs[0];

}

map<string, vector<int> > get_results(indri::collection::Repository& r,char* result_file,const int& tune_documents){
    ifstream f;
    string line;
    string qid="";
    map<string, vector<int> > results;
    f.open(result_file);
    if(f.is_open()){
        while(getline(f,line)){
            size_t qid_founder = line.find_first_of(" ");
            if (qid_founder!=string::npos){
                qid = line.substr(0,qid_founder);
                if(results.find( qid ) == results.end()){
                    results[qid] = vector<int>();
                }
                line = line.substr(qid_founder+4);
                size_t docid_finder = line.find_first_of(" ");
                if(docid_finder != string::npos){
                    if(results[qid].size()==tune_documents){
                        continue;
                    }
                    else{
                        string docid = line.substr(0,docid_finder);
                        results[qid].push_back(get_internal_did(r, docid));
                    }
                    
                }

            }
        }
    }
    return results;
}







map<int,float> get_expression_document_map(indri::api::QueryEnvironment& env,const std::string& expression){
    map<int,float> expression_document_map;
    vector<indri::api::ScoredExtentResult> result = env.expressionList( expression );
    for( size_t i=0; i<result.size(); i++ ) {
        int internal_did =  result[i].document;
        float expression_count = result[i].score;
        expression_document_map[internal_did] = expression_count;

    }
    return expression_document_map;
}

float check_cover_all_terms(indri::collection::Repository& r,vector<int>& document_results,const string& query_string,const string& indexName){
    indri::api::QueryEnvironment env;

    env.addIndex( indexName );
    map<int,float> expression_document_map = get_expression_document_map(env,query_string);
    for (vector<int>::iterator dit=document_results.begin(); dit!=document_results.end(); ++dit){
        int docid = *dit;
        if(expression_document_map.find( docid ) != expression_document_map.end()){
            return 1.0;
        }
    }
    return 0.0;
}

map<string, float> get_cover_all_terms(indri::collection::Repository& r,map<string, vector<int> >& results,map<string, vector<string> >& queries, const string& indexName, const bool& debug){
  map<string, float> cover_all_terms;
  for(map<string, vector<string> >::iterator it=queries.begin();it!=queries.end(); ++it ){
    string qid = it->first;
    string query_string = "";
    for (vector<string>::iterator t=it->second.begin(); t!=it->second.end(); ++t){
        query_string += *t + " ";
    } 
    if(debug) cout<<"For query "<<qid<<endl;
    if(debug) cout<<"Got queries"<<endl;
    cover_all_terms[qid] = check_cover_all_terms(r,results[qid],query_string, indexName);
    // query_with_phrases[qid].show();
    // for(vector<string>::const_iterator sid=it->second.begin(); sid!=it->second.end(); ++sid){

    // }
  }
    return cover_all_terms;

}


static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query" ) )    || 
      !( param.exists( "index" ) ) ||
      !( param.exists( "result") ) ) {
   std::cerr << "get_cover_all_terms usage: " << std::endl
             << "   get_cover_all_terms -query=myquery -index=myindex -result=myresult" << std::endl;
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

        int tune_documents = param.get("tune_documents",10);
        r.openRead( rep_name );
        vector<string> query_words = get_unstemmed_query_words(r,query_file,queries);
        // output(idf,dest_dir);

        // convert queries to queer sub word vectors to prepare 
        // for cooccurrence cvomputation.
        // For example, for a query {qid: [w1,w2,w3]}
        // the result would be {qid: [ [w1,w2],[w1,w2],[w1,w3],[w1,w2,w3] ]}

        map<string, vector<int> > results = get_results(r, result_file,tune_documents);
        // cout<<"finished geting results"<<endl;

        map<string, float> cover_all_terms = get_cover_all_terms(r,results,queries,rep_name,debug);
        for(map<string,float>:: iterator it=cover_all_terms.begin(); it!=cover_all_terms.end(); ++it){

            cout<<it->first<<" "<<it->second<<endl;
        }
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