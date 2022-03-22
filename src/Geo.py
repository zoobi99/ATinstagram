
import time
import sys
import os

import Utilities as util
from Utilities import Post


DATA_ROOT = "..\\data\\"

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys


class GeoPost:
    def __init__(self,id, postCode, name, address, city, lng, lat):
        self.id = str(id)
        self.postCode = str(postCode)
        self.name = str(name)
        self.address = str(address)
        self.city = str(city)
        self.lng = int(lng)
        self.lat = int(lat)
    
    def __str__(self):
        return "Post_ID: " + self.id + "\t|Post_Code: " + self.postCode + "\t|name: " + self.name + "\t|address: " + str(self.address) + "\t|city: " + str(self.city) + "\t|lng: " + int(self.lng) + "\t|lat: " + int(self.lat)
    
    def asArray(self):
        return [self.id, self.postCode, self.name, self.address, self.city, self.lng, self.lat]



# Given a properly established browser, logs in to Instagram using the credentials.txt file
def sel_login(browser):
    #open file "../auth/credentials.txt" and store the first line in variable username and second line in variable password
    with open("../auth/credentials.txt", "r") as f:
        username = f.readline()
        password = f.readline()

    # Create Chrome browser
    browser.get("https://www.instagram.com/")
    wait = WebDriverWait(browser, 10) # [1] code adapted from https://stackoverflow.com/questions/54125384/instagram-login-script-with-selenium-not-being-able-to-execute-send-keystest

    second_page_flag = wait.until(EC.presence_of_element_located(
        (By.CLASS_NAME, "KPnG0")))  # wait until login page appears


    user = browser.find_element_by_name("username") # Find username field
    passw = browser.find_element_by_name('password') # Find password field

    # Enters username and password
    ActionChains(browser)\
        .move_to_element(user).click()\
        .send_keys(username)\
        .move_to_element(passw).click()\
        .send_keys(password)\
        .send_keys(Keys.RETURN)\
        .perform() # [/1]



def sel_parse(browser, url):
    browser.get(url) # Gets the url and automatically waits for page to load
    html = browser.page_source
    jsonStr = html[84:-20] # Remove first and last part of HTML to only get JSON contents of page
    json1 = util.read_json(jsonStr)
    postInfo = json1['items'][0]['location']
    name = postInfo['name']

    posts = []
    for i in range(len(postsJSON)):
        id = postsJSON[i]['node']['id']
        shortCode = postsJSON[i]['node']['shortcode']
        ownerId = postsJSON[i]['node']['owner']['id']
        likes = postsJSON[i]['node']['edge_liked_by']['count']
        timeStamp = postsJSON[i]['node']['taken_at_timestamp']
        caption = postsJSON[i]['node']['edge_media_to_caption']['edges']
        tags = []
        if len(caption) > 0:
            caption = caption[0]['node']['text']
            tags = util.desc_to_tags(caption)
            caption = caption.replace('\n', "<br>").replace('\r', "<br>")
        else:
            caption = ""
        post = Post(id, shortCode, ownerId, likes, timeStamp, tags, caption)
        posts.append(post)
    
    endCursor = json1["data"]["hashtag"]["edge_hashtag_to_media"]["page_info"]["end_cursor"]
    
    return posts


# Function that does everything related to selenium (opens browser, logs in, reads posts under tags, closes browser)
# Returns a list of all post objects found under the given tag, the first endCursor, and the final endCursor
def selenium(request):
    print("Tag: ", request.tag)
    print("Number of entries: " + str(request.numPages))
    browser = webdriver.Chrome(executable_path="../chromedriver.exe")
    sel_login(browser)
    time.sleep(5) # wait for login to complete

    allPosts = []
    firstCursor = "[None]"
    lastCursor = "[None]"

    for i in range(request.numPages):
        print("Parsing page " + str((i+1)))
        url = util.make_url(request.tag, MAX_POSTS_PER_PAGE, request.endCursor)
        posts, endCursor, morePages = sel_parse(browser, url)
        allPosts.extend(posts)
        if morePages == False:
            print("No more pages")
            break

        lastCursor = endCursor
        request.endCursor = endCursor
        if i == 0:
            firstCursor = endCursor
    
    request.numPages = i + 1


    browser.quit()
    # tags = IP.combine_tags(tags1, tags2)
    return allPosts, firstCursor, lastCursor
