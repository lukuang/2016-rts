/* Show query terms (debug purposes)
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


static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query") ) || 
      !( param.exists( "index") ) )  {
   std::cerr << "show_queries usage: " << std::endl
             << "   show_queries -query=myquery -index=myindex " << std::endl;
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
        

        map<string, int> stopwords = read_stopwords();
        map<string, vector<string> > queries;

        r.openRead( rep_name );
        vector<string> query_words = get_unstemmed_query_words(r,query_file,queries);
        
        for(map<string, vector<string> >::iterator it=queries.begin();it!=queries.end();++it){
            string qid = it->first;
            vector<string> terms = it->second;
            cout<<qid<<":";
            for(int i=0; i<terms.size();i++){
                cout<<" "<<terms[i];
            }
            cout<<endl;
        }

        
        r.close();
    } catch( lemur::api::Exception& e ) {
        LEMUR_ABORT(e);
    } catch( ... ) {
        std::cout << "Caught an unhandled exception" << std::endl;
    }
    return 0;
}