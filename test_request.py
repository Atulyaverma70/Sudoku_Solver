import requests

url = "http://127.0.0.1:5000/solve"
data = {
    "grid": [
        [5,3,0,0,7,0,0,0,0], 
        [6,0,0,1,9,5,0,0,0], 
        [0,9,8,0,0,0,0,6,0], 
        [8,0,0,0,6,0,0,0,3], 
        [4,0,0,8,0,3,0,0,1], 
        [7,0,0,0,2,0,0,0,6], 
        [0,6,0,0,0,0,2,8,0], 
        [0,0,0,4,1,9,0,0,5], 
        [0,0,0,0,8,0,0,7,9]
    ]
}

response = requests.post(url, json=data)
print(response.json())  # Print the output
