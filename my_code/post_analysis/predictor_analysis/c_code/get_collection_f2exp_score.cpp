/* get collection f2exp score by treating the whole collection as a document
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




map<string, float>  compute_collection_score(indri::collection::Repository& r,map<string, vector<string> >& queries){
    indri::server::LocalQueryServer local(r);

    float avdl = get_avdl(r);
    map<string, float> collection_score;
    float n = 1.0*local.documentCount();
    for(map<string, vector<string> >:: iterator it=queries.begin(); it!=queries.end(); ++it){
        float query_collection_score = .0;
        string qid = it->first;
        vector<string> query_words = it->second;
         // if (qid == "MB438"){
         //    cout<<"MB438:"<<endl;
         // }
        for(vector<string>::iterator wit = query_words.begin(); wit!=query_words.end(); ++wit){
            // if (qid == "MB438"){
            //     cout<<"\t"<<*wit<<":"<<idf[*wit]<<endl;
            // }
            int f_ct = local.stemCount(*wit);
            int df = local.documentStemCount(*wit);

            if(f_ct!=0 && df!=0){
                float idf = (n+1)*1.0/ df;
                double numerator = idf * f_ct;
                double denominator = f_ct + 0.1 + (0.1*n);
                query_collection_score +=  numerator / denominator;                
            }

        }
        collection_score[qid] = query_collection_score;
    }
    return collection_score;

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

        map<string, float> collection_score;
        map<string, vector<string> > queries;
        r.openRead( rep_name );
        
        vector<string> query_words = get_query_words(r,query_file,queries);
        // output(idf,dest_dir);

        collection_score = compute_collection_score(r,queries);

        for(map<string,float>:: iterator it=collection_score.begin(); it!=collection_score.end(); ++it){

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