import requests
from fastapi import HTTPException, status

API_URL = "http://localhost:8000/api"

def login(username: str, password: str):
    url = f'{API_URL}/auth/login'
    data = {
        'username': username,
        'password': password
    }
    response = requests.post(url, json=data)
    
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect username or password')
        
    return response.json()

def register(username: str, password: str):
    url = f'{API_URL}/auth/register'
    data = {
        'username': username,
        'password': password
    }
    response = requests.post(url, json=data)
    
    if response.status_code != 201:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Username already exists')
        
    return response.json()

def get_balance(user_id: int):
    url = f'{API_URL}/accounts/{user_id}'
    response = requests.get(url)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail='Error getting balance')
        
    return response.json()['balance']

def deposit(user_id: int, amount: float):
    url = f'{API_URL}/transactions/deposit/{user_id}'
    data = {
        'amount': amount
    }
    response = requests.post(url, json=data)
    
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail='Error depositing funds')
        
    return response.json()['balance']

def withdraw(user_id: int, amount: float):
    url = f'{API_URL}/transactions/withdraw/{user_id}'
    data = {
        'amount': amount
    }
    response = requests.post(url, json=data)
    
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail='Error withdrawing funds')
        
    return response.json()['balance']

def transfer(sender_id: int, receiver_id: int, amount: float):
    url = f'{API_URL}/transactions/transfer/{sender_id}'
    data = {
        'receiver': receiver_id,
        'amount': amount
    }
    response = requests.post(url, json=data)
    
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail='Error transferring funds')
        
    return response.json()['balance']