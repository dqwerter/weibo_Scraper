import sqlite3

con = sqlite3.connect('weibo_COVID19.db')
cursorObj = con.cursor()
cursorObj.execute('SELECT post_id FROM posts WHERE post_id = ?', ('InnCfoT',))

if cursorObj.fetchone():
    print('yes')
else:
    print('no')
