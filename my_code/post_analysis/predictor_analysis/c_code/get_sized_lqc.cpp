/* get WIG for only phrases
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



map<string, vector<string> > get_results(char* result_file,const int& tune_documents){
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





int get_internal_did( indri::collection::Repository& r, const string& ex_did ) {
  indri::collection::CompressedCollection* collection = r.collection();
  std::string attributeName = "docno";
  std::vector<lemur::api::DOCID_T> documentIDs;

  documentIDs = collection->retrieveIDByMetadatum( attributeName, ex_did );

  return documentIDs[0];

}



class UnorderedSizedPhrases{
    private:
        int length;
        bool debug;
        vector< vector<string> > phrases;
        vector<int> phrase_ids;
        vector<string> phrase_string;
        map<int,string> uw_phrase_string;
        map<int, map<int,float> > uw_document_map;

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
    public:
        UnorderedSizedPhrases(){

        }

        UnorderedSizedPhrases(vector<string> query_words,int length,bool debug ){
            this->length = length;
            this->debug = debug;
            if(length> query_words.size()){
                cout<<"Wrong: the phrase size cannot be greater than query size!"<<endl;
                cout<<length<<" - "<<query_words.size()<<endl;
                exit(-1);
            }
            if(length <= 1){
                cout<<"Wrong:phrase length needs to be greater than 1!"<<endl;
                cout<<"Now inputed phrase length "<<length<<endl;
                exit(-1);
            }
            
            vector< vector<string> > subwords_vector;
            int end_index = query_words.size()-1;
            int sub_vector_size = length;
            vector< vector<int> > sub_index_vector = get_index_vector(0,end_index,sub_vector_size); 
            int unordered_phrase = 0;
            for(vector< vector<int> >::iterator iit=sub_index_vector.begin(); iit!=sub_index_vector.end();++iit){
                vector<string> temp_phrase_vector ;
                string temp_phrase_string;
                for(std::vector<int>::iterator sit=(*iit).begin(); sit!=(*iit).end();++sit){
                    temp_phrase_vector.push_back( query_words[*sit] );
                    // temp_phrase_string += query_words[*sit] + " ";
                }
                for(int m=temp_phrase_vector.size()-1;m>=0;m--){
                    temp_phrase_string += temp_phrase_vector[m] + " ";
                }
                this->phrases.push_back(temp_phrase_vector);
                phrase_ids.push_back(unordered_phrase);
                unordered_phrase +=1 ;
                phrase_string.push_back( temp_phrase_string );
            }


            
        }

        int phrase_length(){
            return length;
        }

        vector<int> get_phrase_ids(){
            return phrase_ids;
        }

        vector<string> get_single_phrase(int id){
            return phrases[id];
        }

        string get_single_phrase_string(int id){
            return phrase_string[id];
        }

        int phrase_count(){
            return phrase_ids.size();
        }

        void show(){
            cout<<"length "<<length<<":";
            for(int i=0;i<phrase_string.size();i++){
                cout<<phrase_string[i]<<",";
            }
            cout<<endl;
        }

        void get_uw_document_map(const std::string& indexName){
            indri::api::QueryEnvironment env;

            // compute the expression list using the QueryEnvironment API
            env.addIndex( indexName );
            for(int i=0;i<phrase_ids.size();i++){
                if(debug) cout<<"Phrase frequency for unrodered phrases"<<phrase_string[i]<<endl;
                int pid = phrase_ids[i];
                

                string uw_string;
                if(length==2){
                    uw_string = "#uw8("+phrase_string[pid] +")";
                }
                else{
                    int window_size = 4*length;
                    // uw_string = "#uw"+string( itoa(window_size))+"("+phrase_string[pid] +")";
                    uw_string = "#uw"+to_string(window_size)+"("+phrase_string[pid] +")";

                }

                uw_phrase_string[pid] = uw_string;
                if(debug) cout<<"\t"<<uw_string<<endl;
                uw_document_map[pid] = get_expression_document_map(env,uw_string);

            }
            env.close();

        }

        float get_processed_phrase_count(vector<int>& internal_id_vector,const string& cu){
            if(internal_id_vector.size() == 0){
                return .0;
            }

            map<int,int> output_count ;
            for(map<int, map<int,float> >::iterator wit=uw_document_map.begin(); wit!=uw_document_map.end();++wit){
                int pid = wit->first;
                output_count[pid] = 0;
                for(int i=0;i<internal_id_vector.size();i++){
                    int temp_internal_id = internal_id_vector[i];
                    if(wit->second.find(temp_internal_id)!=wit->second.end()){
                        output_count[pid] += 1;
                    }

                }
            }
            float final_value =.0;
            for(map<int,int>::iterator oit=output_count.begin();oit!=output_count.end();++oit){
                
                if(cu=="binary"){
                    if(oit->second!=0){
                        final_value = 1;
                    }
                }
                else if(cu=="average"){
                    final_value += (oit->second*1.0/internal_id_vector.size())/output_count.size();
                    
                }
                else{
                    float temp_value = oit->second*1.0/internal_id_vector.size();
                    if(temp_value>final_value){
                        final_value = temp_value;
                    }
                }
            }
            return final_value;
        }
        

        float get_UF_document_count(const int& phrase_id,const int& internal_did){
            if (uw_document_map[phrase_id].find(internal_did)!=uw_document_map[phrase_id].end() ){
                return uw_document_map[phrase_id][internal_did];
            }
            else{
                return .0;
            }
        }

       

        
        



};


void get_feature_document_count( UnorderedSizedPhrases& unordered_sized_phrases, map<int,float>& uf, const int& internal_did){
    vector<int> phrase_ids = unordered_sized_phrases.get_phrase_ids();
    for(int i=0;i<phrase_ids.size();i++){
        int phrase_id = phrase_ids[i];
        uf[phrase_id] = unordered_sized_phrases.get_UF_document_count(phrase_id,internal_did);
    }
}





class Query{
    private:
        vector<string> terms;
        string qid;
        int term_count;
        int phrase_count;
        bool debug;

    public:
        map<int, UnorderedSizedPhrases > unordered_sized_phrases;

        Query(){

        }

        Query(vector<string> query_words,string qid,bool debug){
            this->debug = debug;
            this->qid = qid;
            for(int i=0;i<query_words.size();i++){
                terms.push_back(query_words[i]);
            }
            term_count = terms.size();
            phrase_count = 0;
            if(query_words.size()>=2){
                for(int j=2;j<=min(int(query_words.size()),5);j++){
                    unordered_sized_phrases[j] = UnorderedSizedPhrases(query_words,j,debug);
                    phrase_count += unordered_sized_phrases[j].phrase_count();
                }
            }
        }

        

       

        void get_uw_document_map(const std::string& indexName){

            for(map<int,UnorderedSizedPhrases>::iterator it=unordered_sized_phrases.begin();it!=unordered_sized_phrases.end();++it){
                it->second.get_uw_document_map(indexName);
            }
        }

        float compute_lqc(indri::collection::Repository& r,vector<string>& document_results,const string& cu){
            indri::server::LocalQueryServer local(r);
            float sized_lqc = .0;
            vector<int> internal_id_vector;
            if(debug) cout<<"Get Internal dids"<<endl;
            
            for(int i=0;i<document_results.size();i++){
                string ex_did = document_results[i];
                int internal_did = get_internal_did(r,ex_did);
                internal_id_vector.push_back(internal_did);
            }
            
            for(map<int,UnorderedSizedPhrases>::iterator it=unordered_sized_phrases.begin(); it!=unordered_sized_phrases.end();++it){
                int phrase_size = it->first;
                float processed_phrase_cout = log2(phrase_size)*it->second.get_processed_phrase_count(internal_id_vector,cu);
                if (debug) cout<<"add value "<<processed_phrase_cout<< " for phrase size "<<phrase_size<<endl;
                sized_lqc += processed_phrase_cout;
            }


            
            if(unordered_sized_phrases.size()==0){
                sized_lqc = 1.0;
            }
            return sized_lqc;
        }
        
        void show(){
            cout<<"Query:"<<endl;
            cout<<"qid: "<<qid<<endl;
            cout<<"terms:";
            for(int i =0;i<terms.size();i++){
                cout<<terms[i]<<" ,";
            }
            cout<<endl;
            cout<<"phrases:"<<endl;
            for(map<int,UnorderedSizedPhrases>::iterator it=unordered_sized_phrases.begin();it!=unordered_sized_phrases.end();++it){
                it->second.show();
            }
        }
};








map<string, float> get_sized_lqc(indri::collection::Repository& r,map<string, vector<string> >& results,map<string, vector<string> >& queries, const string& indexName, const bool& debug, const string& cu){
  map<string, float> lqc;
  map<string,Query> query_with_phrases;
  for(map<string, vector<string> >::iterator it=queries.begin();it!=queries.end(); ++it ){
    string qid = it->first;
    query_with_phrases[qid] = Query(it->second,qid,debug);
    if(debug) cout<<"For query "<<qid<<endl;
    if(debug) cout<<"Got queries"<<endl;
    query_with_phrases[qid].get_uw_document_map(indexName);
    if(debug) cout<<"Got unordered window-document map"<<endl;
    float query_lqc = query_with_phrases[qid].compute_lqc(r,results[qid],cu);
    lqc[qid] = query_lqc;
    // query_with_phrases[qid].show();
    // for(vector<string>::const_iterator sid=it->second.begin(); sid!=it->second.end(); ++sid){

    // }
  }
    return lqc;

}


static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query" ) ) || 
      !( param.exists( "index" ) ) ||
      !( param.exists( "result") ) ||
      !( param.exists( "cu"    ) )  ) {
   std::cerr << "get_sized_lqc usage: " << std::endl
             << "   get_sized_lqc -query=myquery -index=myindex -result=myresult -cu=cu" << std::endl;
   exit(-1);
  }

  string cu = param[ "cu" ];
  if(  cu!="binary" &&
            cu!="average" &&
            cu!="max" ){
    std::cerr << "cu must be one of the values below: " << std::endl
             << "   binary average max" << std::endl;
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
        string cu = param[ "cu" ];
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

        map<string, vector<string> > results = get_results(result_file,tune_documents);
        // cout<<"finished geting results"<<endl;

        map<string, float> lqc = get_sized_lqc(r,results,queries,rep_name,debug,cu);
        for(map<string,float>:: iterator it=lqc.begin(); it!=lqc.end(); ++it){

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