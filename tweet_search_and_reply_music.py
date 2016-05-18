from common_folder import common_library as common
from common_folder import twitter_keys

import datetime
import logging
import random
import re
import tweepy
import pickle

# Global Variables
DATABASE = {}
CONSUMER_KEY = twitter_keys.keys["fwconsumer_key"]
CONSUMER_SECRET = twitter_keys.keys["fwconsumer_secret"]
ACCESS_TOKEN = twitter_keys.keys["fwaccess_key"]
ACCESS_TOKEN_SECRET = twitter_keys.keys["fwaccess_secret"]
LOGGER = logging.getLogger(common.LOGGER_NAME)


def get_tweets_and_reply(keyword, count, latest_date_id, respond_to_retweets):
  """
  Get x number of latest tweets since last tweet date that conatins
  a certain keyword

  Args:
    keyword (string) The string to search for in tweets
    count (int) The count of tweets to pull back
    latest_date_id (int) An int representing the latest tweet date id
    respond_to_retweets (bool) Whether to respond to retweets or not

  Returns None
  """
  set_up_logger()
  LOGGER.info("Starting get_tweets_and_reply()")

  api = login_to_api()
  if not api:
    raise Exception("Can't log in to API")

  # Search for tweets with keword since given date
  last_tweet_date = str(DATABASE['date_of_last_tweet']['datetime'])
  LOGGER.info("Searching for tweets with keyword '{kw}' since {date}".format(kw=keyword, date=last_tweet_date))
  twts = api.search(q=keyword, count=count, since_id=latest_date_id)  
  LOGGER.info("API Search Finished")
  # if no tweets found
  if len(twts) == 0:
    LOGGER.info("No tweets with keyword '{kw}' found since {date}".format(kw=keyword, date=last_tweet_date))
    return
  # Iterate over found tweets
  LOGGER.info("Iterating over {num} tweets".format(num=len(twts)))
  for twt in twts:
    # Check to see if tweet qualifies for reply
    if not tweet_qualifies_for_reply(twt, retweets_allowed=respond_to_retweets):
      continue
    # create the reply object
    reply_obj = generate_reply_obj(twt)
    # send friend request and tweet back a reply
    send_friend_request(api, reply_obj['username'])
    tweet_reply(api, reply_obj['reply'], reply_obj['tweet_id'])
    # update the database with data
    update_database(twt, reply_obj)
    try:
      LOGGER.info("Tweet from @{}: {}".format(twt.user.screen_name, twt.text))
    except UnicodeEncodeError:
      LOGGER.info("Can't print text from tweet due to unicode error.")
    LOGGER.info("Replied message {}".format(reply_obj['reply'], 
                                            reply_obj['username']))

def remove_username_from_tweet(twt_text):
  """
  Removes the username from a tweet. Example "@mike hello" -> "hello"

  Args:
    twt_text (string) The tweet text to remove the username from

  Returns (string) The tweet minus the username and space
  """
  return re.sub("@\w+\s", "", twt_text)

def send_friend_request(api, username):
  """
  Creates a friend request using the API

  Args:
    api (obj) The API object
    username (string) The username of the user the request goes to

  Returns None
  """
  api.create_friendship(username)

def tweet_reply(api, reply, tweet_id):
  """
  Creates a reply tweet using the API

  Args:
    api (obj) The API object
    reply (string) The reply text to send
    tweet_id (int) The tweet id to identify the original tweet

  Returns None
  """
  api.update_status(status=reply, in_reply_to_status_id=tweet_id)
  return

def set_up_logger():
  """
  Sets up the logger with formatting

  Args:

  Returns None
  """
  log_file = common.LOG_NAME
  # Empty log file.
  open(log_file, "w").close()
  LOGGER.filemode = "w"
  LOGGER.setLevel(logging.DEBUG)
  fh = logging.FileHandler(log_file)
  fh.setLevel(logging.DEBUG)
  formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  fh.setFormatter(formatter)
  LOGGER.addHandler(fh)

def login_to_api():
  """
  Logs into the api with the access tokens

  Args:

  Returns API object
  """
  try:
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    LOGGER.info("Logged in successfully")
  except Exception as e:
    LOGGER.info("Unable to login: {error}".format(error=e))
    return
  return tweepy.API(auth)

def open_database(database_name, api):
  """
  Opens database or creates an empty database using pickle.

  Args:
    database_name (string) The name to identy the database file

  Returns None
  """
  try:
    with open(database_name, 'r') as f:
      loaded_database = pickle.load(f)
      global DATABASE
      DATABASE = loaded_database
  except:
    DATABASE = {}
    with open(database_name, "wb") as f:
      pickle.dump(DATABASE, f)
  if not DATABASE.has_key("date_of_last_tweet"):
    last_tweet_obj = get_last_tweet_data(api)
    DATABASE["date_of_last_tweet"] = {}
    DATABASE["date_of_last_tweet"]["datetime"] = (datetime.datetime.now() - datetime.timedelta(days=1))
    DATABASE["date_of_last_tweet"]["tweet_id"] = last_tweet_obj.id
  if not DATABASE.has_key("users_we_tweeted_to"):
    DATABASE["users_we_tweeted_to"] = []
  if not DATABASE.has_key("last_tweet_we_tweeted"):
    DATABASE["last_tweet_we_tweeted"] = last_tweet_obj.text

