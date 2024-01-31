import json 

with open('user.json') as content:
    file = json.load(content)

print(file)