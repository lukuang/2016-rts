## your application name here
AVGIDF= get_average_idf
TERM_DF= get_term_df
CLARITY= show_clarity
SCQ= get_scq
VAR= get_var
UW_LOCAL_COHERENCE= get_unweighted_local_coherence
W_LOCAL_COHERENCE= get_weighted_local_coherence
GET_QUERY_LENGTH= get_query_length
GET_TERM_RELATEDNESS= get_term_relatedness
GET_WEIGHTED_TERM_RELATEDNESS = get_weighted_term_relatedness
GET_LOCAL_TERM_RELATEDNESS = get_local_term_relatedness
GET_MST_TERM_RELATEDNESS = get_mst_term_relatedness
GET_LINK_TERM_RELATEDNESS = get_link_term_relatedness
GET_COLLECTION_F2EXP_SCORE = get_collection_f2exp_score
GET_COLLECTION_SCORE = get_collection_score
GET_DOCUMENT_SCORE = get_document_scores
GET_WIG = get_wig
GET_PWIG = get_pwig
GET_CANDIDATE_SIZE=get_candidate_size
GET_FEEDBACK_QUERIES = get_qf_query
SHOW_QUERIES=show_queries
JURU=juru
## extra object files for your app here
OBJ=

prefix = /usa/lukuang/usr/indri/
exec_prefix = ${prefix}
libdir = ${exec_prefix}/lib
includedir = ${prefix}/include
INCPATH=-I$(includedir)
LIBPATH=-L$(libdir)
CXXFLAGS=-DPACKAGE_NAME=\"Indri\" -DPACKAGE_TARNAME=\"indri\" -DPACKAGE_VERSION=\"5.6\" -DPACKAGE_STRING=\"Indri\ 5.6\" -DPACKAGE_BUGREPORT=\"project@lemurproject.org\" -DYYTEXT_POINTER=1 -DINDRI_STANDALONE=1 -DHAVE_LIBM=1 -DHAVE_LIBPTHREAD=1 -DHAVE_LIBZ=1 -DHAVE_LIBIBERTY=1 -DHAVE_NAMESPACES= -DISNAN_IN_NAMESPACE_STD= -DHAVE_FSEEKO=1 -DSTDC_HEADERS=1 -DHAVE_SYS_TYPES_H=1 -DHAVE_SYS_STAT_H=1 -DHAVE_STDLIB_H=1 -DHAVE_STRING_H=1 -DHAVE_MEMORY_H=1 -DHAVE_STRINGS_H=1 -DHAVE_INTTYPES_H=1 -DHAVE_STDINT_H=1 -DHAVE_UNISTD_H=1 -DHAVE_EXT_ATOMICITY_H=1 -DP_NEEDS_GNU_CXX_NAMESPACE=1 -DHAVE_MKSTEMP=1 -DHAVE_MKSTEMPS=1 -DNDEBUG=1 -std=c++11  -g -O3 $(INCPATH)
CPPLDFLAGS  =  -lindri -liberty -lz -lpthread -lm 

all: feedback_query get_candidate_size scq var collection_f2exp uw_local_coherence w_local_coherence query_length avgidf clarity term_relatedness mst_term_relatedness link_term_relatedness wig pwig local_term_relatedness show_queries

get_candidate_size:
	$(CXX) $(CXXFLAGS) $(GET_CANDIDATE_SIZE).cpp -o $(GET_CANDIDATE_SIZE) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

avgidf:
	$(CXX) $(CXXFLAGS) $(AVGIDF).cpp -o $(AVGIDF) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

term_df:
	$(CXX) $(CXXFLAGS) $(TERM_DF).cpp -o $(TERM_DF) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)


clarity:
	$(CXX) $(CXXFLAGS) $(CLARITY).cpp -o $(CLARITY) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

scq:
	$(CXX) $(CXXFLAGS) $(SCQ).cpp -o $(SCQ) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

var:
	$(CXX) $(CXXFLAGS) $(VAR).cpp -o $(VAR) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

wig:
	$(CXX) $(CXXFLAGS) $(GET_WIG).cpp -o $(GET_WIG) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

pwig:
	$(CXX) $(CXXFLAGS) $(GET_PWIG).cpp -o $(GET_PWIG) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)


collection_f2exp:
	$(CXX) $(CXXFLAGS) $(GET_COLLECTION_F2EXP_SCORE).cpp -o $(GET_COLLECTION_F2EXP_SCORE) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

collection_score:
	$(CXX) $(CXXFLAGS) $(GET_COLLECTION_SCORE).cpp -o $(GET_COLLECTION_SCORE) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

docuemnt_score:
	$(CXX) $(CXXFLAGS) $(GET_DOCUMENT_SCORE).cpp -o $(GET_DOCUMENT_SCORE) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)


uw_local_coherence:
	$(CXX) $(CXXFLAGS) $(UW_LOCAL_COHERENCE).cpp -o $(UW_LOCAL_COHERENCE) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

w_local_coherence:
	$(CXX) $(CXXFLAGS) $(W_LOCAL_COHERENCE).cpp -o $(W_LOCAL_COHERENCE) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

query_length:
	$(CXX) $(CXXFLAGS) $(GET_QUERY_LENGTH).cpp -o $(GET_QUERY_LENGTH) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

term_relatedness:
	$(CXX) $(CXXFLAGS) $(GET_TERM_RELATEDNESS).cpp -o $(GET_TERM_RELATEDNESS) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

feedback_query:
	$(CXX) $(CXXFLAGS) $(GET_FEEDBACK_QUERIES).cpp -o $(GET_FEEDBACK_QUERIES) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)


weighted_term_relatedness:
	$(CXX) $(CXXFLAGS) $(GET_WEIGHTED_TERM_RELATEDNESS).cpp -o $(GET_WEIGHTED_TERM_RELATEDNESS) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)


local_term_relatedness:
	$(CXX) $(CXXFLAGS) $(GET_LOCAL_TERM_RELATEDNESS).cpp -o $(GET_LOCAL_TERM_RELATEDNESS) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)


mst_term_relatedness:
	$(CXX) $(CXXFLAGS) $(GET_MST_TERM_RELATEDNESS).cpp -o $(GET_MST_TERM_RELATEDNESS) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

link_term_relatedness:
	$(CXX) $(CXXFLAGS) $(GET_LINK_TERM_RELATEDNESS).cpp -o $(GET_LINK_TERM_RELATEDNESS) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

show_queries:
	$(CXX) $(CXXFLAGS) $(SHOW_QUERIES).cpp -o $(SHOW_QUERIES) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)


juru:
	$(CXX) $(CXXFLAGS) $(JURU).cpp -o $(JURU) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)


clean:
#	rm -f $(GET) $(THRESHOLD) $(SHOW)
	rm -f  $(GET_FEEDBACK_QUERIES) $(GET_CANDIDATE_SIZE) $(GET_LOCAL_TERM_RELATEDNESS) $(GET_PWIG) $(GET_WIG) $(VAR) $(SCQ) $(AVGIDF) $(CLARITY) $(UW_LOCAL_COHERENCE) $(W_LOCAL_COHERENCE) $(GET_QUERY_LENGTH) $(GET_TERM_RELATEDNESS) $(GET_MST_TERM_RELATEDNESS) $(GET_LINK_TERM_RELATEDNESS) $(GET_COLLECTION_F2EXP_SCORE)  $(TERM_DF) $(GET_WEIGHTED_TERM_RELATEDNESS) $(GET_DOCUMENT_SCORE) $(SHOW_QUERIES) $(JURU)

