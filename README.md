BABOOZA - THE SOCIAL GRAPH ANALYZER

REQUIREMENTS: babooza.py and access.py files
TO RUN: just run "ipython babooza.py"

A) ABSTRACT:
Babooza is a simple tool to analyze Twitter's Social Networks.
The user can analyze any topic and Babooza will download the last 10.000 tweets
about that topic and discover how the users that have tweeted are connected
among themself returning. The results are returned as follows:

1)NODEs		[topic_results.csv]
2)IN_DEGREE 	[topic_results.csv]
3)OUT_DEGREE 	[topic_results.csv]
4)CLOSENESS 	[topic_results.csv]
5)BETWEENNESS 	[topic_results.csv]
6)PAGERANK	[topic_results.csv] 
7)CC 	 	[topic_results.csv]
8)A summary rank-plot of all of previous features 	[topic_plot.png]
9)Average Graph's CC and CC of three random-nodes 	[stdout] 
10)Number of connected components 			[stdout] 
11)k-core of the largest connected component 		[stdout] 

There are two built-in graphs, useful to get get a first approach with the 
program: 
1)Enron Graph (the email network generated by the Enron scandal).
2)Banca Etruria (FULL 10.000 nodes and 300k edges graph generated by the tweets
about Banca Etruria's Receivership).

B) HOW IT WORKS?
The program asks to the user which topic he would like to analyze.
If he choose a topic that is not included in the default option, the program
connects to TWITTER and downloads the latest 10.000 tweets about that topic
and store them on the cloud-base MongoDB instance Mongolab. After that
the program get the users' ids and downloads their followers and stores the edges
on Mongolab. Since TWITTER's rate limit, this operation could take quite long
(75.000 ids per 15 minutes)for this reason two utilities have been implemented
to make things slightly faster:

1)Multithreading: Babooza hacks TWITTER's rate limit problem
using multiple account (13) with a total of 39 access token (access.py).
For each token a thread is instantiated.
2)Stop-n-Go: each time the program processes an user, it stores its
id in a way that if some fatal error occurs, the program will be able 
to restart from where it stopped with no harm.

After that all the edges have been collected, Babooza build a Social Graph
and analyze it using the networkX lib. The results are reported as previously
written.

C) EXTRA
I have partially analyzed four topics (in addition to the full analysis of 
Enron and Banca Etruria) to look up any differences:
1)star wars (small)
2)donald trump (small)
3)world of warcraft (medium)
4)partito democratico (small)

Those analyis could easly restart from where I stopped thanks to the
"stop"-n-go feature.
