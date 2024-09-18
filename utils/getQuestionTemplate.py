import json
def getQuestionTemplate(question):
    with open('./assets/json/question.json', 'r', encoding="utf-8") as file:
        data = json.load(file)
        data = json.dumps(data)
        data = data.replace("$question",question["question"] )
        data = data.replace("$subject",question["subject"] )
        data = data.replace("$optionA","A. "+question["option_a"] )
        data = data.replace("$optionB","B. "+question["option_b"] )
        data = data.replace("$optionC","C. "+question["option_c"] )
        data = data.replace("$optionD","D. "+question["option_d"] )
        data = data.replace("$reference",question["reference"] )
        data = data.replace("$contributor",question["contributor"] )
        data = json.loads(data)
    return data