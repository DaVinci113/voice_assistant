import requests


url = "http://192.168.0.2:1234"
models = "/api/v1/models"
chat = "/api/v1/chat"
query = input("INPUT TEXT: ")
json = {
    "model": "qwen/qwen3-vl-4b",
    "input": query,
}
response = requests.post(url+chat, json=json)
print(response.json())