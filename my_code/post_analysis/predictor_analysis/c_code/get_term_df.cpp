/* get df for individual query terms
then take log of the value and output to
buketed values: 0 1 2 3 4
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


void get_statistics(indri::collection::Repository& r,map<string, int>& df,vector<string>& query_words){

    indri::server::LocalQueryServer local(r);
    for(vector<string>::iterator it = query_words.begin(); it!=query_words.end(); ++it){
        int raw_df = local.documentCount(*it) ;
        // cout<<"df for "<<*it<<" is "<<local.documentStemCount(*it)<<endl;

        if( raw_df == 0){
            df[*it] = 0;
        }
        else{
            float log_df = log(raw_df );
            if(log_df<1){
                df[*it] = 0;
            }
            else if(log_df<2){
                df[*it] = 1;        
            }
            else if(log_df<3){
                df[*it] = 2;        
            }
            else if(log_df<4){
                df[*it] = 3;   
            }
            else{
                df[*it] = 4; 
            }
        }
    }
    // string term = "immigrants";
    // string stem = r.processTerm(term);

    // cout<<"df for "<<term<<" is "<<local.documentStemCount(term)<<endl;
    // cout<<"df for "<<stem<<" is "<<local.documentStemCount(stem)<<endl;
}


map<string, float>  compute_average_df(map<string, vector<string> >& queries,map<string, float>& df){
    map<string, float> average_df;
    for(map<string, vector<string> >:: iterator it=queries.begin(); it!=queries.end(); ++it){
        float query_average_df = .0;
        string qid = it->first;
        vector<string> query_words = it->second;
         // if (qid == "MB438"){
         //    cout<<"MB438:"<<endl;
         // }
        for(vector<string>::iterator wit = query_words.begin(); wit!=query_words.end(); ++wit){
            // if (qid == "MB438"){
            //     cout<<"\t"<<*wit<<":"<<df[*wit]<<endl;
            // }
            query_average_df += df[*wit];      

        }
        query_average_df /= query_words.size();
        average_df[qid] = query_average_df;
    }
    return average_df;

}

static void usage( indri::api::Parameters param ) {
  if( !param.exists( "query" ) || 
      !( param.exists( "index" ) )) {
   std::cerr << "get_average_df usage: " << std::endl
             << "   get_average_df -query=myquery -index=myindex" << std::endl;
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
        //string df_term  = argv[3];
        //float variance_threshold = atof(argv[4]);

        map<string, int> df;
        r.openRead( rep_name );
        map<string, vector<string> > queries;
        vector<string> query_words = get_unstemmed_query_words(r,query_file,queries);
        get_statistics(r,df,query_words);
        // output(df,dest_dir);


        for(map<string,int>:: iterator it=df.begin(); it!=df.end(); ++it){

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