def update_database(twt, reply_obj):
  """
  Updates the database with the replies sent

  Args:
    twt (obj) The tweet object that we are replying to
    reply_obj (obj) The reply object holding the message, username and tweet_id

  Returns None
  """
  # Log creation date and latest date for visual comparison
  print "twt.created_at: {}".format(twt.created_at)
  print "latest date: {}".format(DATABASE["date_of_last_tweet"]["datetime"])

  # Update latest date json with current tweet details
  latest_date_string = str(DATABASE["date_of_last_tweet"]["datetime"])
  if str(twt.created_at) > latest_date_string:
    DATABASE["date_of_last_tweet"]["datetime"] = twt.created_at
    DATABASE["date_of_last_tweet"]["tweet_id"] = str(twt.id)
  
  #Add data to the database
  message = reply_obj["reply"]
  message_text = remove_username_from_tweet(message)
  
  DATABASE[twt.id] = {
    "username" : twt.user.screen_name,
    "tweet" : twt.text,
    "geo" : twt.geo,
    "tweet_id" : twt.id,
    "created_at" : twt.created_at,
    "reply" : message_text
  }

  DATABASE["users_we_tweeted_to"].append(twt.user.screen_name)
  DATABASE["last_tweet_we_tweeted"] = message_text
  print "Added id {} to database".format(str(twt.id))

def tweet_qualifies_for_reply(twt, retweets_allowed=True):
  """
  Performs validation on a twt object to see if we will respond

  Args:
    twt (obj) The tweet object that we are replying to
    retweets_allowed (bool) Decides whether we will respond to retweeted tweets
  """
  tweet_lowercase_text = twt.text.lower()
  # Ignore retweets if flag is set to True
  if not retweets_allowed:
    if tweet_lowercase_text.startswith("rt"):
      LOGGER.info("tweet is a RT. Ignoring.")
      return False

  # Check to see if tweet already exists in the database
  if DATABASE.has_key(str(twt.id)):
    print "id {} already exists".formatted(str(twt.id))
    LOGGER.info("tweet already exists. Ignoring.")
    return False

  # Check to ensure there are no negative words in the tweet text
  for negative_word in common.NEGATIVE_WORDS:
    if negative_word.lower() in tweet_lowercase_text:
      LOGGER.info("Negative word in tweet. Not replying.")
      print "Negative tweet username: {}".format(twt.user.screen_name)
      return False

  # Dont send reply to anyone we have previously replied to
  if twt.user.screen_name in DATABASE["users_we_tweeted_to"]:
    LOGGER.info("User already tweeted to before.")
    return False
  return True


def generate_reply_obj(twt):
  """
  Creates a reply object that holds the reply message, username and tweet_id

  Args:
    twt (obj) The tweet object that we are replying to

  Returns reply_obj (obj)
  """
  LOGGER.info("starting generate_reply_obj()")
  replies_with_usable_length = []
  # Check to see if reply is shorter than length of username
  username_string = "@{name} ".format(name=twt.user.screen_name)

  # Get a reply that plugs the latest song on youtube
  for possible_reply in common.SONG_REPLIES:
    if len(possible_reply) < (140 - len(username_string)):
      replies_with_usable_length.append(possible_reply)

  # if no replies available or the latest song is in the tweet, use placeholder
  if (len(replies_with_usable_length) == 0 
    or common.LATEST_SONG_NAME in twt.text.lower()):
    placeholder_reply = ":)"
  else:
    placeholder_reply = random.choice(replies_with_usable_length)

  # If last reply is the same as this reply, get a non song reply
  if placeholder_reply == DATABASE["last_tweet_we_tweeted"]:
    placeholder_reply = random.choice(common.NON_SONG_REPLIES)

  #Create message
  message = "{twt_handle}{text}".format(twt_handle=username_string,
                                        text=placeholder_reply)
  reply_obj = {
    "reply" : message,
    "tweet_id" : twt.id,
    "username" : twt.user.screen_name
    }
  return reply_obj

def close_database(database_name):
  """
  Closes and updates pickle database.
  
  Args:
    database_name (string) The name of the database
  
  Returns: None
  """
  with open(database_name, 'w') as f:
    pickle.dump(DATABASE, f)


def print_database_data_to_screen():
  """
  Prints the contents of the database to the screen
  
  Returns: None
  """
  open_database(common.DATABASE_NAME)
  for item, value in DATABASE.iteritems():
    print "{} : {}".format(item, value)
  return


def get_last_tweet_data(api):
  """
  Gets the latest tweet data
  
  Returns: None
  """
  # http://docs.tweepy.org/en/latest/api.html#API.user_timeline
  latest_tweets = api.user_timeline(id = api.me().id, count = 1)
  return latest_tweets[0]


def main():
  api = login_to_api()
  open_database(common.DATABASE_NAME, api)
  latest_tweet_id = DATABASE["date_of_last_tweet"]["tweet_id"]
  get_tweets_and_reply(common.BAND_NAME, 3, latest_tweet_id, False)
  close_database(common.DATABASE_NAME)


if __name__ == "__main__":
  #print_database_data_to_screen()
  main()
