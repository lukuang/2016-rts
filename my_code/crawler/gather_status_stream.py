# Twitter Tools
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from datetime import datetime
import argparse,json,os
import logging
import logging.handlers

from myUtility.misc import gene_single_indri_text

_current_dir = os.path.dirname(os.path.abspath(__file__))
_module_dir = os.path.dirname(os.path.abspath(_current_dir))
import sys
sys.path.append(_module_dir)

from process_tweet  import CrawledTweet




class TweetListener(StreamListener):

  def __init__(self,log_dir,text_dir,api=None):
    super(TweetListener,self).__init__(api)
    self.logger = logging.getLogger('tweetlogger')
    self.text_logger = logging.getLogger("textlogger")

    self._log_dir,self._text_dir = log_dir,text_dir

    now = datetime.utcnow()
    statusHandler = logging.handlers.TimedRotatingFileHandler(os.path.join(self._log_dir,'status.log'),when='M',encoding='utf-8',utc=True)
    statusHandler.setLevel(logging.INFO)
    self.logger.addHandler(statusHandler)
    
    textHandler = logging.handlers.TimedRotatingFileHandler(os.path.join(self._text_dir,'status.log'),when='M',encoding='utf-8',utc=True)
    textHandler.setLevel(logging.INFO)
    self.text_logger.addHandler(textHandler)

    warningHandler = logging.handlers.TimedRotatingFileHandler(os.path.join(self._log_dir,'warning.log'),when='H',encoding='bz2',utc=True)
    warningHandler.setLevel(logging.WARN)
    self.logger.addHandler(warningHandler)
    logging.captureWarnings(True);

    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.WARN)
    self.logger.addHandler(consoleHandler)


    self.logger.setLevel(logging.INFO)
    self.count = 0

  def on_data(self,data):
    self.count+=1
    self.logger.info(data)
    if self.count % 1000 == 0:
        print "%d statuses processed" % self.count
    
    if len(data)!=0:
        data = json.loads(data)
        if "delete" not in data:
            tweet = CrawledTweet(data)
            single_document_text = gene_single_indri_text(
                                  tweet.tid,tweet.text,
                                  tweet.extra_fields,
                                  tweet.field_data)
            self.text_logger.info(single_document_text)

    return True

  def on_error(self,exception):
    self.logger.warn(str(exception))

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("auth_file")
  parser.add_argument("text_dir")
  parser.add_argument("log_dir")
  args=parser.parse_args()

  listener = TweetListener(args.log_dir,args.text_dir)
  auth_info = json.load(open(args.auth_file))
  consumer_key = auth_info["consumer_key"]
  consumer_secret = auth_info["consumer_secret"]
  access_token = auth_info["access_token"]
  access_token_secret = auth_info["access_token_secret"]


  auth = OAuthHandler(consumer_key,consumer_secret)
  auth.set_access_token(access_token,access_token_secret)

  stream = Stream(auth,listener)
  while True:
    try:
      stream.sample()
    except Exception as ex:
      print str(ex)
      pass
