import React from 'react';
import { useState, useEffect } from 'react';
import axios from 'axios';

const Dashboard = ({ user }) => {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    // Fetch balance and transactions history on component mount
    axios.get('/api/accounts/balance', { headers: { Authorization: `Bearer ${user.token}` } })
      .then((response) => {
        setBalance(response.data.balance);
      });
    
    axios.get('/api/transactions/history', { headers: { Authorization: `Bearer ${user.token}` } })
      .then((response) => {
        setTransactions(response.data.transactions);
      });
  }, [user]);

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Welcome, {user.username}!</p>
      
      <h2>Account Balance: ${balance}</h2>

      <h3>Transaction History:</h3>
      {transactions.map((transaction) => (
        <div key={transaction.id}>
          <p><strong>From:</strong> {transaction.sender_account_number}</p>
          <p><strong>To:</strong> {transaction.receiver_account_number}</p>
          <p><strong>Amount:</strong> ${transaction.amount}</p>
          <p><strong>Timestamp:</strong> {new Date(transaction.timestamp).toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
};

export default Dashboard;