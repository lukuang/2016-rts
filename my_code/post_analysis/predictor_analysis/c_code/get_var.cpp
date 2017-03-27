/* get variance of the tf-idf weights of query terms
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


float get_term_variance(indri::collection::Repository& r,const string& term){
    indri::server::LocalQueryServer local(r);
    indri::collection::Repository::index_state state = r.indexes();
    float term_variance = .0;
    int df = local.documentStemCount(term);
    float n = 1.0*local.documentCount();
    if(df==0){
        return .0;
    }
    else{
        
      for( size_t i=0; i<state->size(); i++ ) {
        float idf = log( 1+n/df );
        float average_weight = .0;
        vector<float> weights;


        indri::index::Index* index = (*state)[i];
        indri::thread::ScopedLock( index->iteratorLock() );

        indri::index::DocListIterator* iter = index->docListIterator( term );
        if (iter == NULL) continue;

        iter->startIteration();

        indri::index::DocListIterator::DocumentData* entry;

        for( iter->startIteration(); iter->finished() == false; iter->nextEntry() ) {
          entry = iter->currentEntry();
          int term_count = entry->positions.size();
          float term_weight = 1 + log(term_count)*idf;
          average_weight += term_weight/df;
          weights.push_back(term_weight);
        }
        for(int j=0;j<weights.size();j++){
            term_variance += pow( (weights[j]-average_weight),2)/df;
        }
        delete iter;
        return term_variance;
      }

      

    }

}

map<string, float>  compute_var(indri::collection::Repository& r,map<string, vector<string> >& queries){
    indri::server::LocalQueryServer local(r);
    map<string, float> var;

    float n = 1.0*local.documentCount();
    for(map<string, vector<string> >:: iterator it=queries.begin(); it!=queries.end(); ++it){
        float query_scq = .0;
        string qid = it->first;
        vector<string> query_words = it->second;
         // if (qid == "MB438"){
         //    cout<<"MB438:"<<endl;
         // }
        float query_variance = .0;
        for(vector<string>::iterator wit = query_words.begin(); wit!=query_words.end(); ++wit){
            // if (qid == "MB438"){
            //     cout<<"\t"<<*wit<<":"<<idf[*wit]<<endl;
            // }
            query_variance += get_term_variance(r,*wit);
            
        }
        var[qid] = query_variance;
    }
    return var;

}

static void usage( indri::api::Parameters param ) {
  if( !param.exists( "query" ) || 
      !( param.exists( "index" ) )) {
   std::cerr << "get_scq usage: " << std::endl
             << "   get_scq -query=myquery -index=myindex" << std::endl;
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

        string rep_name = param[ "index" ];
        //int percent_threshold = atoi(argv[2]);
        //string idf_term  = argv[3];
        //float variance_threshold = atof(argv[4]);

        map<string, float> var;
        map<string, vector<string> > queries;
        r.openRead( rep_name );
        
        vector<string> query_words = get_query_words(r,query_file,queries);
        // output(idf,dest_dir);

        var = compute_var(r,queries);

        for(map<string,float>:: iterator it=var.begin(); it!=var.end(); ++it){

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