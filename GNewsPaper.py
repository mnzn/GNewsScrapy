import newspaper
import pymongo
from deep_translator import (GoogleTranslator,
                             ChatGptTranslator,
                             MicrosoftTranslator,
                             PonsTranslator,
                             LingueeTranslator,
                             MyMemoryTranslator,
                             YandexTranslator,
                             PapagoTranslator,
                             DeeplTranslator,
                             QcriTranslator,
                             single_detection,
                             batch_detection)
import time
import os, sys
import requests

client = pymongo.MongoClient('localhost', 27017)
db = client["gnews"]
headlines_collection = db["headlines"]
articles_collection = db["Post"]

my_translator = GoogleTranslator(source='auto', target='zh-CN')

def GT(text, batch=False):
    time.sleep(3)
    if batch:
        #print("list len:", len(text))
        words = 0;
        for x in text:
            words += len(x)
        if words < 5000:
            return my_translator.translate_batch(text)
        words = 0
        tmp = []
        index = 0
        for x in text:
            words += len(x)
            tmp.append(x)
            index += 1
            if words > 4500:
                break
        if words>=5000:
            tmp.pop()
            index -= 1
        return GT(tmp, True) + GT(text[index:], True)
    else:
        return my_translator.translate(text=text)

def save_article(x, a):
    path = "/root/GNewsFront/public/news_resource/pics/"+x['link_hash']
    if not os.path.exists(path):
        os.mkdir(path, 0o666)
    if not os.path.exists(path+"/figure.webp"):
        if x['figure'] is not None:
            data = requests.get(x['figure'], timeout=(5,5)).content
            if data is not None:
                with open(path+"/figure.webp", 'wb') as f:
                    f.write(data)
                    f.close()
            else:
                x['figure'] = None

    file = "/root/GNewsFront/public/news_resource/pics/"+x['link_hash']+"/article.html"
    with open(file, "w") as f:
        f.write(a.article_html)
        f.close()

def fetch_img(x, article):
    url = article.top_img
    if url is None or not article.has_top_image():
        return
    file = "/root/GNewsFront/public/news_resource/pics/"+x['link_hash']+"/top_img.jpg"
    try:
        res = requests.get(url, timeout=(5,5))
    except requests.exceptions.RequestException as e:
        print("fetch top_image timeout", url)
        return False
    if res.status_code == 200:
        with open(file, 'wb') as f:
            f.write(res.content)
            f.close()
        return True
    else:
        return False

def get_icon(x):
    icon = x['icon']
    alt_icon = x['alt_icon']
    icon_title = x['icon_title']

    path = "/root/GNewsFront/public/news_resource/icons/" + icon_title
    if not os.path.exists(path):
        print(icon_title)
        os.makedirs(path, 0o666)

    url = ""
    file = ""
    if icon is not None:
        file = path + "/icon.webp"
        url = icon
    else:
        file = path + "/alt_icon.webp"
        url = alt_icon

    if os.path.exists(file):
        return

    data = requests.get(url, timeout=(5,5)).content
    if data is not None:
        with open(file, 'wb') as f:
            f.write(data)
            f.close()
    else:
        print("get icon failed", url, icon_title)

def split_string(string, length):
    return [string[i:i + length] for i in range(0, len(string), length)]

def get_headline():
    myquery={"downloaded":False,"skip":False}
    c = newspaper.Config()
    c.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    for x in headlines_collection.find(myquery):
        article = newspaper.Article(x['final_link'], keep_article_html=True, config=c)
        try:
            article.download()
            article.parse()
            article.nlp()
        except Exception as e:
            headlines_collection.update_one({"_id":x["_id"]},{"$set":{"skip":True}})
            print("download or update article failed,set skip:", x["final_link"])
            continue


        text_lines_tmp = article.text.splitlines()
        text_lines = []
        #text_lines = [x for x in text_lines if len(x) != 0]
        for i,t in enumerate(text_lines_tmp):
            if len(t) == 0:
                continue
            if len(t)>5000:
                text_lines+=split_string(t, 4900)
            else:
                text_lines.append(t)

        #for i,t in enumerate(text_lines):
        #    print(i,len(t),t)
        if not text_lines:
            headlines_collection.update_one({"_id":x["_id"]},{"$set":{"skip":True}})
            print("text_lines empty,set skip:", x["final_link"], text_lines)
            continue

        #print(x['title'])
        text_lines_cn = GT([x['title']]+text_lines, True)
        #print(text_lines_cn)
        title_cn = text_lines_cn[0]
        del text_lines_cn[0]

        save_article(x, article)

        text = ""
        for l in text_lines:
            text += l
            text += "\n\n"
        text_cn = ""
        for l in text_lines_cn:
            if l is None:
                continue
            text_cn += l
            text_cn += "\n\n"
        #print(text,text_cn)
        has_top_image = fetch_img(x, article)
        get_icon(x)
        a = {
            "figure": "/news_resource/pics/"+x['link_hash']+"/figure.webp" if x['figure'] is not None else None,
            "published": True,
            "title": x['title'],
            "title_cn": title_cn,
            "icon": "/news_resource/icons/" + x['icon_title'] + ("/alt_icon.webp" if x['icon'] is None else "/icon.webp"),
            "time": x['time'],
            "top_image": "/news_resource/pics/"+x['link_hash']+"/top_img.jpg" if article.has_top_image() and has_top_image else None,
            "summary": article.summary,
            "text": text,
            "text_cn": text_cn,
            "url": x['final_link'],
            }
        try:
            articles_collection.insert_one(a)
            headlines_collection.update_one({"_id":x["_id"]},{"$set":{"downloaded":True}})
        except Exception as e:
            print("insert article or update headline failed:", a["url"], str(e))

        print("Inserted one article")
        #break
    #for p in articles_collection.find():
    #    print(p)



get_headline()
client.close()


#docker network create mongoCluster
#docker run --name mongo --network mongoCluster -d --restart unless-stopped -p 127.0.0.1:27017:27017 -v /root/mongo-data/:/data/db mongodb/mongodb-community-server --replSet rs0 --bind_ip localhost,mongo
#docker exec -it mongo mongosh
#db.headlines.createIndex({"final_link":1},{unique:true})
#db.Post.createIndex({"url":1},{unique:true})
#mkdir /root/GNewsFront/public/news_resource/pics/
#mkdir /root/GNewsFront/public/news_resource/icons/
