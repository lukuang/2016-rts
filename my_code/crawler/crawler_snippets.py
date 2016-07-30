import sys,os
import re
import urllib
import urllib2
import codecs
import time
import math
import string
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
import requests

reload(sys)
sys.setdefaultencoding('utf-8')




def get_mb_queries(original_file):
    title_queries = {}
    desc_queries = {}
    qid = ""
    in_desc = False
    in_title = False
    with open(original_file) as f:
        for line in f:
            line = line.rstrip()
            mn = re.search("<num> Number: (\w+)",line)
            
            if mn is not None:
                qid = mn.group(1)
                title_queries[qid] = ""
                desc_queries[qid] = ""
            else:
                mt = re.search("<title>",line)
                if mt is not None:
                    in_title = True
                    continue
                else:
                    md = re.search("<desc> Description:",line)
                    if md is not None:
                        in_desc = True
                        continue
                    else:
                        ma = re.search("<narr> Narrative:",line)
                        if ma is not None:
                            in_desc = False
            
            if in_desc:
                desc_queries[qid] += line+"\n"
            elif in_title:
                title_queries[qid] = line+"\n"
                in_title = False
    return title_queries,desc_queries


class BingSearchAPI():
    bing_api = "https://api.datamarket.azure.com/Bing/Search/Web?$format=json"
    def __init__(self, key):
        self.key = key

    def replace_symbols(self, request):
        # Custom urlencoder.
        # They specifically want %27 as the quotation which is a single quote '
        # We're going to map both ' and " to %27 to make it more python-esque
        request = string.replace(request, "'", '%27')
        request = string.replace(request, '"', '%27')
        request = string.replace(request, '+', '%2b')
        request = string.replace(request, ' ', '%20')
        request = string.replace(request, ':', '%3a')
        return request
        
    def search(self, query, params):
        ''' This function expects a dictionary of query parameters and values.
            Sources and Query are mandatory fields. 
            Sources is required to be the first parameter.
            Both Sources and Query requires single quotes surrounding it.
            All parameters are case sensitive. Go figure.

            For the Bing Search API schema, go to http://www.bing.com/developers/
            Click on Bing Search API. Then download the Bing API Schema Guide
            (which is oddly a word document file...pretty lame for a web api doc)
        '''
        request = '&Query="'  + str(query) + '"'
        for key,value in params.iteritems():
            request += '&' + key + '=' + str(value) 
        request = self.bing_api + self.replace_symbols(request)
        print request
        return requests.get(request, auth=(self.key, self.key))

    def search_next(self, url):
        print url
        return requests.get(url, auth=(self.key, self.key))



