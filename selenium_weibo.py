import os
import time
import datetime
from random import random

import sqlite3
from selenium import webdriver

# open weibo.cn
driver = webdriver.Chrome('/Users/wangqin/code/PycharmProjects/weibo_covid19/chromedriver')
# driver.maximize_window()
driver.get("https://weibo.cn/")
driver.find_element_by_xpath('/html/body/div[2]/div/a[1]').click()

# login: manual operation needed
time.sleep(2)

username = str(os.environ.get('WEIBO_USERNAME'))
password = str(os.environ.get('WEIBO_PASSWORD'))

driver.find_elements_by_id('loginName')[0].send_keys(username)
driver.find_elements_by_id('loginPassword')[0].send_keys(password)
driver.find_elements_by_id('loginAction')[0].click()
time.sleep(10)

# set date iteration
start_date = datetime.date(2020, 3, 21)
end_date = datetime.date(2020, 5, 15)
delta = datetime.timedelta(days=1)

# setup database connection
con = sqlite3.connect('weibo_COVID19.db')
cursorObj = con.cursor()
sql_create_posts_table = 'Create TABLE IF NOT EXISTS posts ' \
                         '(post_id TEXT, post_content TEXT, post_time TEXT, like_count TEXT, ' \
                         'comments_count TEXT, repost_count TEXT, user_id TEXT, username TEXT);'
cursorObj.execute(sql_create_posts_table)

while start_date <= end_date:
    search_keys = ['新冠', '疫情', '肺炎']  # '新冠',
    for search_key in search_keys:
        search_date = start_date.strftime("%Y%m%d")
        start_date += delta

        driver.get('https://weibo.cn/search/mblog?advanced=mblog&f=s')
        driver.find_element_by_name('keyword').send_keys(search_key)
        driver.find_element_by_name('hasori').click()
        driver.find_element_by_name('starttime').clear()
        driver.find_element_by_name('starttime').send_keys(search_date)
        driver.find_element_by_name('endtime').clear()
        driver.find_element_by_name('endtime').send_keys(search_date)
        driver.find_element_by_xpath('/html/body/div[6]/form/div/input[13]').click()
        driver.find_element_by_name('smblog').click()

        backoff_attempted = 0

        while True:
            time.sleep(1 + random() * 3)

            if len(driver.find_elements_by_partial_link_text('赞[')) != 0:
                backoff_attempted = 0

                # get content
                post_content_list = driver.find_elements_by_class_name('ctt')
                content_list = [post_content.text for post_content in post_content_list]

                # get user_id & username
                user_list = driver.find_elements_by_class_name('nk')
                user_id_list = [user.get_attribute('href')[16:] for user in user_list]
                username_list = [user.text for user in user_list]

                # get attitude_num
                attitude_list = driver.find_elements_by_partial_link_text('赞[')
                attitude_num_list = [attitude.text[2:-1] for attitude in attitude_list]
                post_id_list = [a.get_attribute('href').split('/')[4] for a in attitude_list]

                # get repost_num
                repost_list = driver.find_elements_by_partial_link_text('转发[')
                repost_num_list = [repost.text[3:-1] for repost in repost_list]

                # get comment_num & post_id
                comment_list = driver.find_elements_by_partial_link_text('评论[')
                comment_num_list = [comment_num.text[3:-1] for comment_num in comment_list]

                for i in range(len(post_id_list)):
                    post_id = (post_id_list[i],)
                    cursorObj.execute('SELECT post_id FROM posts WHERE post_id = ?', post_id)
                    if not cursorObj.fetchone():
                        values = (post_id_list[i], content_list[i], search_date, attitude_num_list[i],
                                  comment_num_list[i], repost_num_list[i], user_id_list[i], username_list[i])
                        sql = 'INSERT INTO posts VALUES(?,?,?,?,?,?,?,?)'
                        print(values)
                        cursorObj.execute(sql, values)
                    else:
                        print('post_id',post_id[0], 'collected.')
                con.commit()
            else:
                if backoff_attempted == 0:
                    backoff_attempted += 1
                    print('Empty page for', search_key, str(search_date), 'at page',
                          str(curr_page) + ', backoff for 5 seconds.')
                    driver.back()
                    time.sleep(5)
                elif backoff_attempted == 1:
                    backoff_attempted += 1
                    if curr_page:
                        driver.back()
                        time.sleep(1)
                        driver.find_element_by_xpath('//*[@id="pagelist"]/form/div/input[2]').send_keys(str(int(curr_page) + 2))
                        print('Empty page twice for', search_key, str(search_date), 'at page',
                              str(curr_page) + ', jump to next page.')
                else:
                    backoff_attempted = 0
                    print('Empty page third time for', search_key, str(search_date), 'at page',
                          str(curr_page) + ', start new search.')
                    break

            curr_page, total_page = driver.find_element_by_xpath('//*[@id="pagelist"]/form/div').text.split(' ')[-1][
                                    :-1].split('/')
            if curr_page == total_page:
                break

            driver.find_element_by_link_text('下页').click()

con.close()
