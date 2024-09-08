import json

def getUserMenu(userList):
    # Open and read the JSON file
    with open('./assets/json/userList.json', 'r') as file:
        data = json.load(file)
    # read elements in userList
    for user in userList:
        button = {'type': 'button', 'style': 'primary', 'height': 'sm', 'action': {'type': 'message', 'label': 'action', 'text': 'userID:0000'}}
        button["action"]["label"] = user["displayName"]
        button["action"]["text"] = user["userId"]
        data["footer"]["contents"].append(button)

    # Print the data
    print(data)
    return data

# getUserMenu([{"displayName":"tim","userId":"12345678"},{"displayName":"Jane","userId":"761829"},{"displayName":"Ketty","userId":"927391"}])