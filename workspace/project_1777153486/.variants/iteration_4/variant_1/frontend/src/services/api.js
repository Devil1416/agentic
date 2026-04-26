import requests
from fastapi import HTTPException

API_URL = "http://localhost:8000/api"

def handle_response(res):
    if res.status_code != 200:
        raise HTTPException(status_code=500, detail='Error communicating with the server')
    return res.json()

class ApiService:
    @staticmethod
    def login(username: str, password: str):
        data = { 'username': username, 'password': password }
        res = requests.post(f"{API_URL}/auth/login", json=data)
        return handle_response(res)

    @staticmethod
    def register(username: str, password: str):
        data = { 'username': username, 'password': password }
        res = requests.post(f"{API_URL}/auth/register", json=data)
        return handle_response(res)

    @staticmethod
    def get_accounts():
        res = requests.get(f"{API_URL}/accounts")
        return handle_response(res)

    @staticmethod
    def create_account(userId: int):
        data = { 'owner_id': userId }
        res = requests.post(f"{API_URL}/accounts", json=data)
        return handle_response(res)

    @staticmethod
    def deposit(accountNumber: str, amount: float):
        data = { 'account_number': accountNumber, 'amount': amount }
        res = requests.post(f"{API_URL}/transactions/deposit", json=data)
        return handle_response(res)

    @staticmethod
    def withdraw(accountNumber: str, amount: float):
        data = { 'account_number': accountNumber, 'amount': amount }
        res = requests.post(f"{API_URL}/transactions/withdraw", json=data)
        return handle_response(res)

    @staticmethod
    def transfer(sender: str, receiver: str, amount: float):
        data = { 'sender': sender, 'receiver': receiver, 'amount': amount }
        res = requests.post(f"{API_URL}/transactions/transfer", json=data)
        return handle_response(res)