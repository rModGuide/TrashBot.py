# TrashBot - Keep the front page clean of low effort, trash posts that are highly downvoted.

# Import modules the script needs to work
import praw
import time
from time import localtime, timezone
from datetime import datetime as dt, timedelta as td, date, timezone
import pmtw
import traceback

### User defined variables section

# Define the subreddit that you are working on.
sub_name = "YOUR_SUBREDDIT"

# Set this number anywhere from 1-1000.  This is how many posts the bot will check each pass.
posts_to_check = 500

# Define how much time to sleep before the next pass.
# 3600 seconds in one hour.
sleep_seconds = 3600

# Define time threshold for post removal.
minimum_hours = 5

# Submission upvote ratio.
# number is a decimal with two digits.
# Thirty three percent is represented as 0.33.
vote_score = 0.33

# This function logs you into reddit and creates the reddit instance.
# These values are stored in a separate config file that is imported.
# This is for security.  If you need to share the code, you won't accidentally share your login credentials.
def reddit_login():
    print("Connecting to reddit...")
    try:
        reddit = praw.Reddit(
            client_id='',
            client_secret='',
            user_agent=f"Post Quality Monitor Bot for /r/{sub_name} by u/buckrowdy - v0.1 ",
            username='',
            password='',
        )

    except Exception as e:
        print(f"\t### ERROR - Could not login.\n\t{e}")
        traceback.print_exc()
    print(f"Logged in as: {reddit.user.me()}")
    return reddit


# Get new submissions from the subreddit.
# The script will check the new posts from a limit you set up above.
def get_latest_submissions(subreddit):
    print(f"Getting posts from {sub_name}...")
    submissions = subreddit.new(limit=int(posts_to_check))
    print("Done")
    return submissions


#  This function checks submissions for timestamp.
def check_submissions(submissions):
    try:
        print("Now processing submissions...")
        for submission in submissions:
            # Set up a removal reply
            removal_reply = f"""Hello u/{submission.author}.\nYour post to r/{submission.subreddit} has been removed. 
			To maintain a high level of quality on the front page, any post with a negative post score after {minimum_hours} hours of posting will be removed.  Please [see here for more info.](http://reddit.com/r/{submission.subreddit}/about/rules)\n\n*I am a bot. Replies and chats will not receive replies.*  
			If you feel this was done in error, or would like better clarification or need further assistance, 
			please [message the moderators.](https://www.reddit.com/message/compose?to=/r/{submission.subreddit}&subject=Question regarding the removal of this submission by /u/{submission.author}&message=I have a question regarding the removal of this submission: {submission.permalink})"""
            # Get the UTC unix timestamp
            ts = submission.created_utc
            # Convert to datetime format
            post_time = dt.utcfromtimestamp(ts)
            # Get the current UTC time
            current_time = dt.utcnow()
            # Convert timestamps to check them for the 5 hour threshold.
            hours_since_post = int(
                (current_time - post_time).seconds / (minimum_hours * 60)
            )
            hour_converter = float(hours_since_post / 60)
            float_convert = round(hour_converter, 1)
            print(
                f"{post_time} - ({float_convert} hrs) - {submission.upvote_ratio} - u/ {submission.author}\n\t{submission.title}"
            )
            # Check if post is past the minimum threshold.
            # If post is over the threshold, check the upvote ratio, then removes
            if hours_since_post >= int(minimum_hours):
                if submission.upvote_ratio <= int(vote_score):
                    post_submission = reddit.submission(id=submission.id)
                    this_comment = post_submission.reply(body=removal_reply)
                    this_comment.mod.distinguish(how="yes", sticky=True)
                    this_comment.mod.lock()
                    submission.mod.remove(mod_note="dv<25%")
                    print(f"\t### REMOVE ITEM {submission.id} - {submission.title}\n")

                    #  Leave a toolbox usernote.
                    notes = pmtw.Usernotes(reddit, submission.subreddit)
                    link = f"{submission.permalink}"
                    n = pmtw.Note(user=f"{submission.author}", note="dv<33%", link=link)
                    notes.add_note(n)
                else:
                    continue

        print("Done")
    except Exception as e:
        print(f"\t### ERROR - SOMETHING WENT WRONG.\n\t{e}")
        traceback.print_exc()


######################################

### Bot starts here

if __name__ == "__main__":
    try:
        # Connect to reddit and return the object
        reddit = reddit_login()
        # Connect to the sub
        subreddit = reddit.subreddit(sub_name)

    except Exception as e:
        print("\t\n### ERROR - COULD NOT CONNECT TO REDDIT.")
        traceback.print_exc()

    # Loop the bot
    while True:
        try:
            # Get the latest submissions after emptying variable
            submissions = None
            submissions = get_latest_submissions(subreddit)

        except Exception as e:
            print("\t### ERROR - Could not get posts from reddit")
            traceback.print_exc()

        if not submissions is None:
            # Once you have submissions, check their score and timestamp.
            check_submissions(submissions)

        # Loop every X seconds (60 minutes, currently.)
        sleep_until = (dt.now() + td(0, sleep_seconds)).strftime("%H:%M:%S")
        print(f"Be back around {sleep_until}.")
        print("    ")
        time.sleep(sleep_seconds)
