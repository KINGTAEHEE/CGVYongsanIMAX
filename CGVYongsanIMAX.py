import ntplib
import requests
import telegram
from telegram.error import RetryAfter
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from time import ctime, timezone
from time import sleep

def Checker(date):
    global bot
    global listData
    listData2 = list() # 이전 정보를 가지고있는 listData와 비교할 리스트
    url = "http://www.cgv.co.kr/common/showtimes/iframeTheater.aspx?areacode=01&theatercode=0013&date=" + date.strftime("%Y%m%d")
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    targetDate = soup.select("body > div.showtimes-wrap > div.sect-schedule > div.slider > div.item-wrap > ul.item > li.on > div.day > a")
    if len(targetDate) == 0: # 만약 값을 가져오지 못했을 경우 넘어간다(서버 오류나 페이지 정보 잘못된 경우)
        return
    if targetDate[0].attrs['href'][55:63] != date.strftime("%Y%m%d"): # 날짜가 맞는지 비교하고 다르면 넘어간다(예매오픈 안된 날짜면 오늘날짜로 자동 리다이렉션 됨)
        return
    countMovie = len(soup.select("body > div > div.sect-showtimes > ul > li"))
    i = 1
    while i <= countMovie: # 상영작 리스트 확인
        movieName = soup.select("body > div > div.sect-showtimes > ul > li:nth-child({0}) > div > div.info-movie > a > strong".format(i))
        countHall = int(len(soup.select("body > div > div.sect-showtimes > ul > li:nth-child({0}) > div > div.type-hall > div.info-hall > ul".format(i))))
        j = 1
        while j <= countHall: # 선택된 상영작의 상영관 확인
            dubbingCheck = ""
            hallList = soup.select("body > div > div.sect-showtimes > ul > li:nth-child({0}) > div > div:nth-child({1}) > div.info-hall > ul > li:nth-child(1)".format(i, j + 1))
            if "IMAX" in hallList[0].text.strip():
                dubbing = soup.select("body > div > div.sect-showtimes > ul > li:nth-child({0}) > div > div:nth-child({1}) > div.info-hall > ul > li:nth-child(1)".format(i, j + 1))
                if "더빙" in dubbing[0].text.strip():
                    dubbingCheck = "(더빙)"
                else:
                    dubbingCheck = ""
                countTime = int(len(soup.select("body > div > div.sect-showtimes > ul > li:nth-child({0}) > div > div:nth-child({1}) > div.info-timetable > ul > li".format(i, j + 1))))
                listTime = list()
                k = 1
                while k <= countTime: # 선택된 상영관의 시간표 확인
                    timeTable = soup.select("body > div > div.sect-showtimes > ul > li:nth-child({0}) > div > div:nth-child({1}) > div.info-timetable > ul > li:nth-child({2}) > a > em".format(i, j + 1, k))
                    if int(len(timeTable)) == 0:
                        k = k + 1
                    else:
                        listTime.append(timeTable[0].text.strip())
                        k = k + 1
                if len(listTime) != 0: # 상영 시간표가 존재하면 listData2 리스트에 추가한다
                    listData2.append([date.strftime("%Y%m%d"), movieName[0].text.strip(), hallList[0].text.strip() + dubbingCheck, listTime]) # 제목, 상영관, 시간표 정보를 리스트에 담는다
            # elif "4DX" in hallList[0].text.strip():
            #     dubbing = soup.select("body > div > div.sect-showtimes > ul > li:nth-child({0}) > div > div:nth-child({1}) > div.info-hall > ul > li:nth-child(1)".format(i, j + 1))
            #     if "더빙" in dubbing[0].text.strip():
            #         dubbingCheck = "(더빙)"
            #     else:
            #         dubbingCheck = ""
            #     countTime = int(len(soup.select("body > div > div.sect-showtimes > ul > li:nth-child({0}) > div > div:nth-child({1}) > div.info-timetable > ul > li".format(i, j + 1))))
            #     listTime = list()
            #     k = 1
            #     while k <= countTime: # 선택된 상영관의 시간표 확인
            #         timeTable = soup.select("body > div > div.sect-showtimes > ul > li:nth-child({0}) > div > div:nth-child({1}) > div.info-timetable > ul > li:nth-child({2}) > a > em".format(i, j + 1, k))
            #         if int(len(timeTable)) == 0:
            #             k = k + 1
            #         else:
            #             listTime.append(timeTable[0].text.strip())
            #             k = k + 1
            #     if len(listTime) != 0: # 상영 시간표가 존재하면 listData2 리스트에 추가한다
            #         listData2.append([date.strftime("%Y%m%d"), movieName[0].text.strip(), hallList[0].text.strip() + dubbingCheck, listTime]) # 제목, 상영관, 시간표 정보를 리스트에 담는다
            j = j + 1
        i = i + 1

    if len(listData) == 0: # 처음 실행하여 리스트가 비어있으면 listData2를 옮겨담는다
        messageQueue = "" # 봇 메시지 큐
        listData = listData2
        for data in listData:
            messageQueue = messageQueue + listData[0][0] + " CGV용산아이파크몰" + "\n"
            messageQueue = messageQueue + "[" + data[1] + "]" + "\n"
            messageQueue = messageQueue + data[2] + "\n"
            for time in data[3]:
                messageQueue = messageQueue + time + " "
            print(messageQueue)
            try:
                bot.sendMessage(chat_id=chat_id, text=messageQueue)
            except RetryAfter:
                print("[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] 텔레그램 봇 API RetryAfter 발생! 1분 대기합니다")
                sleep(60)
                bot.sendMessage(chat_id=chat_id, text=messageQueue)
            messageQueue = ""
    else: # 이번에 읽은 정보 리스트(listData2)를 기존 저장된 정보 리스트(listData)와 비교한다
        messageQueue = "" # 봇 메시지 큐
        compareDate = list()
        compareName = list()
        compareHall = list()
        compareTime = list()
        for data2 in listData2:
            if data2 not in listData: # 날짜, 제목, 상영관, 시간표 중 하나라도 다를 경우
                for i in range(0, len(listData)): # 날짜 비교
                    if data2[0] == listData[i][0]:
                        compareDate.append("같음")
                    else:
                        compareDate.append("다름")
                for i in range(0, len(listData)): # 제목 비교
                    if data2[1] == listData[i][1]:
                        compareName.append("같음")
                    else:
                        compareName.append("다름")
                for i in range(0, len(listData)): # 상영관 비교
                    if data2[2] == listData[i][2]:
                        compareHall.append("같음")
                    else:
                        compareHall.append("다름")
                for i in range(0, len(listData)): # 날짜,제목,상영관 일치 여부 비교
                    if compareDate[i] == "같음" and compareName[i] == "같음" and compareHall[i] == "같음": # 시간표가 다른 경우
                        compareTime.append("같음")
                    else:
                        compareTime.append("다름")
                if "같음" in compareTime:
                    for i in range(0, len(compareTime)):
                        if compareTime[i] == "같음":
                            for j in range(0, len(data2[3])):
                                if data2[3][j] not in listData[i][3]: # 현재 시간표 중 기존 시간표에 없던 시간이 있으면 전체 덮어쓴다(추가예매 오픈)
                                    listData[i][3] = data2[3]
                                    messageQueue = messageQueue + listData[i][0] + " CGV용산아이파크몰" + "\n"
                                    messageQueue = messageQueue + "[" + listData[i][1] + "]" + "\n"
                                    messageQueue = messageQueue + listData[i][2] + " 추가예매 오픈" + "\n"
                                    for time in listData[i][3]:
                                        messageQueue = messageQueue + time + " "
                                    print(messageQueue)
                                    try:
                                        bot.sendMessage(chat_id=chat_id, text=messageQueue)
                                    except RetryAfter:
                                        print("[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] 텔레그램 봇 API RetryAfter 발생! 1분 대기합니다")
                                        sleep(60)
                                        bot.sendMessage(chat_id=chat_id, text=messageQueue)
                                    messageQueue = ""
                                    break
                else: # 하나라도 다르면 새로 추가한다
                    listData.append(data2)
                    messageQueue = messageQueue + data2[0] + " CGV용산아이파크몰" + "\n"
                    messageQueue = messageQueue + "[" + data2[1] + "]" + "\n"
                    messageQueue = messageQueue + data2[2] + "\n"
                    for time in data2[3]:
                        messageQueue = messageQueue + time + " "
                    print(messageQueue)
                    try:
                        bot.sendMessage(chat_id=chat_id, text=messageQueue)
                    except RetryAfter:
                        print("[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] 텔레그램 봇 API RetryAfter 발생! 1분 대기합니다")
                        sleep(60)
                        bot.sendMessage(chat_id=chat_id, text=messageQueue)
                    messageQueue = ""
                compareDate = []
                compareName = []
                compareHall = []
                compareTime = []

# if __name__ == '__main__':
c = ntplib.NTPClient()
response = c.request("time.windows.com", version=3)
response.offset
date = datetime.fromtimestamp(response.tx_time)
bot = telegram.Bot(token="*") # 봇 token
chat_id = "*" # 채팅방 ID
listData = list() # 상영 정보를 담을 리스트
Checker(date) # 처음 상영 정보를 담기 위해 오늘자로 우선 실행한다
while True: # 이후 무한 반복
    i = 0
    j = 0
    while i <= 30:
        try:
            date = date + timedelta(days=1)
            Checker(date)
            i = i + 1
        except:
            print("[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] Error 발생! 10분 대기합니다")
            sleep(10 * 60) # 10분 대기
    date = datetime.fromtimestamp(response.tx_time) # 오늘자로 다시 초기화
    while j < len(listData): # 지나간 날짜의 상영 정보는 리스트에서 삭제한다
        try:
            if int(listData[j][0]) < int(date.strftime("%Y%m%d")):
                del listData[j]
            else:
                j = j + 1
        except:
            break
    sleep(10) # 30일치 확인이 끝나면 10초 대기한다
