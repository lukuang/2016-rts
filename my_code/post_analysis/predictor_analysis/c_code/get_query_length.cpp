/* get query length after stopwords removal
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
  if( !( param.exists( "query" ) ) || 
      !( param.exists( "index" ) )   ) {
   std::cerr << "get_query_length usage: " << std::endl
             << "   get_query_length -query=myQuery -index=myIndex" << std::endl;
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

        r.openRead( rep_name );

        //int percent_threshold = atoi(argv[2]);
        //string idf_term  = argv[3];
        //float variance_threshold = atof(argv[4]);

        map<string, vector<string> > queries;

        vector<string> query_words = get_query_words(r,query_file,queries);
        
        for(map<string, vector<string> >::iterator it=queries.begin();it!=queries.end();++it){
            cout<<it->first<<" "<<it->second.size()<<endl;
        }

        
    } catch( lemur::api::Exception& e ) {
        LEMUR_ABORT(e);
    } catch( ... ) {
        std::cout << "Caught an unhandled exception" << std::endl;
    }
    return 0;
}