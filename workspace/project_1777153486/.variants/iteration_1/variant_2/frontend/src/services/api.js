import requests
from fastapi import HTTPException, status

API_URL = "http://localhost:8000/api"

def login(username: str, password: str):
    payload = {
        'username': username,
        'password': password
    }
    response = requests.post(f'{API_URL}/auth/login', json=payload)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise HTTPException(status_code=response.status_code, detail="Invalid username or password")

def register(username: str, password: str):
    payload = {
        'username': username,
        'password': password
    }
    response = requests.post(f'{API_URL}/auth/register', json=payload)
    if response.status_code == 201:
        return True
    else:
        raise HTTPException(status_code=response.status_code, detail="Registration failed")

def get_balance(token: str):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(f'{API_URL}/accounts/balance', headers=headers)
    if response.status_code == 200:
        return response.json()['balance']
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch balance")

def deposit(token: str, amount: float):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    payload = {
        'amount': amount
    }
    response = requests.post(f'{API_URL}/transactions/deposit', json=payload, headers=headers)
    if response.status_code == 201:
        return True
    else:
        raise HTTPException(status_code=response.status_code, detail="Deposit failed")

def withdraw(token: str, amount: float):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    payload = {
        'amount': amount
    }
    response = requests.post(f'{API_URL}/transactions/withdraw', json=payload, headers=headers)
    if response.status_code == 201:
        return True
    else:
        raise HTTPException(status_code=response.status_code, detail="Withdrawal failed")

def transfer(token: str, recipient: str, amount: float):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    payload = {
        'recipient': recipient,
        'amount': amount
    }
    response = requests.post(f'{API_URL}/transactions/transfer', json=payload, headers=headers)
    if response.status_code == 201:
        return True
    else:
        raise HTTPException(status_code=response.status_code, detail="Transfer failed")