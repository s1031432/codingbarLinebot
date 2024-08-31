import os, json, requests, random
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
# your line user id 
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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    # get user info
    userInfoUrl = "https://api.line.me/v2/bot/profile/{}".format(user_id)
    userInfo = requests.get(userInfoUrl, headers={'Authorization': "Bearer {}".format(CHANNEL_TOKEN)})
    user = json.loads(userInfo.text)
    userMessage = event.message.text
    if user not in users:
        users.append(user)
    
    # show user list who talked to linebot
    if user["userId"] == OWNER_ID and userMessage == "Send Text":
        userIdStr = ""
        for user in users :
            for i in range(-4,0):
                userIdStr+= user["userId"][i]
            userIdStr += (' '+ user["displayName"]+'\n')
        replyMessage = userIdStr
    # if user text starts with userId, send customized message
    elif user["userId"] == OWNER_ID and userMessage[0:4].isalnum():
        ownerMessage = userMessage[5:-1]
        for user in users:
            if user["userId"][29:33] == userMessage[0:4]:
                receiveUser = user["userId"]
                break
        line_bot_api.push_message(receiveUser, TextSendMessage(text=ownerMessage))
        replyMessage = "done!" 
    else:
        response = SendTextztoGemini(userMessage)
        geminiResponseString = response["candidates"][0]["content"]["parts"][0]["text"]
        notifySendMessage("User Name: "+ user['displayName'] +'\n'+'UserId: '+user['userId']+'\n'\
                        +"Gemini Reply:" + response["candidates"][0]["content"]["parts"][0]["text"]
                      )
        replyMessage = geminiResponseString
    text_message = TextSendMessage(replyMessage)
    line_bot_api.reply_message(event.reply_token, text_message)
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