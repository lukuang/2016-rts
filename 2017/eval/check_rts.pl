#!/usr/bin/perl -w

use strict;

# Check a TREC 2017 Real Time Summarization track, Scenario B
# submission for various common errors:
#      * extra fields
#      * multiple run tags
#      * unknown topics (missing topics allowed, since retrieving no docs
#        for a topic is a valid repsonse)
#      * invalid retrieved documents (approximate check)
#      * duplicate retrieved documents in a single topic
#      * too many documents retrieved for a topic
# Messages regarding submission are printed to an error log

# Results input file for Scenario B is of the form
#     YYYYMMDD topic-id Q0 tweet-id rank score tag

# For Scenario B, enforce at most 100 Tweets per day per topic.  This check
# uses the YYYMMDD given in the run.  Note that this does not check that
# the Tweet actually occurred on that date.  That is beyond the scope of the
# check script.  Also, we accept dates of 6 Aug since the date is the
# decision date and perhaps the decision was delayed past midnight of the
# final day in the evaluation period.
#

# Change these variable values to the directory in which the error log
# should be put
my $errlog_dir = ".";

# If more than 25 errors, then stop processing; something drastically
# wrong with the file.
my $MAX_ERRORS = 25; 

my $MAX_RET = 100;		# maximum number of docs to retrieve per day

my @topics;

my %docnos;                     # hash of retrieved docnos
my (%numret,%daycounts);	# number of docs retrieved per topic (per day)
my ($results_file);		# input file to be checked; it is an
				# 	input argument to the script
my $line;			# current input line
my $line_num;			# current input line number
my $errlog;			# file name of error log
my $num_errors;			# flags for errors detected
my $topic;
my ($docno,$q0,$sim,$rank,$tag,$date,$time);
my $q0warn = 0;
my $run_id;
my ($i);

my $usage = "Usage: $0 resultsfile\n";
$#ARGV == 0 || die $usage;
$results_file = $ARGV[0];

open RESULTS, "<$results_file" ||
	die "Unable to open results file $results_file: $!\n";

my @path = split "/", $results_file;
my $base = pop @path;
$errlog = $errlog_dir . "/" . $base . ".errlog";
open ERRLOG, ">$errlog" ||
	die "Cannot open error log for writing\n";

@topics = (46..233);
foreach $topic (@topics) {
    $numret{"RTS$topic"} = 0;
    for ($i=29; $i<=31; $i++) {
 	$date = "201707$i";
        $daycounts{$topic}{$date} = 0;
    }
    for ($i=1; $i<=6; $i++) {
 	$date = "2017080$i";
        $daycounts{$topic}{$date} = 0;
    }
}

$num_errors = 0;
$line_num = 0;
$run_id = "";
while ($line = <RESULTS>) {
    chomp $line;
    next if ($line =~ /^\s*$/);

    undef $tag;
    my @fields = split " ", $line;
    $line_num++;
	
    if (scalar(@fields) == 7) {
       ($date,$topic,$q0,$docno,$rank,$sim,$tag) = @fields;
    } else {
       &error("Wrong number of fields (expecting 7)");
       exit 255;
    }

    # make sure runtag is ok
    if (! $run_id) { 	# first line --- remember tag 
	$run_id = $tag;
	if ($run_id !~ /^[A-Za-z0-9_.-]{1,15}$/) {
	    &error("Run tag `$run_id' is malformed");
	    next;
	}
    }
    else {			# otherwise just make sure one tag used
	if ($tag ne $run_id) {
	    &error("Run tag inconsistent (`$tag' and `$run_id')");
	    next;
	}
    }

    # make sure topic is known
    if (!exists($numret{$topic})) {
	&error("Unknown topic '$topic'");
	$topic = 0;
	next;
    }  
    

    # make sure DOCNO known and not duplicated
    if ($docno =~ /^[0-9]{18}$/) {   # valid DOCNO to the extent we will check
	if (exists $docnos{$docno} && $docnos{$docno} eq $topic) {
	    &error("Document `$docno' retrieved more than once for topic $topic");
	    next;
	}
	$docnos{$docno} = $topic;
    }
    else {				# invalid DOCNO
	&error("Unknown document `$docno'");
	next;
    }

    if ($q0 ne "Q0" && ! $q0warn) {
        $q0warn = 1;
        &error("Field 3 is `$q0' not `Q0'");
    }

    # remove leading 0's from rank (but keep final 0!)
    $rank =~ s/^0*//;
    if (! $rank) {
        $rank = "0";
    }

    # date has to be in correct format and refer to a date within
    # the evaluation period.
    my ($year,$month,$day);
    if ($date !~ /(\d\d\d\d)(\d\d)(\d\d)/) {
	&error("Date string $date not in correct format of YYYYMMDD");
	next;
    }
    $year = $1; $month = $2; $day = $3;
    if ($year ne "2017") {
	&error("Date $date has year $year, not 2017");
	next;
    }
    if ($month eq "07" ) {
	if ($day < 29 || $day > 31) {
 	    &error("July date $date has day $day (must be between 29--31)");
	    next;
	}
    }
    elsif ($month eq "08") {
        if ($day < 1 || $day > 6) {
	    &error("August date $date has day $day (must be between 1--6)");
	    next;
	}
    }
    else {
	&error("Date $date has month $month, not  07 or 08");
	next;
    }

    $daycounts{$topic}{$date}++;
}


# Do global checks:
#   error if some topic has too many documents retrieved
foreach $topic (@topics) { 
    for ($i=29; $i<=31; $i++) {
	$date = sprintf "201707%02d", $i;
	if ($daycounts{$topic}{$date} > $MAX_RET) {
            &error("Too many documents ($daycounts{$topic}{$date}) retrieved for day $date for topic $topic");
	}
    }
    for ($i=1; $i<=6; $i++) {
	$date = sprintf "201708%02d", $i;
	if ($daycounts{$topic}{$date} > $MAX_RET) {
            &error("Too many documents ($daycounts{$topic}{$date}) retrieved for day $date for topic $topic");
	}
    }
}
print ERRLOG "Finished processing $results_file\n";
close ERRLOG || die "Close failed for error log $errlog: $!\n";

if ($num_errors) { exit 255; }
exit 0;


# print error message, keeping track of total number of errors
sub error {
   my $msg_string = pop(@_);

    print ERRLOG 
    "run $results_file: Error on line $line_num --- $msg_string\n";

    $num_errors++;
    if ($num_errors > $MAX_ERRORS) {
        print ERRLOG "$0 of $results_file: Quit. Too many errors!\n";
        close ERRLOG ||
		die "Close failed for error log $errlog: $!\n";
	exit 255;
    }
}
