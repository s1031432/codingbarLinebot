import os, json, requests, random
from utils.getUserMenu import getUserMenu
from utils.getQuestionTemplate import getQuestionTemplate
from utils.getAnswerTemplate import getAnswerTemplate
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, FlexSendMessage, TextSendMessage

load_dotenv()

QUESTION_URL = os.getenv("QUESTION_URL")
GEMINI_APIKEY = os.getenv("GEMINI_APIKEY")
CHANNEL_TOKEN = os.getenv("CHANNEL_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
NOTIFY_TOKEN = os.getenv("NOTIFY_TOKEN")
OWNER_ID = os.getenv("OWNER_USER_ID")

users = []

line_bot_api = LineBotApi(CHANNEL_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
app = Flask(__name__)

# lineBotHeaders = {'Authorization':'Bearer '+'xxx','Content-Type':'application/json'}
# body = {
#     'to':'',
#     'messages':[{
#             'type': 'text',
#             'text': 'Coco'
#         }]
#     }
# # 向指定網址發送 request
# req = requests.request('POST', 'https://api.line.me/v2/bot/message/push',headers=lineBotHeaders,data=json.dumps(body).encode('utf-8'))

@app.route("/", methods=['POST'])
def callback():
    # 獲取簽名
    signature = request.headers['X-Line-Signature']

    # 獲取請求正文
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 處理 webhook 正文
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'
# get user info
def getUserInfo(event):
    user = {}
    userInfoUrl = "https://api.line.me/v2/bot/profile/{}".format(event.source.user_id)
    userInfo = requests.get(userInfoUrl, headers={'Authorization': "Bearer {}".format(CHANNEL_TOKEN)})
    user = json.loads(userInfo.text)
    user["id"] = event.source.user_id
    user["message"] = event.message.text
    user["step"] = "default"
    user["exam"] = {
        "id": 0,
        "answer": "",
        "option": "",
        "correct_count": 0,
        "incorrect_count": 0 
    }
    user["distUserId"] = ""
    return user
users= {}
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global users
    userId = event.source.user_id
    if userId not in users:
        users[userId] = getUserInfo(event)
    else:
        users[userId]["message"] = event.message.text
    if users[userId]["step"] == "waitingMsg":
        users[userId]["step"] = "default"
        try:
            line_bot_api.push_message(users[userId]["distUserId"], TextSendMessage(text=users[userId]["message"]))
            replyMessage = TextSendMessage("傳送成功")
        except Exception as error:
            replyMessage = TextSendMessage("傳送失敗")
    # show user list who talked to linebot
    else:
        if users[userId]["message"] == "exam":
            # get question from Google Sheet. 'q=3' means retrieving the question with the number 3.
            result = requests.get(QUESTION_URL+"?q=3")
            result = json.loads(result.text)
            questionFlexMsg = FlexSendMessage(
                alt_text = "flex message",
                contents = getQuestionTemplate(result[0])
            )
            line_bot_api.reply_message(event.reply_token, questionFlexMsg)
            # set the user's status to 'exam'.
            users[userId]["step"] = "exam"
            # store exam infomation
            users[userId]["exam"]["id"] = result[0]["id"]
            users[userId]["exam"]["question"] = result[0]["question"]
            users[userId]["exam"]["answer"] = result[0]["answer"]
            users[userId]["exam"]["option"] = result[0]["option_"+result[0]["answer"].lower()]
            users[userId]["exam"]["reference"] = result[0]["reference"]
            users[userId]["exam"]["correct_count"] = result[0]["correct_count"]
            users[userId]["exam"]["incorrect_count"] = result[0]["incorrect_count"]

        elif users[userId]["step"] == "exam":
            users[userId]["step"] = "default"
            if any(char in users[userId]["message"] for char in ['A', 'B', 'C', 'D']):
                answerFlexMsg = FlexSendMessage(
                    alt_text = "flex message",
                    contents = getAnswerTemplate(users[userId])
                )
                line_bot_api.reply_message(event.reply_token, answerFlexMsg)
                ## update correct or incorrect count
                data = {
                    "id": users[userId]["exam"]["id"],
                    "isCorrect": users[userId]["exam"]["answer"] == users[userId]["message"]
                }
                requests.post(QUESTION_URL, data=json.dumps(data), headers={'Content-Type': 'application/json'})
            else:
                invalidMsg = TextSendMessage("回答格式錯誤，請點擊按鈕答題")
                line_bot_api.reply_message(event.reply_token, invalidMsg)
            

        elif users[userId]["id"] == OWNER_ID and users[userId]["message"] == "Send Text":
            userListFlexMsg = FlexSendMessage(
                alt_text = "flex message",
                contents = getUserMenu(users)
            )
            line_bot_api.reply_message(event.reply_token, userListFlexMsg)
        # if user text starts with userId, send customized message
        elif users["message"][0]=="U" and len(user["message"])==33:
            users[userId]["distUserId"] = users[userId]["message"]
            users[userId]["step"] = "waitingMsg"
            userDisplayName = ""
            for user in users:
                if users[userId]["message"] == users[userId]["id"]:
                    userDisplayName = users[userId]["displayName"]
                    break
            replyMessage = TextSendMessage("你想傳給{}什麼訊息呢?".format(userDisplayName))
        else:
            response = SendTextztoGemini(users[userId]["message"])
            geminiResponseString = response["candidates"][0]["content"]["parts"][0]["text"]
            notifySendMessage("User Name: "+ users[userId]['displayName'] +'\n'+'UserId: '+users[userId]["id"]+'\n'\
                            +"Gemini Reply:" + response["candidates"][0]["content"]["parts"][0]["text"]
                        )
            replyMessage = TextSendMessage(geminiResponseString)
    
    # line_bot_api.reply_message(event.reply_token, replyMessage)
    # requests.get(gasNotifyUrl+"?msg="+user["displayName"]+"："+event.message.text, headers={"Authorization": 'Bearer X5TEgso9iQq5lptU259mb3TD8xidwRSSfc3hSQwiJwv'})
    ### fetch data
    
    
    # print('\n'+"Request"+'\n')
    # print(response)
    # sendNotify("{}: {}\nGemini: {}".format(user["displayName"], event.message.text, ))
    # 只取出文字回覆的部分，並透過TextSendMessage這個Function包成Line的訊息回覆格式
   
     # 回覆訊息
    
    

def notifySendMessage(message):
    notifyHeaders =  {'Authorization':'Bearer '+ NOTIFY_TOKEN,'Content-Type':'application/x-www-form-urlencoded'}
    notifyBody = "message="+ message
    req = requests.request('POST', 'https://notify-api.line.me/api/notify',headers=notifyHeaders, data=notifyBody)

def SendTextztoGemini(message):
    message = {"contents":[{"parts":[{"text":message}]}]}
    # 將要傳給Gemini的訊息，依照Gemini的API格式包好
    gemini_data = json.dumps(message)
    # result是Gemini給我們的回應，是一個Object
    gemini_response = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key="+GEMINI_APIKEY, headers={"Content-Type": "application/json"}, data=gemini_data)
    result = json.loads(gemini_response.text)
    return result
if __name__ == "__main__":
    app.run(debug=True, port=5000)