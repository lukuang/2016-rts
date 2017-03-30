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






map<string, vector<string> > get_results(char* result_file){
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
                    if(results[qid].size()==10){
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


class SizedPhrases{
    private:
        int length;
        bool debug;
        vector< vector<string> > phrases;
        vector<int> phrase_ids;
        vector<string> phrase_string;
        map<int,float> uw_cf;
        map<int,string> uw_phrase_string;
        map<int, map<int,float> > uw_document_map;
        map<int,float> ow_cf;
        map<int,string> ow_phrase_string;
        map<int, map<int,float> > ow_document_map;

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
        SizedPhrases(){

        }

        SizedPhrases(vector<string> query_words,int length,bool debug){
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
            for(int i=0; i<=query_words.size()-length;i++){
                vector<string> temp_phrase_vector ;
                string temp_phrase_string;
                for(int j=0;j<length;j++){
                    temp_phrase_vector.push_back( query_words[i+j] );
                    temp_phrase_string += query_words[i+j] + " ";
                }
                this->phrases.push_back(temp_phrase_vector);
                phrase_ids.push_back(i);
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

        void compute_pcf(const std::string& indexName){
            indri::api::QueryEnvironment env;

            // compute the expression list using the QueryEnvironment API
            env.addIndex( indexName );
            for(int i=0;i<phrase_ids.size();i++){
                if(debug) cout<<"Phrase frequency for "<<phrase_string[i]<<endl;
                int pid = phrase_ids[i];
                string ow_string = "#1("+phrase_string[pid] +")";
                ow_phrase_string[pid] = ow_string;
                ow_cf[pid] = env.expressionCount( ow_string );
                if(debug) cout<<"\t"<<ow_string<<" "<<ow_cf[pid]<<endl;
                ow_document_map[pid] = get_expression_document_map(env,ow_string);

                string uw_string;
                if(length==2){
                    uw_string = "#uw140("+phrase_string[pid] +")";
                }
                else{
                    int window_size = 4*length;
                    // uw_string = "#uw"+string( itoa(window_size))+"("+phrase_string[pid] +")";
                    uw_string = "#uw"+to_string(window_size)+"("+phrase_string[pid] +")";

                }

                uw_phrase_string[pid] = uw_string;
                uw_cf[pid] = env.expressionCount( uw_string );
                if(debug) cout<<"\t"<<uw_string<<" "<<uw_cf[pid]<<endl;
                uw_document_map[pid] = get_expression_document_map(env,uw_string);

            }
            env.close();

        }

        float get_OF_document_count(const int& phrase_id,const int& internal_did){
            if (ow_document_map[phrase_id].find(internal_did)!=ow_document_map[phrase_id].end() ){
                return ow_document_map[phrase_id][internal_did];
            }
            else{
                return .0;
            }
        }

        float get_UF_document_count(const int& phrase_id,const int& internal_did){
            if (uw_document_map[phrase_id].find(internal_did)!=uw_document_map[phrase_id].end() ){
                return uw_document_map[phrase_id][internal_did];
            }
            else{
                return .0;
            }
        }

        float get_OF_collection_count(const int& phrase_id){
            return ow_cf[phrase_id];
        }

        float get_UF_collection_count(const int& phrase_id){
            return uw_cf[phrase_id];
        }
        



};

class Document{
    private:
        string ex_did;
        int internal_did;
        map <string, int> stem_count;
        vector <string> stem_vector;
        string stemmed_doc_string;
        bool debug;

        int dl = 0;
    public:
        Document(){

        }

        Document(indri::collection::Repository& r, const string& ex_did, bool debug ){
            internal_did = get_internal_did(r,ex_did);
            this->debug = debug;
            
            indri::server::LocalQueryServer local(r);

            std::vector<lemur::api::DOCID_T> documentIDs;
            documentIDs.push_back(internal_did);
            indri::server::QueryServerVectorsResponse* response = local.documentVectors( documentIDs );

            if( response->getResults().size() ) {
                indri::api::DocumentVector* docVector = response->getResults()[0];

                for( size_t i=0; i<docVector->positions().size(); i++ ) {
                  int position = docVector->positions()[i];
                  const std::string& stem = docVector->stems()[position];
                  stemmed_doc_string += stem+" ";
                  if(stem_count.find(stem)==stem_count.end()){
                    stem_count[stem] = 0;
                  }
                  stem_count[stem] += 1;
                  stem_vector.push_back(stem);
                  dl += 1;
                }
                delete docVector;
            }
        }

        void get_feature_document_count(indri::collection::Repository& r, const string& term, float& tf){
            string stem = r.processTerm( term );
            tf = .0;
            if(stem_count.find(stem)!=stem_count.end()){
                tf = stem_count[term]*1.0;
            }
        }

        void get_feature_document_count( SizedPhrases& phrases, map<int,float>& of, map<int,float>& uf){
            vector<int> phrase_ids = phrases.get_phrase_ids();
            for(int i=0;i<phrase_ids.size();i++){
                int phrase_id = phrase_ids[i];
                of[phrase_id] = phrases.get_OF_document_count(phrase_id,internal_did);
                uf[phrase_id] = phrases.get_UF_document_count(phrase_id,internal_did);
            }
        }

        int get_dl(){
            return dl;
        }

};


class Query{
    private:
        vector<string> terms;
        map <string,float> tcf;
        string qid;
        int term_count;
        int phrase_count;
        bool debug;

    public:
        map<int, SizedPhrases > sized_phrases;

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
                for(int j=2;j<=query_words.size();j++){
                    sized_phrases[j] = SizedPhrases(query_words,j,debug);
                    phrase_count += sized_phrases[j].phrase_count();
                }
            }
        }

        void get_collection_frequency(indri::collection::Repository& r,const std::string& indexName){
            compute_tcf(r);
            compute_pcf(indexName);
        }

        void compute_tcf(indri::collection::Repository& r){
            indri::server::LocalQueryServer local(r);
            if(debug) cout<<"Term frequency:"<<endl;
            for(int i =0;i<terms.size();i++){
                tcf[ terms[i] ] = local.termCount( terms[i] );
                 if(debug) cout<<"\t"<<terms[i] <<" "<<tcf[ terms[i] ]<<endl;
            }
        }

        void compute_pcf(const std::string& indexName){
            for(map<int,SizedPhrases>::iterator it=sized_phrases.begin();it!=sized_phrases.end();++it){
                it->second.compute_pcf(indexName);
            }
        }

        float compute_query_pwig(indri::collection::Repository& r,vector<string>& document_results){
            indri::server::LocalQueryServer local(r);
            float C = 1.0*local.termCount();
            float wig = .0;
            for(int i=0;i<document_results.size();i++){
                string ex_did = document_results[i];
                if(debug) cout<<"Process document "<<ex_did<<endl;
                Document single_document = Document(r,ex_did,debug);
                int dl = single_document.get_dl();
                float alpha = 1000.0/(dl+1000.0); 
                if(phrase_count!=0){
                    float phrase_lambda = 1.0/sqrt(phrase_count);
                    //compute wig for phrase features
                    if(debug) cout<<"Get Phrase features"<<endl;
                    for(map<int,SizedPhrases>::iterator it=sized_phrases.begin(); it!=sized_phrases.end();++it){
                        map<int,float> of;
                        map<int,float> uf;
                        single_document.get_feature_document_count(it->second,of,uf);
                        for(map<int,float>::iterator oit=of.begin();oit!=of.end();++oit){
                            int phrase_id = oit->first;
                            string phrase_string = it->second.get_single_phrase_string(phrase_id);
                            if(debug) cout<<"For phrase "<<phrase_string<<endl;
                            float cof = it->second.get_OF_collection_count(phrase_id);
                            float cuf = it->second.get_UF_collection_count(phrase_id);
                            if(cof!=.0){
                                float of_document_score = (1-alpha)*(of[phrase_id]/dl) + alpha*(cof/C);
                                float of_collection_score = cof/C;
                                wig += phrase_lambda*log2( of_document_score/of_collection_score);
                                if(debug) cout<<"add "<<phrase_lambda*log2( of_document_score/of_collection_score)<<"for unordered feature to wig"<<endl;
                            }
                            if(cuf!=.0){              
                                float uf_document_score = (1-alpha)*(uf[phrase_id]/dl) + alpha*(cuf/C);
                                float uf_collection_score = cuf/C;
                                wig += phrase_lambda*log2( uf_document_score/uf_collection_score);
                                if(debug) cout<<"add "<< phrase_lambda*log2( uf_document_score/uf_collection_score)<<"for unordered feature to wig"<<endl;
                            }
                        }
                    }
                }
                else{
                    float term_lambda = 1.0/sqrt(term_count);

                    //compute wig for term features
                    if(debug) cout<<"Get term freatures:"<<endl;
                    for(int j=0;j<terms.size();j++){
                        string term = terms[j];
                        float tf ;
                        single_document.get_feature_document_count(r,term,tf);
                        if (debug) cout<<"\tterm cout for "<<term<<" is "<<tf<<endl;
                        if(tcf[term] != .0){
                            float feature_document_score = (1-alpha)*(tf/dl) + alpha*(tcf[term]/C);
                            float feature_collection_score = tcf[term]/C;
                            wig += term_lambda*log2( feature_document_score/feature_collection_score);
                            if(debug) cout<<"add "<<term_lambda*log2( feature_document_score/feature_collection_score)<<"for term "<<term<<" to wig"<<endl;
                        }
                        
                    }
                }
                
            }
            if(document_results.size()!=0){
                wig /= document_results.size();
            }
            return wig;
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
            for(map<int,SizedPhrases>::iterator it=sized_phrases.begin();it!=sized_phrases.end();++it){
                it->second.show();
            }
        }
};








map<string, float> get_pwig(indri::collection::Repository& r,map<string, vector<string> >& results,map<string, vector<string> >& queries, const string& indexName, const bool& debug){
  map<string, float> wig;
  map<string,Query> query_with_phrases;
  for(map<string, vector<string> >::iterator it=queries.begin();it!=queries.end(); ++it ){
    string qid = it->first;
    query_with_phrases[qid] = Query(it->second,qid,debug);
    if(debug) cout<<"For query "<<qid<<endl;
    if(debug) cout<<"Got queries"<<endl;
    query_with_phrases[qid].get_collection_frequency(r,indexName);
    if(debug) cout<<"Got collection frequency"<<endl;
    float query_wig = query_with_phrases[qid].compute_query_pwig(r,results[qid]);
    wig[qid] = query_wig;
    // query_with_phrases[qid].show();
    // for(vector<string>::const_iterator sid=it->second.begin(); sid!=it->second.end(); ++sid){

    // }
  }
    return wig;

}


static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query" ) )    || 
      !( param.exists( "index" ) ) ||
      !( param.exists( "result") ) ) {
   std::cerr << "get_pwig usage: " << std::endl
             << "   get_pwig -query=myquery -index=myindex -result=myresult" << std::endl;
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

        r.openRead( rep_name );
        vector<string> query_words = get_unstemmed_query_words(r,query_file,queries);
        // output(idf,dest_dir);

        // convert queries to queer sub word vectors to prepare 
        // for cooccurrence cvomputation.
        // For example, for a query {qid: [w1,w2,w3]}
        // the result would be {qid: [ [w1,w2],[w1,w2],[w1,w3],[w1,w2,w3] ]}

        map<string, vector<string> > results = get_results(result_file);
        // cout<<"finished geting results"<<endl;


        map<string, float> wig = get_pwig(r,results,queries,rep_name,debug);
        for(map<string,float>:: iterator it=wig.begin(); it!=wig.end(); ++it){

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