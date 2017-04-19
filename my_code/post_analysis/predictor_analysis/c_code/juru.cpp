/* implement ranking function of Juru
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




template<typename A, typename B>
std::pair<B,A> flip_pair(const std::pair<A,B> &p)
{
    return std::pair<B,A>(p.second, p.first);
}

template<typename A, typename B>
std::multimap<B,A> flip_map(const std::map<A,B> &src)
{
    std::multimap<B,A> dst;
    std::transform(src.begin(), src.end(), std::inserter(dst, dst.begin()), 
                   flip_pair<A,B>);
    return dst;
}

lemur::api::DOCID_T  get_internal_did( indri::collection::Repository& r, const string& ex_docid ) {
  indri::collection::CompressedCollection* collection = r.collection();
  std::string attributeName = "docno";
  std::vector<lemur::api::DOCID_T> documentIDs;

  documentIDs = collection->retrieveIDByMetadatum( attributeName, ex_docid );

  return documentIDs[0];

}

float compute_h(const float& prob){
    float h = .0;
    if(prob != 1){
        h -= prob*log(prob);
        h -= (1-prob)*log(1-prob);
    }
    
    return h;
}

vector<int> get_docid_vector_for_term(indri::collection::Repository& r,const string& term){
    vector<int> docids;
    indri::server::LocalQueryServer local(r);
    indri::collection::Repository::index_state state = r.indexes();
    for( size_t i=0; i<state->size(); i++ ) {
        indri::index::Index* index = (*state)[i];
        indri::thread::ScopedLock( index->iteratorLock() );

        indri::index::DocListIterator* iter = index->docListIterator( term );
        if (iter == NULL) continue;

        iter->startIteration();

        int doc = 0;
        indri::index::DocListIterator::DocumentData* entry;

        for( iter->startIteration(); iter->finished() == false; iter->nextEntry() ) {
          entry = iter->currentEntry();

           docids.push_back(entry->document); 
        }

        delete iter;
    }
    return docids;
}

map<string, vector<int> >  get_docids(indri::collection::Repository& r,map<string, vector<string> >& queries){
    map<string, vector<int> > docids;
    for(map<string, vector<string> >::iterator it=queries.begin();it!=queries.end(); ++it){
       map<int, int> temp_docid_map;
       string qid = it->first;
       docids[qid] = vector<int>();
       for(int i=0;i<it->second.size();i++){
            string stem = it->second[i];
            vector<int> temp_docid_vector = get_docid_vector_for_term(r,stem);
            for(int j=0;j<temp_docid_vector.size();j++){
                int temp_internal_did = temp_docid_vector[j];
                if(temp_docid_map.find( temp_internal_did )==temp_docid_map.end()){
                    temp_docid_map[ temp_internal_did ] = 0;
                    docids[qid].push_back(temp_internal_did);
                }
            }
       } 
    }


    return docids;
}

string get_reversed_stem(indri::collection::Repository& r,const string & term){
    string reversed_term;
    if (term == r.processTerm(term) ){

        reversed_term = term;
    }
    else{
        reversed_term = term +"e";
        if (term != r.processTerm(reversed_term) ){
            reversed_term = term + "ing";
            if (term != r.processTerm(reversed_term) ){
                string end_chara = term.substr(term.size()-1);
                reversed_term = term + end_chara;
                if (term != r.processTerm(reversed_term) ){
                    cerr<<"Cannot find reversed_term for "<<term<<"!"<<endl;
                    return "";
                }
            }
        }
        // cout<<"reversed term for "<<term<<" is "<<reversed_term<<endl;
    }
    return reversed_term;
}



class Collection{
    public:
        map<string, int> df;
        map<string, float> idf;
        UINT64 N;
        float avdl;
        Collection(){

        }

        Collection(indri::collection::Repository& r,vector<string>& query_words){
            indri::server::LocalQueryServer local(r);

            UINT64 termCount = local.termCount();
            N = local.documentCount();
            avdl = termCount*1.0/N;

            for(vector<string>::iterator it = query_words.begin(); it!=query_words.end(); ++it){

                    df[*it] =  local.documentStemCount(*it);
                    if (df[*it]==0){
                        idf[*it] = .0;
                    }
                    else{
                        idf[*it] = log( N*1.0/df[*it] );
                    }
            }
            
        }

        void show(){
            for(map<string,float>::iterator it=idf.begin();it!=idf.end();++it){
               cout<<"Term: "<<it->first<<" "<<it->second<<endl; 
            }
        }
        
};  





class Document{

    public:
    string external_id;
    int internal_did;
    float average_tf;
    int dl;
    map<string,int> tf;
    int unique_term_size;
    float lengthNorm ;
    bool debug;
    Document(){

    }

    Document( const vector<string>& single_query_word,const Collection& collection, const bool debug){
        external_id = "IDEAL";
        internal_did = -1;
        dl = 0;
        dl = single_query_word.size();
        unique_term_size = dl;
        average_tf = 1;
        for(int i=0;i<dl;i++){
            tf[ single_query_word[i] ] = 1;
        }
        lengthNorm = 0.8*collection.avdl + 0.2*unique_term_size;
        lengthNorm = sqrt(lengthNorm);
        this->debug=debug;

    }

    Document(indri::collection::Repository& r,const int& internal_did,const Collection& collection,const vector<string>& single_query_word, const bool& debug){
        indri::server::LocalQueryServer local(r);
        dl = 0;
        this->debug=debug;
        std::vector<lemur::api::DOCID_T> documentIDs;
        documentIDs.push_back(internal_did);
        indri::server::QueryServerVectorsResponse* response = local.documentVectors( documentIDs );

        map<string, int>  temp_word_map;
        map<string, int>  unique_term_map ;
        for(int k=0;k<single_query_word.size();k++){
            temp_word_map[ single_query_word[k] ] = 0;
        }

        if( response->getResults().size() ) {
            indri::api::DocumentVector* docVector = response->getResults()[0];

            for( size_t i=0; i<docVector->positions().size(); i++ ) {
              int position = docVector->positions()[i];
              const std::string& stem = docVector->stems()[position];

              if (temp_word_map.find(stem)!=temp_word_map.end()){
                  if(tf.find(stem)==tf.end()){
                    tf[stem] = 0;
                  }
                  tf[stem] += 1;
              }
              if(unique_term_map.find(stem)==unique_term_map.end()){
                    unique_term_map[stem] = 0;
                }
              
              dl += 1;
            }
            delete docVector;
        }

        delete response;

        unique_term_size = unique_term_map.size();
        average_tf = dl*1.0/unique_term_size;
        // if (this->debug) cout<<"document "<<internal_did<<" unique_term_size: "<<unique_term_size<<" dl "<<dl<<endl;
        this->internal_did = internal_did;

        indri::collection::CompressedCollection* indri_collection = r.collection();
        external_id = indri_collection->retrieveMetadatum( internal_did, "docno" );

        lengthNorm = 0.8*collection.avdl + 0.2*unique_term_size;
        lengthNorm = sqrt(lengthNorm);
    }



    float compute_document_score(const vector<string>& single_query_word, Collection& collection){
        float document_score = .0;
        for(int j=0;j<single_query_word.size();j++){
            string single_term = single_query_word[j];
            if( (collection.idf.find(single_term) == collection.idf.end() ) ||
                (this->tf.find(single_term) == this->tf.end()           ) ){
                
                document_score += .0;
            }
            else{
                float tfNorm = log(1+this->tf[ single_term ]) / log(1+this->average_tf);
                document_score += tfNorm*collection.idf[ single_term ];

            }
            if (this->debug) {
                if(internal_did == 462230|| internal_did == -1){
                    cout<<"\tscore: "<<document_score<<" term: "<<single_term;
                    cout<<" tf: "<<this->tf[ single_term ]<<" avg_tf "<<this->average_tf;
                    cout<<" idf "<<collection.idf[ single_term ]<<endl;

                }
            }

        }
        document_score /= lengthNorm;
        if (this->debug) {
            if(internal_did == 462230 || internal_did == -1){
                cout<<"did: "<<this->external_id;
                cout<<" dl: "<<this->dl;
                cout<<" avdl: "<<collection.avdl;
                cout<<" lengthNorm: "<<this->lengthNorm;
                cout<<" final doc score: "<<document_score<<endl;
                // exit(-1);
            }
        }
        return document_score;
    }

};

class LACollection{
    public:
        map<string, int> df;
        map<string, float> idf;
        UINT64 N;
        float avdl;
        LACollection(){

        }

        LACollection(const Collection& collection){

            N = collection.N;
            avdl = collection.avdl;
            
        }

        void update_idf(const string& la_string, const float la_df){
            df[la_string] = la_df;
            idf[la_string] = log( N*1.0/la_df );
        }

        void show(){
            for(map<string,float>::iterator it=idf.begin();it!=idf.end();++it){
               cout<<"Term: "<<it->first<<" "<<it->second<<endl; 
            }
        }
        
};  



class LADocument{

    public:
    string external_id;
    int internal_did;
    float average_tf;
    int dl;
    map<string,int> tf;
    int unique_term_size;
    float lengthNorm;
    bool debug;
    LADocument(){

    }


    LADocument(indri::collection::Repository& r,const int& internal_did,const Collection& collection, const bool& debug){
        indri::server::LocalQueryServer local(r);

        this->debug=debug;
        dl = 0;
        std::vector<lemur::api::DOCID_T> documentIDs;
        documentIDs.push_back(internal_did);
        indri::server::QueryServerVectorsResponse* response = local.documentVectors( documentIDs );

        map<string, int>  unique_term_map ;


        if( response->getResults().size() ) {
            indri::api::DocumentVector* docVector = response->getResults()[0];

            for( size_t i=0; i<docVector->positions().size(); i++ ) {
              int position = docVector->positions()[i];
              const std::string& stem = docVector->stems()[position];

              
              if(unique_term_map.find(stem)==unique_term_map.end()){
                    unique_term_map[stem] = 0;
                }
              
              dl += 1;
            }
            delete docVector;
        }

        delete response;

        unique_term_size = unique_term_map.size();
        average_tf = dl*1.0/unique_term_size;
        // if (this->debug) cout<<"document "<<internal_did<<" unique_term_size: "<<unique_term_size<<" dl "<<dl<<endl;
        this->internal_did = internal_did;

        indri::collection::CompressedCollection* indri_collection = r.collection();
        external_id = indri_collection->retrieveMetadatum( internal_did, "docno" );

        lengthNorm = 0.8*collection.avdl + 0.2*unique_term_size;
        lengthNorm = sqrt(lengthNorm);
    }

    void update_tf(const string& la_string, const float la_tf){
        tf[la_string] = la_tf;
    }

    // void increase_tf(const string& la_string, const float la_tf){
    //     if(tf.find(la_string)==tf.end()){
    //         this->update_tf(la_string,la_tf);
    //     }
    //     else{
    //         tf[la_string] += la_tf;
    //     }
    // }

    float compute_document_score(const vector<string>& single_query_word, LACollection& la_collection){
        float document_score = .0;
        for(int j=0;j<single_query_word.size();j++){
            string single_term = single_query_word[j];
            if( (la_collection.idf.find(single_term) == la_collection.idf.end() ) ||
                (this->tf.find(single_term) == this->tf.end()           ) ){
                
                document_score += .0;
            }
            else{
                float tfNorm = log(1+this->tf[ single_term ]) / log(1+this->average_tf);
                document_score += tfNorm*la_collection.idf[ single_term ];

            }
            if (this->debug) {
                if(internal_did == 100359){
                    cout<<"\tscore: "<<document_score<<" term: "<<single_term;
                    cout<<" tf: "<<this->tf[ single_term ]<<" avg_tf "<<this->average_tf;
                    cout<<" idf "<<la_collection.idf[ single_term ]<<endl;

                }
            }

        }
        document_score /= lengthNorm;
        if (this->debug) {
            if(internal_did == 100359){
                cout<<"did: "<<this->external_id;
                cout<<" dl: "<<this->dl;
                cout<<" lengthNorm: "<<this->lengthNorm;
                cout<<" final doc score: "<<document_score<<endl;
                // exit(-1);
            }
        }
        return document_score;
    }
};
 
class LAPostingList{
    private:
        map<string,LADocument> documents;
        string qid;
        bool debug;
    public:
        map<string,int> df;

        map<string, float> scores;
        LAPostingList(){

        }

        LAPostingList(const string& qid,const bool& debug){
            this->qid = qid;
            this->debug = debug;
        }

        void add_document(LADocument single_la_document){
            string external_id = single_la_document.external_id;
            if(documents.find(external_id) == documents.end()){
                documents[external_id] = single_la_document;
            }
            else{
                for(map<string,int>::iterator tit=single_la_document.tf.begin();tit!=single_la_document.tf.end();++tit){
                    documents[external_id].update_tf(tit->first,tit->second);
                }
            }
        }

        void compute_score(const vector<string>& la_vector, LACollection& la_collection){
            for(map<string,LADocument>::iterator it=documents.begin();it!=documents.end();++it){
                string external_id = it->first;
                float score_now = it->second.compute_document_score(la_vector,la_collection);
                // if (this->debug) cout<<"Score for did "<<external_id<<"is:"<<endl;
                scores[ external_id ] = score_now;
                
            }

            for(int i=0;i<la_vector.size();i++){
                string single_la = la_vector[i];
                this->df[single_la] = la_collection.df[single_la];
            }
        }

};

class PostingList{
    private:
        vector<Document> documents;
        string qid;
        bool debug;
        float max_doc_score;
    public:
        map<string, float> scores;
        PostingList(){
            max_doc_score = .0;
        }

        PostingList(indri::collection::Repository& r, vector<int> & query_internal_dids,const string& qid, Collection collection, const vector<string>& single_query_word,const bool& debug){
            for(int i=0;i<query_internal_dids.size();i++){
                int internal_did = query_internal_dids[i];
                documents.push_back( Document(r,internal_did,collection,single_query_word,debug) ); 
            }
            this->qid = qid;
            this->debug = debug;
            max_doc_score = .0;
        }

        void compute_score(const vector<string>& single_query_word, Collection& collection){
            for(int i=0;i<documents.size();i++){
                string external_id = documents[i].external_id;
                // if (this->debug) cout<<"Score for did "<<external_id<<"is:"<<endl;
                float score_now = documents[i].compute_document_score(single_query_word,collection);
                scores[ external_id ] = score_now;
                if(max_doc_score<score_now){
                    max_doc_score = score_now;
                }
            }
        }

        void print_result(const int& result_size){
            std::multimap<float, string> dst = flip_map(scores);

            int count = 0;
            for(map <float, string>::reverse_iterator dit=dst.rbegin();dit!=dst.rend();++dit){
                cout<<qid<<" Q0 "<< dit->second<<" "<<(count+1)<<" "<<dit->first<<" Juru"<<endl;
                count++;
                if (count >= result_size) break;
            }
        }

        void update_candidate_las(indri::collection::Repository& r, map<string, map<string,int> >& candidate_map,const string& external_id,const map <string,int>& stopwords){
              indri::server::LocalQueryServer local(r);
              if (this->debug) cout<<"process "<<external_id<<endl;
              lemur::api::DOCID_T documentID = get_internal_did( r,external_id );

              std::vector<lemur::api::DOCID_T> documentIDs;
              documentIDs.push_back(documentID);

              indri::server::QueryServerVectorsResponse* response = local.documentVectors( documentIDs );
              
              map<string, vector<int> > stem_index;
              vector<string> index_stem;

              if( response->getResults().size() ) {
                indri::api::DocumentVector* docVector = response->getResults()[0];
              
                


                for( size_t i=0; i<docVector->positions().size(); i++ ) {
                      int position = docVector->positions()[i];
                      const std::string& stem = docVector->stems()[position];
                      if (stem_index.find(stem)==stem_index.end()){
                          stem_index[stem] = vector<int>();
                        }
                      stem_index[stem].push_back(i);
                      index_stem.push_back(stem);
                }

                delete docVector;
              }

              delete response;

              for(map<string, map<string,int> >::iterator it=candidate_map.begin();it!=candidate_map.end();++it){
                string query_stem = it->first;
                for(int j=0;j<stem_index[query_stem].size();j++){
                    int index_of_stem = stem_index[query_stem][j];
                    for(int m=index_of_stem+1;(m-index_of_stem<=5 && m<index_stem.size() );m++){
                        string candidate_stem = index_stem[m];
                        if (candidate_stem=="[OOV]"){
                            continue;
                        }
                        if(stopwords.find(candidate_stem) != stopwords.end()){
                            continue;
                        }
                        else if (candidate_map.find(candidate_stem)==candidate_map.end()){
                            //make sure the candidate is not a query term
                            candidate_map[query_stem][candidate_stem] = 0;
                             // if (this->debug) cout<<"\tadd term "<< candidate_stem<<endl;
                        }
                    }
                    for(int n=index_of_stem-1;(index_of_stem-n<=5 && n>=0 );n--){
                        string candidate_stem = index_stem[n];
                        if (candidate_stem=="[OOV]"){
                            continue;
                        }
                        if(stopwords.find(candidate_stem) != stopwords.end()){
                            continue;
                        }
                        else if (candidate_map.find(candidate_stem)==candidate_map.end()){
                            //make sure the candidate is not a query term
                            candidate_map[query_stem][candidate_stem] = 0;

                        }
                    }

                }
              }
        }

       vector<string> get_candidate_las(indri::collection::Repository& r,const vector<string>& single_query_word){
            std::multimap<float, string> dst = flip_map(scores);
            map<string, map<string,int> > candidate_map;
            for(int k=0;k<single_query_word.size();k++){
                candidate_map[ single_query_word[k] ] = map<string,int>();
            }

            map <string,int> stopwords = read_stopwords(r);
            int count = 0;
            for(map <float, string>::reverse_iterator dit=dst.rbegin();dit!=dst.rend();++dit){
                string external_id = dit->second;
                this->update_candidate_las(r,candidate_map,external_id,stopwords);
                count++;
                if (count >= 10) break;
            }
            // if (this->debug){
            vector<string> candidate_las;
            for(map<string, map<string,int> >::iterator it=candidate_map.begin();it!=candidate_map.end();++it){
                string query_stem = it->first;
                for(map<string,int>::iterator sit=it->second.begin();sit!=it->second.end();++sit){
                    string query_term_reverse = get_reversed_stem(r,query_stem);
                    string other_term_reverse = get_reversed_stem(r,sit->first);
                    if (query_term_reverse.length()==0 || other_term_reverse.length() == 0){
                        if (this->debug) cout<<"one of the terms cannot be reversed: "<<query_term_reverse<<" "<<other_term_reverse<<endl;
                        continue;
                    }
                    else{
                        string single_cnadidate = query_term_reverse+" "+ other_term_reverse;
                        // if (this->debug) cout<<"candidate la: "<<single_cnadidate<<endl;
                        candidate_las.push_back(single_cnadidate);  
                    }
                    
                }
                
            }
            // }
            if (this->debug) cout<<"Found "<<candidate_las.size()<<" candidate las"<<endl;

            // return candidate_las;
            return candidate_las;

        }

        map<string,LAPostingList> get_la(const std::string& indexName,indri::collection::Repository& r,const vector<string>& single_query_word, Collection& collection){
            vector<string> top_las;
            
            // get probability for documents
            if(this->debug) cout<<"generate ideal document"<<endl;
            Document ideal_document = Document(single_query_word,collection,this->debug);
            float max_score = ideal_document.compute_document_score(single_query_word,collection);
            max_score = max(max_score,this->max_doc_score);
            if(this->debug) cout<<"max score: "<<max_score<<endl;
            map<string,float> prob ;
            for(map<string,float>::iterator sit=scores.begin();sit!=scores.end();++sit){

                prob[sit->first] = sit->second / max_score;
            }
            if(this->debug) cout<<"got probability "<<endl;



            vector<string> candidate_las = this->get_candidate_las(r,single_query_word);            
            map<string, map<string,LADocument> > la_documents;
            LACollection la_collection = LACollection(collection);

            map<string,float> candidate_ig;

            for(int i=0;i<candidate_las.size();i++){
                string single_cnadidate = candidate_las[i];
                if(this->debug) cout<<"For "<<single_cnadidate<<endl;
                la_documents[single_cnadidate] = map<string,LADocument>();
                string indri_expression="#uw6( " + single_cnadidate +" )";
                
                // get expression df
                indri::api::QueryEnvironment env;

                env.addIndex( indexName );
                int expression_df = env.documentExpressionCount( indri_expression );
                
                la_collection.update_idf(single_cnadidate,expression_df);
                // if(this->debug) cout<<"got df"<<endl;
                // get expression tf
               
                vector<indri::api::ScoredExtentResult> result = env.expressionList( indri_expression );
                env.close();
                map<int,int> expression_doc_tf;
                for( size_t j=0; j<result.size(); j++ ) {
                    int internal_did = result[j].document;
                    if (expression_doc_tf.find(internal_did)==expression_doc_tf.end() ){
                        expression_doc_tf[internal_did] = 0;
                    }
                    expression_doc_tf[internal_did] += result[j].score;
                }
                // if(this->debug) cout<<"got tf"<<endl;
                for(map<int,int>::iterator eit=expression_doc_tf.begin();eit!=expression_doc_tf.end();++eit){
                    int internal_did = eit->first;
                    int expression_tf = eit->second;
                    LADocument single_la_document = LADocument(r,internal_did,collection, this->debug);
                    single_la_document.update_tf(single_cnadidate,expression_tf);
                    string external_id = single_la_document.external_id;
                    la_documents[single_cnadidate][external_id] = single_la_document;

                }

                int include_size = 0;
                int exclude_size = 0;
                float include_prob = .0;
                float exclude_prob = .0;
                float all_prob = .0;
                for(int j=0;j<this->documents.size();j++){
                    string external_id = this->documents[j].external_id;
                    all_prob += prob[external_id];
                    if (la_documents[single_cnadidate].find(external_id)==la_documents[single_cnadidate].end()){
                        exclude_size += 1; 
                        exclude_prob += prob[external_id];
                    }
                    else{
                        include_size += 1; 
                        include_prob += prob[external_id];
                    }
                }
                all_prob /= 1.0*(include_size+exclude_size);
                include_prob /= 1.0*(include_size);
                exclude_prob /= 1.0*(exclude_size);
                float h_all = compute_h(all_prob);
                float h_include = compute_h(include_prob);
                float h_exclude = compute_h(exclude_prob);
                candidate_ig[single_cnadidate] = h_all ;
                candidate_ig[single_cnadidate] -= (include_size*h_include)/(include_size+exclude_size);
                candidate_ig[single_cnadidate] -= (exclude_size*h_exclude)/(include_size+exclude_size);
                if (this->debug) cout<<"ig score: "<< candidate_ig[single_cnadidate]<<endl;
                
            }

            if (this->debug) cout<<"got candidate ig scores"<<endl;
            LAPostingList la_posting_list = LAPostingList(this->qid,this->debug);
            map<string,LAPostingList> individual_posting;
            std::multimap<float, string> dst = flip_map(candidate_ig);
            int count = 0;
            for(map <float, string>::reverse_iterator dit=dst.rbegin();dit!=dst.rend();++dit){
                string single_la = dit->second;
                top_las.push_back(dit->second);

                map<string,LADocument> documents_for_single_la = la_documents[single_la];
                individual_posting[single_la] = LAPostingList(this->qid,this->debug);
                for(map<string,LADocument>::iterator lait=documents_for_single_la.begin();lait!=documents_for_single_la.end();++lait){
                    la_posting_list.add_document(lait->second);
                    individual_posting[single_la].add_document(lait->second);
                }
                count++;
                if (count >= 2) break;
            }
            la_posting_list.compute_score(top_las,la_collection);
            for(map<string,float>::iterator sit=this->scores.begin();sit!=this->scores.end();++sit){
                string external_id = sit->first;
                this->scores[external_id] = 0.75*sit->second;
                if(la_posting_list.scores.find(external_id)!=la_posting_list.scores.end() ){
                    this->scores[external_id] += 0.25*la_posting_list.scores[external_id];
                }
            }

            for(int j=0;j<top_las.size();j++){
                string single_la = top_las[j];
                vector<string> temp_la_vector ;
                temp_la_vector.push_back(single_la);
                individual_posting[single_la].compute_score(temp_la_vector,la_collection);
            }

            return individual_posting;
        }



};



void write_la(map<string, map<string,LAPostingList> >& query_las, char* la_file){
    ofstream la_file_stream;
    la_file_stream.open(la_file);
    for(map<string, map<string,LAPostingList> >::iterator it=query_las.begin();it!=query_las.end();++it){
        string qid = it->first;
        for(map<string,LAPostingList>::iterator t_it=query_las[qid].begin(); t_it!=query_las[qid].end();++t_it){
            string single_la = t_it->first;
            la_file_stream<<qid<<":"<<single_la<<":"<<t_it->second.df[single_la]<<":";
            map<string, float> single_scores = t_it->second.scores;
            std::multimap<float, string> dst = flip_map(single_scores);

            int count = 0;
            for(map <float, string>::reverse_iterator dit=dst.rbegin();dit!=dst.rend();++dit){
                la_file_stream<<dit->second<<",";
                count++;
                if (count >= 10) break;
            }
            la_file_stream<<"\n";
        }

    }
    la_file_stream.close();
}


static void usage( indri::api::Parameters param ) {
  if( !( param.exists( "query" ) || param.exists( "term" )) || 
      !( param.exists( "index" ) ) ) {
   std::cerr << "juru usage: " << std::endl
             << "   juru -query=myquery -index=myindex OR" << std::endl;
    std::cerr << "   juru -term=myquery -index=myindex OR" << std::endl;
   exit(-1);
  }
}


int main(int argc, char** argv){
    indri::collection::Repository r;
    try {
        indri::api::Parameters& param = indri::api::Parameters::instance();
        param.loadCommandLine( argc, argv );
        usage( param );
        
        string rep_name = param[ "index" ];
        bool debug = false;
        if (param.exists( "debug" )){
            debug = true;
        }

        

        

        //int percent_threshold = atoi(argv[2]);
        //string df_term  = argv[3];
        //float variance_threshold = atof(argv[4]);
        int result_size = param.get("result_size",1000);

        r.openRead( rep_name );
        map<string, vector<string> > queries;
        map<string, map<string,LAPostingList> > query_las;
        vector<string> query_words;

        bool use_la = false;
        bool use_la_file = false;
        char* la_file;
        if( param.exists( "query" )){
            std::string query_file_string = param[ "query" ];
            char* query_file = new char[query_file_string.length()+1];
            memcpy(query_file, query_file_string.c_str(), query_file_string.length()+1);
            if( param.exists( "required_qid" ) ){
                string required_qid = param["required_qid"];
                query_words = get_query_words(r,query_file,queries,required_qid);
                if (param.exists( "use_la" )){
                    use_la = true;
                    if(param.exists( "la_dir" )){
                        use_la_file = true;
                        string la_file_string = param[ "la_dir" ];
                        la_file_string += "/"+required_qid;
                        if(debug) cout<<"The file is "<<la_file_string<<endl;
                        la_file = new char[la_file_string.length()+1];
                        memcpy(la_file, la_file_string.c_str(), la_file_string.length()+1);
                        // if(debug) printf("FILE %s\n", la_file);
                    }
                    
                }
            }
            else{
                query_words = get_query_words(r,query_file,queries);

            }
        }
        else if( param.exists( "term" ) ){
            use_la = true;
            result_size = 10;
            std::string term = param[ "term" ];
            map<string, int> stopwords = read_stopwords(r);
            string term_stem = r.processTerm(term);
            if(stopwords.find(term_stem)==stopwords.end()){
                query_words.push_back(term_stem);
                std::vector<string> query_vector = query_words;
                queries[term] = query_vector;
            }
            else{
                exit(0);
            }
        }


        Collection collection= Collection(r,query_words);
        if (debug) {
            cout<<"Got collection stats"<<endl;
            // collection.show();
        }
        map<string, vector<int> >docids =   get_docids(r,queries);
        if (debug) cout<<"Got internal docids"<<endl;
        for(map<string, vector<int> >::iterator it=docids.begin();it!=docids.end();it++){
            string qid = it->first;
            if (debug) cout<<"compute score for query "<<qid<<endl;
            PostingList *single_posting_list = new PostingList(r,it->second,qid, collection,queries[qid],debug);
            if (debug) cout<<"got posting_lists"<<endl;
            single_posting_list->compute_score(queries[qid], collection);
            if(use_la){
                query_las[qid] = single_posting_list->get_la(rep_name,r,queries[qid], collection);
                if(debug){
                    for(map<string,LAPostingList>::iterator t_it=query_las[qid].begin(); t_it!=query_las[qid].end();++t_it){
                        cout<<"find top la "<<t_it->first<<endl;
                    } 
                }
            }
            single_posting_list->print_result(result_size);
            delete single_posting_list;

        }
        if(use_la_file){
            if(debug) printf("write to file %s\n",la_file);
            write_la(query_las,la_file);
        }
        else{
            if(debug) cout<<"USE LA FILE TURN TO FALSE!"<<endl;
        }


        r.close();
    } catch( lemur::api::Exception& e ) {
        LEMUR_ABORT(e);
    } catch( ... ) {
        std::cout << "Caught an unhandled exception" << std::endl;
    }
    return 0;
}