class snippets_crawler():
    def __init__(self, query_id, query,dest_dir,limit):
        self.query_id = query_id
        self.query = query
        self.results_limit = limit
        self.pages_cnt = 1
        self.crawl_idx = 1
        self.url_base = ''
        self.parameters = {}
        self.url_list = []
        self.results = []
        self.output_root = os.path.join(dest_dir, str(query_id))
        
        if not os.path.exists(self.output_root):
            os.makedirs(self.output_root)   
            self.need = True
        else:
            self.need = False             

        
    def get_page(self,url,para=None):
        try:
            response = requests.get(url, params=para)
            response.encoding = 'utf-8'
            if response.status_code == 403:
                print '403 ' + url
                sys.exit()
            if "ipv4" in response.url:
                raise RuntimeError("Found ipv4 in response url:\n%s" %sresponse.url)
            return response.url,response.text
        except:
            print 'Error: ' + url
            return 'ERROR','ERROR'                  

            
            
    def google_get_search_results(self, url, content):
        time.sleep(20)
        print url
        page = BeautifulSoup(content, 'lxml')
        
        if page.find('div', id='ires'):
            #print "found result"
            #results_cnt = int(page.find(id='sortBy').find('span', 'sortRight').span.string.split()[-2])
            list_results = page.find('div', id='ires').find_all('div', class_='g')
            
            for l in list_results:
                if l.find('h3', 'r'):
                    if not l.find('h3', 'r').find("a"):
                        continue
                    href = l.find('h3', 'r').a['href']
                    decoder = href.split('?')[1].split('&')
                    href_link = ''
                    for d in decoder:
                        #print d
                        if d.split('=')[0] == 'q':
                            href_link = d.split('=')[1]
                            if len(href_link) > 0:
                                url = href_link
                                if url not in self.url_list:
                                    self.url_list.append(url)
                              
                                    if l.find('span', class_='st'):
                                        #print "YES!"
                                        #print l.find('span', class_='st')
                                        snippets = l.find('span', class_='st').get_text()
                                        #print type(snippets)
                                    else:
                                        snippets = u''
                                    # print "snippets:"
                                    # print snippets
                                    self.results.append({'id':self.query_id+'_google_'+str(self.crawl_idx), 'url':url, 'snippets':snippets})
                    
                                    self.crawl_idx += 1
                                    #print self.pages_cnt,self.max_pages
                                    if self.crawl_idx > self.results_limit:
                                        self.crawl_idx = 1
                                        return                                

                
            if page.find('table', id='nav'):
                page_index = page.find('table', id='nav').find_all('td')
                
                # for ele in page_index:
                #     print ele
                       
                for i in range(len(page_index)):
                    if not page_index[i].find('a'):
                        if self.pages_cnt == 1:
                            if i+2 == len(page_index):
                                break
                            next_page = page_index[i+2]
                        else:
                            if i+1 == len(page_index):
                                break
                            next_page = page_index[i+1]
                        
                        if next_page.find('a'):

                            next_url = 'http://www.google.com'+next_page.a['href']
                            # print "next url:"
                            # print next_url
                            self.pages_cnt += 1                    
                            next_url, next_content = self.get_page(next_url)
                            self.google_get_search_results(next_url, next_content)
                        else:
                            return
                        break



    def google_crawl(self):
        self.url_base = 'http://www.google.com/search?'
        self.parameters = {}
        self.parameters['q'] = self.query
        self.parameters['hl'] = 'en'

        self.pages_cnt = 1
        self.crawl_idx = 1
        self.results = []
        self.url_list = []
        
        final_url, content = self.get_page(self.url_base, self.parameters)
        print final_url 
        with codecs.open('./google_test', 'wb', 'utf-8') as out:
            out.write(content)
        
        print 'crawling Google data...'
        
        self.google_get_search_results(final_url, content)
        with codecs.open(os.path.join(self.output_root, 'google.json'), 'wb', 'utf-8') as f:
            json.dump(self.results, f, indent=4)
    
        
    def yahoo_get_search_results(self, url, content):
        page = BeautifulSoup(content, 'lxml')
        with codecs.open("yahoo_test","w","utf-8") as f:
            f.write(content)
        if page.find('div', id='web'):
            #print "found web"
            #print page.find('div', id='web')
            list_results = page.find('div', id='web').find_all('li')
            
            for l in list_results:
                #print "found result"
                #print l

                if l.find('div', class_='compTitle'):

                    #print l.find('div', 'compText aAbs')
                    #print "found title"
                    if l.find('div', class_='compTitle').find('h3'):
                        if l.find('div', class_='compTitle').find('h3').find('a'):
                            href_link = l.find('div', class_='compTitle').find('h3').a['href']
                            #print "found url"
                            if len(href_link) > 0:
                                url = href_link
                                if url not in self.url_list:
                                    self.url_list.append(url)
                                    if l.find('div',class_='compText'):
                                        if l.find('div',class_='compText').find('p'):
                                            snippets = l.find('div',class_='compText').find('p').get_text()
                                        else:
                                            snippets = u''
                                    
                                        self.results.append({'id':self.query_id+'_yahoo_'+str(self.crawl_idx), 'url':url, 'snippets':snippets})

                                    self.crawl_idx += 1
                                    #print self.pages_cnt,self.max_pages
                                    if self.crawl_idx > self.results_limit:
                                        self.crawl_idx = 1
                                        return
                        else:
                            continue
                    else:
                        print "compTitle aAbs not found!"

            
            if page.find('div', class_='compPagination'):
                if page.find('div', class_='compPagination').find("a",class_="next"):
                    next_url = page.find('div', class_='compPagination').find("a",class_="next")['href']       
                    next_url, next_content = self.get_page(next_url)
                    print next_url
                    self.yahoo_get_search_results(next_url, next_content)
                else:
                    return
                        
                

    def yahoo_crawl(self):
        self.url_base = 'http://search.yahoo.com/search?'
        self.parameters = {}
        self.parameters['p'] = self.query

        self.crawl_idx = 1
        self.results = []
        self.url_list = []
        final_url, content = self.get_page(self.url_base, self.parameters)
        
        with codecs.open('./yahoo_test', 'wb', 'utf-8') as out:
            out.write(content)
        
        print 'crawling Yahoo data...'
        print final_url
        self.yahoo_get_search_results(final_url, content)
        with codecs.open(os.path.join(self.output_root, 'yahoo.json'), 'wb', 'utf-8') as f:
            json.dump(self.results, f, indent=4)


    def handle_bing_results(self, json_object, my_key):
        stop = False
        if 'd' in json_object:
            if 'results' in json_object['d']:
                for ele in json_object['d']['results']:
                    if ele['Url'] not in self.url_list:
                        self.url_list.append(ele['Url'])
                        self.results.append({'id':self.query_id+'_bing_'+str(self.crawl_idx), 'url':ele['Url'], 'snippets':ele['Description']})
                        self.crawl_idx += 1
                        if self.crawl_idx > self.results_limit:
                            stop = True
                            break
            if not stop:
                if '__next' in json_object['d']:   
                    next_url = json_object['d']['__next'].split('?')[0]+'?$format=json&'+json_object['d']['__next'].split('?')[1]
                    bing = BingSearchAPI(my_key)
                    json_results = bing.search_next(next_url).json()
                    self.handle_bing_results(json_results, my_key)


    def bing_crawl(self):
        my_key = "xq8N3fk9oXvw86bXSdP/KSo7bfS+X0fbIKTTqkA+SDE"
        query_string = self.query
        bing = BingSearchAPI(my_key)
        params = {'$top': 100,
                  '$skip': 0}

        self.crawl_idx = 1
        self.results = []
        self.url_list = []
        
        result = bing.search(query_string,params)
        try:
            json_results = result.json()
        except:
            print result
            sys.exit(-1)
        self.handle_bing_results(json_results, my_key)

        with codecs.open(os.path.join(self.output_root, 'bing.json'), 'wb', 'utf-8') as f:
            json.dump(self.results, f, indent=4)

  
    def start_crawl(self):
        print 'Crawl Query %s: %s' %(self.query_id,self.query)
        if not self.need:
            print "already crawled, go next!"
        else:
            self.google_crawl()
            self.yahoo_crawl()
            self.bing_crawl()


def load_queries():
    fn = '/home/lukuang/2015_RTS/2015-data/TREC2015-MB-testtopics.txt'

    queries_list = []
    title_queries,desc_queries = get_mb_queries(fn)
    for qid in sorted(title_queries.keys()):
        q_string = title_queries[qid]
        q_string = re.sub("\&"," ",q_string)
        queries_list.append((qid,q_string))
    #with open(fn) as f:
    #    for line in f:
    #        line = line.strip()
    #        if line:
    #            row = line.split(':')
    #            queries_list.append((row[0],row[1]))

    return queries_list
    
    
if __name__ == '__main__':
    very_start = datetime.now()
    queries = load_queries()

    for q in queries:
        snippets_crawler(q[0],q[1],"./raw").start_crawl()

