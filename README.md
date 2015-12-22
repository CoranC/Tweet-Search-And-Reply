# Tweet-Search-And-Reply
A module to search for tweets with given keywords and respond to them automatically

In this module, I use tweepy to query the Twitter API for tweets with certain keywords.

## Requirements:
*Tweepy* http://www.tweepy.org/

*Pickle*

*Common Library*: I created a common library where I stored terms and keyword lists that I used.

*Twitter Keys*: The file stores all of the specific access keys I need.

## Background:
I was approached by a band who wanted to promote their latest song on twitter in a streamlined way.
We discussed a tool whereby we would search for people who were talking about them and tweet those users
a link to their latest song. This was an interesting task with some interesting challenges.

**1. What tweets should we look for?**

Any tweets containing the bands name or their twitter handle

**2. What tweets should we reply to?**

The tweets are validated to see if they are worth responding to:
- Has the bot already tweeted this person?
- Has the tweet got any negative words in it that we want to avoid?
- Is the tweet a RT, and if so, do we want to ignore this?
- Has this tweet been responded to before?
If any of these are true, we should ignore the tweet.

Otherwise, we will respond with a choice of replies
- Has the tweet got the name of the bands latest song in it? If so, do not reply with a link to the song as they obviously already know it. Send back a placeholder reply
- Otherwise, respond with a nice reply and a link to the song

**3. Lets friend request the people tweeting about us!**

This is useful as you can send a friend request which won't execute if they are already a follower!

**4. How will we record the data?**

I use the pickle module here to record all tweets we respond to.
This data informs future validation checks! Awesome...

**5. When will we run it?**

Daily of course! A borg file will execute the python file every night!