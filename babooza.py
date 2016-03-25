# -*- coding: utf-8 -*-
"""
Created on Sat Dec 12 15:43:43 2015

@author: aalto
"""
from access import getTokens
import networkx as nx
import pymongo
import tweepy
import time
from tweepy import OAuthHandler
import threading
import matplotlib.pyplot as plt
from random import choice
import numpy as np
import os.path

MONGODB_URI = "mongodb://aalto:ciaobello@ds057944.mongolab.com:57944/aalto"

database = "aalto"
collection = "Tweets"
api = None
    
def getApi(cfg):
    auth = OAuthHandler(cfg["consumer_key"], cfg["consumer_secret"])
    auth.set_access_token(cfg["access_token"], cfg["access_token_secret"])
    api = tweepy.API(auth)
    return api

def limit_handled(cursor, user):
    over = False
    while True:
        try:
            if (over == True):
                print "Routine Riattivata, Serviamo il numero:", user
                over = False
            yield cursor.next()
        except tweepy.RateLimitError:
            print "Raggiunto Limite, ", threading.current_thread(), " in Pausa"
            dummy_event = threading.Event()
            dummy_event.wait(timeout=15*60 + 15)
            over = True
        except tweepy.TweepError as ex:
            #print "TweepError of ", threading.current_thread()
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print message, user, threading.current_thread()
            if ex.reason == "Not authorized":
                print "User, ",user," doesn't allow to look up to his follower list."
                break
            dummy_event = threading.Event()
            dummy_event.wait(timeout=60)
            
def getMDBCollection(collection):
    client = pymongo.MongoClient(MONGODB_URI)
    db = client[database]
    return db[collection.replace(" ", "")]
    
def storeTweets(cfg):
    api = getApi(cfg)
    print "Connected to Twitter"
    tweets_collection = getMDBCollection(topic+"_tweets")
    print "New collection ", topic.replace(" ", "") + "_tweets created"
    for tweetsPag in limit_handled(tweepy.Cursor(api.search, q=topic, count=100).pages(100), 0):
        tweets_collection.insert_many([{str((tweet.user).id):tweet.text} for tweet in tweetsPag])
    print "Tweets uploaded to MDB"
        
def getIDsFromMDB():
    tweets_collection = getMDBCollection(topic+"_tweets")
    ids = []
    for doc in tweets_collection.find():
        ids.append(sorted((doc.keys()))[0])
    return list(set(ids))
    
def storeFollowersOnMDB2(api):
    global ids
    global counter
    global processedUsers
    edges_collection= getMDBCollection(topic + "_edges")
    while counter < len(ids):
        user = ids[counter]
        counter += 1 
        print "Processing user:", user
        for followersPag in limit_handled(tweepy.Cursor(api.followers_ids, id = user, count=5000).pages(), user):
            toAdd = [{user : str(follower)} for follower in followersPag if str(follower) in ids]
            if toAdd:
                edges_collection.insert_many(toAdd) 
        processedUsers.append(int(user))
        saveProcessedUsers()
        print "User ", user, " processed, processed users: ", len(processedUsers)
    print threading.current_thread(), "have done!"
    
def saveProcessedUsers():
    global semaphore
    if semaphore == 1:
        semaphore=0
        np.array(processedUsers).dump(topic.replace(" ","")+"_processedUsers.data")
        semaphore=1
        
def work(cfg):
    api = getApi(cfg)
    storeFollowersOnMDB2(api) 
        
def getFollowers(cfgL):
    threads = []
    print "Starting 39 threads..."
    for k in range(39):
        t = threading.Thread(target=work, args=(cfgL[k],))
        threads.append(t)
        time.sleep(5)
        print "Starting Thread: " + str(k)
        t.start()  
    print 
    for thread in threads:
        thread.join()
    print "Followers Collected!" 
    
def createSocialGraph():
    try:
        print "Trying to retrive graph from memory..."
        graph = nx.read_edgelist(open(topic.replace(" ", "") +"_socialGraph.edgelist", "rb"), nodetype=int, create_using=nx.DiGraph())
        print "Graph successfully retrived from memory"
    except:
        graph = nx.DiGraph()
        edges_collection = getMDBCollection(topic + "_edges")
        print "No data found in memory. Building Social Graph from scratch..."
        for doc in edges_collection.find():
            followed = sorted((doc.keys()))[0]
            follower = doc[followed]
            graph.add_edge(int(follower),int(followed))
        print "Social Graph has been built successfully!"
        nx.write_edgelist(graph, open(topic.replace(" ", "")+ "_socialGraph.edgelist", "wb"))
    return graph
        
