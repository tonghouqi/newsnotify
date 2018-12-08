# -- coding: utf-8 --
"""
采集同花顺的7*24小时财经消息/采集东方财富7*24小时
1:使用requests.get采集同花顺的时候，必须使用headers
2：返回的字段不规范的字典形式，key没有引号，导致json.loads的时候报错，这个需要引用demjson包。另外如果key
   value都是单引号，可以使用ast包（同花顺才这样）

"""
from win32api import *
from win32gui import *
import win32con
import sys, os
import struct
import time
import requests
from bs4 import BeautifulSoup
import demjson

# Class
class WindowsBalloonTip:
    def __init__(self, title, msg):
        message_map = { win32con.WM_DESTROY: self.OnDestroy,}

        # Register the window class.
        wc = WNDCLASS()
        hinst = wc.hInstance = GetModuleHandle(None)
        wc.lpszClassName = 'PythonTaskbar'
        wc.lpfnWndProc = message_map # could also specify a wndproc.
        classAtom = RegisterClass(wc)

        # Create the window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = CreateWindow(classAtom, "Taskbar", style, 0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0, hinst, None)
        UpdateWindow(self.hwnd)

        # Icons managment
        iconPathName = os.path.abspath(os.path.join( sys.path[0], 'balloontip.ico' ))
        icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
        try:
            hicon = LoadImage(hinst, iconPathName, win32con.IMAGE_ICON, 0, 0, icon_flags)
        except:
            hicon = LoadIcon(0, win32con.IDI_APPLICATION)
        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER+20, hicon, u'国投财经7*24时直播')

        # Notify
        Shell_NotifyIcon(NIM_ADD, nid)
        Shell_NotifyIcon(NIM_MODIFY, (self.hwnd, 0, NIF_INFO, win32con.WM_USER+20, hicon, 'Balloon Tooltip', msg, 800, title))
        # self.show_balloon(title, msg)
        time.sleep(10)

        # Destroy
        DestroyWindow(self.hwnd)
        classAtom = UnregisterClass(classAtom, hinst)
    def OnDestroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        Shell_NotifyIcon(NIM_DELETE, nid)
        PostQuitMessage(0) # Terminate the app.

# Function
def balloon_tip(title, msg):
    w=WindowsBalloonTip(title, msg)

# Main
if __name__ == '__main__':
    ids = ids2 = []
    count = count2 = 0

    while True:
        #东方财富
        dongfang = requests.get('http://kuaixun.eastmoney.com/')
        #print dongfang.text
        soup = BeautifulSoup(dongfang.text, "lxml")
        for item in soup.find(id='livenews-list').children:
            idnum = item.get('id')
            if idnum not in ids:
                starttime = item.find(class_ = 'time').text
                mediatitle = item.find(class_ = 'media-title').text
                href = item.find('a',href=True)
                hrefcont = ""
                if not href is None:
                    hrefcont = u" " + href['href']
                weibotext = starttime + "  " + mediatitle + "  "+hrefcont
                if count > 0:
                    balloon_tip( u'深圳国投财经7*24直播：', weibotext)
                    print weibotext
                    file = open(str(time.strftime('%Y-%m-%d',time.localtime(time.time())))+".txt",'a+')
                    file.writelines(weibotext.encode('utf-8')+"\n")
                    file.close()
                ids.append(idnum)


        #同花顺7*24小时
        #unix时间戳13位
        millis = int(round(time.time() * 1000))
        tempURL = "http://stock.10jqka.com.cn/thsgd/realtimenews.js?_="+str(millis)
        #设置request headers，必须设置headers，不然会被禁止
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Host": "stock.10jqka.com.cn",
            "Referer": "http://news.10jqka.com.cn/realtimenews.html",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
        }
        ret_data = requests.get(tempURL,headers=headers)
        #print ret_data.text
        rawdata = ret_data.text.encode('utf-8').split("thsRss =")[1].split(";\nif ( typeof")[0]
        rawdata = demjson.decode(rawdata)

        data = rawdata["item"]
        for item in data:
            idnum2 = item['seq']
            if idnum2 not in ids2:
                starttime = item['pubDate'].split(' ')[1]
                content = item['content']
                source = item['source']
                if source != "":
                    news = starttime + "  (" + source + ")" + content
                else:
                    news = starttime + "  " + content
                if count2 > 0:
                    balloon_tip( u'深圳国投财经7*24直播：', news)
                    print news
                    file = open(str(time.strftime('%Y-%m-%d', time.localtime(time.time()))) + ".txt", 'a+')
                    file.writelines(news.encode('utf-8') + "\n")
                    file.close()
                ids2.append(idnum2)

        if len(ids) > 5000: ids = []
        if len(ids2) > 5000:ids2 = []
        if count > 30000:count = 1
        if count2 > 30000:count2 = 1
        count = count + 1
        count2 = count2 + 1
        time.sleep(10)
