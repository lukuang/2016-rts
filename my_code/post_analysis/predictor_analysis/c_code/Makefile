## your application name here
AVGIDF= get_average_idf
CLARITY= show_clarity
## extra object files for your app here
OBJ=

prefix = /usa/lukuang/usr/indri/
exec_prefix = ${prefix}
libdir = ${exec_prefix}/lib
includedir = ${prefix}/include
INCPATH=-I$(includedir)
LIBPATH=-L$(libdir)
CXXFLAGS=-DPACKAGE_NAME=\"Indri\" -DPACKAGE_TARNAME=\"indri\" -DPACKAGE_VERSION=\"5.6\" -DPACKAGE_STRING=\"Indri\ 5.6\" -DPACKAGE_BUGREPORT=\"project@lemurproject.org\" -DYYTEXT_POINTER=1 -DINDRI_STANDALONE=1 -DHAVE_LIBM=1 -DHAVE_LIBPTHREAD=1 -DHAVE_LIBZ=1 -DHAVE_LIBIBERTY=1 -DHAVE_NAMESPACES= -DISNAN_IN_NAMESPACE_STD= -DHAVE_FSEEKO=1 -DSTDC_HEADERS=1 -DHAVE_SYS_TYPES_H=1 -DHAVE_SYS_STAT_H=1 -DHAVE_STDLIB_H=1 -DHAVE_STRING_H=1 -DHAVE_MEMORY_H=1 -DHAVE_STRINGS_H=1 -DHAVE_INTTYPES_H=1 -DHAVE_STDINT_H=1 -DHAVE_UNISTD_H=1 -DHAVE_EXT_ATOMICITY_H=1 -DP_NEEDS_GNU_CXX_NAMESPACE=1 -DHAVE_MKSTEMP=1 -DHAVE_MKSTEMPS=1 -DNDEBUG=1   -g -O3 $(INCPATH)
CPPLDFLAGS  =  -lindri -liberty -lz -lpthread -lm 

all: avgidf clarity

avgidf:
	$(CXX) $(CXXFLAGS) $(AVGIDF).cpp -o $(AVGIDF) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

clarity:
	$(CXX) $(CXXFLAGS) $(CLARITY).cpp -o $(CLARITY) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

# threshold:
# 	$(CXX) $(CXXFLAGS) $(THRESHOLD).cpp -o $(THRESHOLD) $(OBJ) $(LIBPATH) $(CPPLDFLAGS)

clean:
#	rm -f $(GET) $(THRESHOLD) $(SHOW)
	rm -f  $(AVGIDF) $(CLARITY)


