import os

username = str(os.environ.get('WEIBO_USERNAME'))
password = str(os.environ.get('WEIBO_PASSWORD'))
print(username, password)
