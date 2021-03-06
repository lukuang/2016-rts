/* get idf average for query words given index()
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


void get_statistics(indri::collection::Repository& r,map<string, float>& idf,vector<string>& query_words){

    indri::server::LocalQueryServer local(r);
    float n = 1.0*local.documentCount();
    for(vector<string>::iterator it = query_words.begin(); it!=query_words.end(); ++it){
        int df = local.documentStemCount(*it) ;
        // cout<<"df for "<<*it<<" is "<<local.documentStemCount(*it)<<endl;

        if( df == 0){
            idf[*it] = .0;
        }
        else{
            idf[*it] = log(n/df );        
        }
    }
    // string term = "immigrants";
    // string stem = r.processTerm(term);

    // cout<<"df for "<<term<<" is "<<local.documentStemCount(term)<<endl;
    // cout<<"df for "<<stem<<" is "<<local.documentStemCount(stem)<<endl;
}


map<string, float>  compute_average_idf(map<string, vector<string> >& queries,map<string, float>& idf){
    map<string, float> average_idf;
    for(map<string, vector<string> >:: iterator it=queries.begin(); it!=queries.end(); ++it){
        float query_average_idf = .0;
        string qid = it->first;
        vector<string> query_words = it->second;
         // if (qid == "MB438"){
         //    cout<<"MB438:"<<endl;
         // }
        for(vector<string>::iterator wit = query_words.begin(); wit!=query_words.end(); ++wit){
            // if (qid == "MB438"){
            //     cout<<"\t"<<*wit<<":"<<idf[*wit]<<endl;
            // }
            query_average_idf += idf[*wit];      

        }
        query_average_idf /= query_words.size();
        average_idf[qid] = query_average_idf;
    }
    return average_idf;

}

static void usage( indri::api::Parameters param ) {
  if( !param.exists( "query" ) || 
      !( param.exists( "index" ) )) {
   std::cerr << "get_average_idf usage: " << std::endl
             << "   get_average_idf -query=myquery -index=myindex" << std::endl;
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

        map<string, float> idf;
        map<string, float> average_idf;
        map<string, vector<string> > queries;
        r.openRead( rep_name );
        
        vector<string> query_words = get_query_words(r,query_file,queries);
        get_statistics(r,idf,query_words);
        // output(idf,dest_dir);

        average_idf = compute_average_idf(queries,idf);

        for(map<string,float>:: iterator it=average_idf.begin(); it!=average_idf.end(); ++it){

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