def networkxOperations(graph):
    print "Computing in-Degree of the graph's nodes... \n "
    in_degree=nx.DiGraph.in_degree(graph)
    in_degree_sequence=sorted(in_degree.values(),reverse=True)
    plt.loglog(in_degree_sequence,'b-',marker='o', label="in-degree")
    print "Computing out-Degree of the graph's nodes... \n "
    out_degree=nx.DiGraph.out_degree(graph)
    out_degree_sequence=sorted(out_degree.values(),reverse=True)
    plt.loglog(out_degree_sequence,'b-',marker='*', label="out-degree")
    print "Computing Closeness of the graph's nodes... \n "
    closeness=nx.closeness_centrality(graph)
    closeness_sequence= sorted(closeness.values(),reverse=True)
    plt.loglog(closeness_sequence,'r-',marker='s', label="closeness")
    print "Computing Betweenness of the graph's nodes... \n "
    betweenness=nx.betweenness_centrality(graph)
    betweenness_sequence = sorted(betweenness.values(), reverse = True)
    plt.loglog(betweenness_sequence,'g-',marker='p', label="betweenness")    
    print "Computing Pagerank of the graph's nodes... \n "
    prank=nx.pagerank(graph, alpha=0.85)
    pagerank_sequence= sorted(prank.values(), reverse=True)
    plt.loglog(pagerank_sequence,'y-',marker='*', label="pagerank")
    print "Computing Clustering Coefficient of the graph..."
    cc=nx.clustering(graph.to_undirected())
    cc_sequence = sorted(cc.values(), reverse=True)
    plt.loglog(cc_sequence,'k-',marker='h', label="cc")
    print (sum(cc_sequence)*1.0)/len(graph), "\n"
    #plotting functions
    plt.title("Graph Properties Rank Plot")
    plt.ylabel("Properties")
    plt.xlabel("Rank")
    plt.legend(loc= 3, prop={"size": 8})
    plt.savefig(topic.replace(" ", "") +"_plot.png")
    plt.show()
    print "Computing Clusering coefficient of nodes... \n ", nx.clustering(graph.to_undirected(), nodes=[choice(graph.nodes()),choice(graph.nodes()),choice(graph.nodes())])
    print "Number of connected components: ", sum(1 for x in nx.connected_components(graph.to_undirected()))
    maxSubGraph = max(nx.connected_component_subgraphs(graph.to_undirected()), key=len)
    core = nx.k_core(maxSubGraph).nodes()
    print "k-core", core
    with open(topic.replace(" ", "")+"_results.csv", "w") as f:
        f.write("NODE"+","+"IN_DEGREE"+","+"OUT_DEGREE"+","+"CLOSENESS"+","+"BETWEENNESS"+","+"PAGERANK"+","+"CC \n")
        for node in graph.nodes():
            f.write(str(node)+","+str(in_degree[node])+","+str(out_degree[node])+","+str(closeness[node])+","+str(betweenness[node])+","+str(prank[node])+","+str(cc[node])+"\n")
            
   
        
print "Hi Welcome to Babooza - The social graph analyzer."
inTop = raw_input("Which topic would you like to analyze (DEFAULT: 0 for Enron Graph - 1 for Banca Etruria Graph) \n")
if inTop=="0":
    topic = "Enron"
    print "You have choosed Enron Graph. \nBulding Social Graph..."
    try:
        gaux = nx.read_edgelist("Email-Enron.txt", nodetype=int, create_using=nx.DiGraph())
        print "Graph Successfully built."
        networkxOperations(gaux)
    except:
        print "Graph not found. Halting program..."
elif inTop == "1":
    topic = "BE"
    print "You have choosed Banca Etruria Graph"
    gaux = createSocialGraph()
    networkxOperations(gaux)
else:
    print "You have choosed: ", inTop
    topic = inTop
    cfgL = getTokens()
    if not os.path.exists(topic.replace(" ","")+"_processedUsers.data"):
        storeTweets(cfgL[0])
        processedUsers = []
    else:
        print "You already tried to look up this topic. Retriving your work..."
        processedUsers = np.load(topic.replace(" ","")+"_processedUsers.data").tolist()
    print "Getting IDs from MongoLab..."
    ids = getIDsFromMDB()
    print "IDs Acquired:", len(ids)
    aux = map(str,processedUsers)
    ids = list(set(ids)-set(aux))
    semaphore = 1
    counter = 0
    getFollowers(cfgL)
    gaux= createSocialGraph()
    networkxOperations(gaux)


    
