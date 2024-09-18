import os, json, requests, random
from utils.getUserMenu import getUserMenu
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, FlexSendMessage, TextSendMessage
load_dotenv()


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
#     'to':'U2deac20d8bac62a51ea352713a23f2c9',
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
    user["distUserId"] = ""
    return user
users= {}
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global users
    userId = event.source.user_id
    if userId not in users:
        users[userId] = getUserInfo(event)
    if step == "waitingMsg":
        step = "default"
        try:
            line_bot_api.push_message(users[userId]["distUserId"], TextSendMessage(text=users[userId]["message"]))
            replyMessage = TextSendMessage("傳送成功")
        except Exception as error:
            replyMessage = TextSendMessage("傳送失敗")
    # show user list who talked to linebot
    else:
        if users[userId]["id"] == OWNER_ID and users[userId]["message"] == "Send Text":
            userListFlexMsg = FlexSendMessage(
                alt_text = "flex message",
                contents = getUserMenu(users)
            )
            line_bot_api.reply_message(event.reply_token, userListFlexMsg)
        # if user text starts with userId, send customized message
        elif user["message"][0]=="U" and len(user["message"])==33:
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
    
    line_bot_api.reply_message(event.reply_token, replyMessage)
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