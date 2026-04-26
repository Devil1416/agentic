import requests
from fastapi import HTTPException, status

API_URL = "http://localhost:8000/api"

def login(username: str, password: str):
    data = {
        'username': username,
        'password': password
    }
    response = requests.post(f'{API_URL}/auth/login', json=data)
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    return response.json()

def register(username: str, password: str):
    data = {
        'username': username,
        'password': password
    }
    response = requests.post(f'{API_URL}/auth/register', json=data)
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail="Registration failed")
    return response.json()

def get_balance(token: str):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(f'{API_URL}/accounts/balance', headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to get balance")
    return response.json()

def deposit(token: str, amount: float):
    data = {
        'amount': amount
    }
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.post(f'{API_URL}/transactions/deposit', json=data, headers=headers)
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail="Deposit failed")
    return response.json()

def withdraw(token: str, amount: float):
    data = {
        'amount': amount
    }
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.post(f'{API_URL}/transactions/withdraw', json=data, headers=headers)
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail="Withdrawal failed")
    return response.json()

def transfer(token: str, recipient: str, amount: float):
    data = {
        'recipient': recipient,
        'amount': amount
    }
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.post(f'{API_URL}/transactions/transfer', json=data, headers=headers)
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail="Transfer failed")
    return response.json()