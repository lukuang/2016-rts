/* get bm25 scores for result documents. For debug purposes
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
        for(vector<string>::const_iterator sid=it->second.begin(); sid!=it->second.end(); ++sid){
            map<string , int> doc_term_map = get_term_map(r,*sid);
            one_result_term_map.push_back(doc_term_map);
        }

        result_term_map[it->first] = one_result_term_map;
    }
    return result_term_map;
}


map<string, vector< float>  >  compute_document_score(indri::collection::Repository& r,map<string, vector<string> >& queries,map<string, vector< map<string,int> > > result_term_map){
    indri::server::LocalQueryServer local(r);

    float avdl = get_avdl(r);
    map<string, vector<float>  > document_score;
    float n = 1.0*local.documentCount();
    for(map<string, vector<string> >:: iterator it=queries.begin(); it!=queries.end(); ++it){
        string qid = it->first;
        vector<string> query_words = it->second;
        document_score[qid] = vector<float>();
        cout<<"For query "<<qid<<":"<<endl;
        vector< map<string,int> > query_result_term_map = result_term_map[qid];
        for(int i=0; i<query_result_term_map.size();i++){
            map<string,int> document_term_map = query_result_term_map[i];
            float single_document_score = .0;
            int d_size = 0;
            for(map<string,int>::iterator dit=document_term_map.begin();dit!=document_term_map.end();++dit){
                d_size += dit->second;
            }
            for(vector<string>::iterator wit = query_words.begin(); wit!=query_words.end(); ++wit){
            
                float k1=1.0;
                int k3=1000;
                float b = 0.75;

                string term = *wit;
                
                if(document_term_map.find(term)!=document_term_map.end()){
                    int df = local.documentStemCount(*wit);
                    int tf = document_term_map[term];
                    cout<<"\tterm "<<term<<", tf: "<<tf<<endl;
                    float idf = log( (n-df+0.5)*1.0/(df+0.5)  );
                    if (idf <0){
                        cout<<"For query: "<<qid<<" term "<<term<<" has negative idf "<<to_string(idf)<<endl;
                    }
                    double numerator = idf * (k1+1)*tf ;
                    numerator *= (k3+1)*1.0/(k3+1);
                    double denominator = k1*( (1-b) + b*d_size*1.0/avdl ) + tf;
                    single_document_score +=  numerator / denominator;                
                }
                

            }
            document_score[qid].push_back(single_document_score);
        }
        
        
        
        
    }
    return document_score;

}

static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query" )) || 
      !( param.exists( "index" )) ||
      !( param.exists( "result" ))  ) {
   std::cerr << "get_document_score usage: " << std::endl
             << "get_document_score -query=myquery -index=myindex -result=result" << std::endl;
   exit(-1);
  }
}


int main(int argc, char** argv){
    indri::collection::Repository r;
    try {
        indri::api::Parameters& param = indri::api::Parameters::instance();
        param.loadCommandLine( argc, argv );
        usage( param );
        std::string query_file_string = param[ "query" ];
        char* query_file = new char[query_file_string.length()+1];
        memcpy(query_file, query_file_string.c_str(), query_file_string.length()+1);

        std::string result_file_string = param[ "result" ];
        char* result_file = new char[result_file_string.length()+1];
        memcpy(result_file, result_file_string.c_str(), result_file_string.length()+1);

        string rep_name = param[ "index" ];
        int tune_documents = param.get("tune_documents",50);
        //int percent_threshold = atoi(argv[2]);
        //string idf_term  = argv[3];
        //float variance_threshold = atof(argv[4]);

        map<string, vector< float>  > document_score;
        map<string, vector<string> > queries;
        r.openRead( rep_name );
        
        vector<string> query_words = get_query_words(r,query_file,queries);
        map<string, vector<string> > results = get_results(result_file,tune_documents);
        // output(idf,dest_dir);
        map<string, vector< map<string,int> > > result_term_map = get_result_term_map(r,results);
        document_score = compute_document_score(r,queries,result_term_map);

        for(map<string, vector< float> >:: iterator it=document_score.begin(); it!=document_score.end(); ++it){

            string qid = it->first;
            cout<<"Query "<<qid<<":"<<endl;
            vector< float> query_document_scores = document_score[qid];
            for(int i=0;i<query_document_scores.size();i++){
                float score = query_document_scores[i];
                int id = i+1;
                cout<<"\t"<<to_string(id)<<" :"<<to_string(score)<<endl;
            }
        }
        r.close();
    } catch( lemur::api::Exception& e ) {
        LEMUR_ABORT(e);
    } catch( ... ) {
        std::cout << "Caught an unhandled exception" << std::endl;
    }
    return 0;
}