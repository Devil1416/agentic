import requests
from fastapi import HTTPException, status

API_URL = 'http://localhost:8000/'

def login(username: str, password: str):
    url = API_URL + 'auth/login'
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise HTTPException(status_code=response.status_code, detail='Invalid username or password')

def register(username: str, password: str):
    url = API_URL + 'auth/register'
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(url, json=data)
    if response.status_code == 201:
        return True
    else:
        raise HTTPException(status_code=response.status_code, detail='Registration failed')

def get_balance(token: str):
    url = API_URL + 'accounts/balance'
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['balance']
    else:
        raise HTTPException(status_code=response.status_code, detail='Failed to fetch balance')

def deposit(token: str, amount: float):
    url = API_URL + 'transactions/deposit'
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "amount": amount
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        return True
    else:
        raise HTTPException(status_code=response.status_code, detail='Deposit failed')

def withdraw(token: str, amount: float):
    url = API_URL + 'transactions/withdraw'
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "amount": amount
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        return True
    else:
        raise HTTPException(status_code=response.status_code, detail='Withdrawal failed')

def transfer(token: str, receiver: str, amount: float):
    url = API_URL + 'transactions/transfer'
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "receiver": receiver,
        "amount": amount
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        return True
    else:
        raise HTTPException(status_code=response.status_code, detail='Transfer failed')