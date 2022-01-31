###TODO list
# 1. Make a function that sorts the dictionary by the number of likes
# 2. Compare 2018/2019 to other years like 2020 and 2021 using #atclassof20XX

import time
import sys

import TagParser as parser
import Utilities as util

PAGES = 20
MAX_POSTS_PER_PAGE = 50
METADATA_ROOT = "..\\metadata\\"
DATA_ROOT = "..\\data\\"
ERR_USAGE = "Usage:\npython CollectData.py <hashtag>\npython CollectData.py <hashtag> <num_pages>\npython CollectData.py <hashtag> <num_pages> <end_cursor>"

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

class ParseRequest:
    def __init__(self, tag, num_pages=PAGES, end_cursor=None):
        self.tag = tag
        self.num_pages = num_pages
        self.end_cursor = end_cursor

class Post:
    def __init__(self, id, postCode, likes, timeStamp, tags, caption):
        self.id = id
        self.postCode = postCode
        self.likes = likes
        self.timeStamp = timeStamp
        self.tags = tags
        self.caption = caption
        
    
    def __str__(self):
        return "Post_ID: " + self.id + " | Post_Code: " + self.postCode + " | Likes: " + str(self.likes) + " | Time Stamp: " + str(self.timeStamp) + " | Tags: " + str(self.tags) + " | Caption: " + self.caption 
    
    def timeToStr(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timeStamp))

# main function
def main():
    start = time.time()
    # check if proper number of arguments are given
    # and set up request object
    if len(sys.argv) == 1:
        print("Invalid number of arguments\n" + ERR_USAGE)
        return -1
    
    request = ParseRequest(sys.argv[1])
    if len(sys.argv) == 3:
        hashtag = sys.argv[1]
        num_pages = int(sys.argv[2])
        end_cursor = None
        request = ParseRequest(hashtag, num_pages, end_cursor)
    elif len(sys.argv) == 4:
        hashtag = sys.argv[1]
        num_pages = int(sys.argv[2])
        end_cursor = sys.argv[3]
        request = ParseRequest(hashtag, num_pages, end_cursor)
    elif len(sys.argv) > 4:
        print("Invalid number of arguments\n" + ERR_USAGE)
        return -1
    
    # create url from request object
    url = util.make_url(request.tag, MAX_POSTS_PER_PAGE, request.end_cursor) # make url
    print(url) #display url


    # create browser and store results
    currTime = int(time.time())
    allPosts, finalCursor = selenium(request) # opens in controlled browser
    print("Number of posts: ", len(allPosts))

    # Prints results of all_tags to a file ../Data/<tag>_<num_pages>pages_<unix_time>.txt
    outputFilename = DATA_ROOT + request.tag + "_" + str(request.num_pages) + "pages_" + str(currTime) + ".txt"
    with open(outputFilename, 'w', encoding="utf8") as f:
        for post in allPosts:
            f.write(str(post) + "\n")
    
    # Print metadata to a file ../Data/_bookmark_<tag>_<num_pages>pages_<unix_time>.txt
    metaFilename = METADATA_ROOT + "_bookmark_" + request.tag + "_" + str(request.num_pages) + "pages_" + str(currTime) + ".txt"
    with open(metaFilename, 'w', encoding="utf8") as f:
        f.write("Final Cursor: " + str(finalCursor) + "\n")
        f.write("Number of posts: " + str(len(allPosts)) + "\n")
        f.write("Last Post Date: " + str(allPosts[-1].timeStamp) + "\n\n")
        f.write(allPosts[-1].timeToStr()) # Writes date of last post in allPosts array)

    end = time.time()
    print("Time taken: " + str(end - start))
    return 0


# Given a properly established browser, logs in to Instagram using the credentials.txt file
def sel_login(browser):
    #open file "../auth/credentials.txt" and store the first line in variable username and second line in variable password
    with open("../auth/credentials.txt", "r") as f:
        username = f.readline()
        password = f.readline()

    #create chrome browser
    browser.get("https://www.instagram.com/")
    wait = WebDriverWait(browser, 10) # [1] code adapted from https://stackoverflow.com/questions/54125384/instagram-login-script-with-selenium-not-being-able-to-execute-send-keystest

    second_page_flag = wait.until(EC.presence_of_element_located(
        (By.CLASS_NAME, "KPnG0")))  # util login page appear


    user = browser.find_element_by_name("username") 
    passw = browser.find_element_by_name('password')

    ActionChains(browser)\
        .move_to_element(user).click()\
        .send_keys(username)\
        .move_to_element(passw).click()\
        .send_keys(password)\
        .send_keys(Keys.RETURN)\
        .perform() # [/1]

# This function parses data from a given URL and returns a list of Post objects and the end_cursor for the next page
def sel_parse(browser, url):
    browser.get(url) # gets url and automatically waits for page to load
    html = browser.page_source
    json_str = html[84:-20] # remove first and last part of html to only get JSON contents of page
    json1 = util.read_json(json_str)
    posts_json = json1['data']['hashtag']['edge_hashtag_to_media']['edges']

    posts = []
    for i in range(len(posts_json)):
        id = posts_json[i]['node']['id']
        shortCode = posts_json[i]['node']['shortcode']
        likes = posts_json[i]['node']['edge_liked_by']['count']
        timeStamp = posts_json[i]['node']['taken_at_timestamp']
        caption = posts_json[i]['node']['edge_media_to_caption']['edges']
        tags = []
        if len(caption) > 0:
            caption = caption[0]['node']['text']
            tags = parser.parse_desc(caption)
            caption = caption.replace('\n', "<\\br>").replace('\r', "<\\br>")
        else:
            caption = ""
        post = Post(id, shortCode, likes, timeStamp, tags, caption)
        posts.append(post)
    
    end_cursor = json1["data"]["hashtag"]["edge_hashtag_to_media"]["page_info"]["end_cursor"]
    
    return posts, end_cursor


# Function that does everything related to selenium (opens browser, logs in, reads posts under tags, closes browser)
# Returns a list of all post objects found under the given tag
def selenium(request):
    print("Tag: ", request.tag)
    print("Number of entries: " + str(request.num_pages))
    browser = webdriver.Chrome(executable_path="../chromedriver.exe")
    sel_login(browser)
    time.sleep(5) # wait for login to complete

    allPosts = []

    for i in range(request.num_pages):
        print("Parsing page " + str((i+1)))
        url = util.make_url(request.tag, MAX_POSTS_PER_PAGE, request.end_cursor)
        posts, end_cursor = sel_parse(browser, url)
        request.end_cursor = end_cursor
        allPosts.extend(posts)
        # tags = IP.all_tags(json_str)
        # all_tags = IP.combine_tags(all_tags, tags)


    browser.quit()
    # tags = IP.combine_tags(tags1, tags2)
    return allPosts, request.end_cursor

# start main
if __name__ == "__main__":
    main()