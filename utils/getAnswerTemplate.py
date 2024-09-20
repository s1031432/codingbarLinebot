import json
def getAnswerTemplate(user):
    with open('./assets/json/answer.json', 'r', encoding="utf-8") as file:
        data = json.load(file)
        data = json.dumps(data)
        data = data.replace( "$question", user["exam"]["question"] )
        if user["exam"]["answer"] == user["message"]:
            data = data.replace( "$answer", "答對了！答案是\\n {}. {}".format( user["exam"]["answer"], user["exam"]["option"] ) )
            user["exam"]["correct_count"] += 1
        else:
            data = data.replace( "$answer", "答錯了！答案是\\n{}. {}".format( user["exam"]["answer"], user["exam"]["option"] ) )
            user["exam"]["incorrect_count"] += 1
        data = data.replace( "$correct", str(user["exam"]["correct_count"]) )
        data = data.replace( "$incorrect", str(user["exam"]["incorrect_count"]) )
        data = data.replace( "$reference", str(user["exam"]["reference"]) )
        data = json.loads(data)
    return data