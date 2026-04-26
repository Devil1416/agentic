import React from 'react';
import { useEffect, useState } from 'react';
import axios from './services/api';

const Dashboard = ({ user }) => {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);

  // Fetch balance and transaction history on component mount
  useEffect(() => {
    axios.get('/accounts/balance', { headers: { Authorization: `Bearer ${user.token}` } })
      .then(response => setBalance(response.data.balance));
    
    axios.get('/transactions', { headers: { Authorization: `Bearer ${user.token}` } })
      .then(response => setTransactions(response.data.transactions));
  }, [user]);

  return (
    <div>
      <h2>Dashboard</h2>
      <p>Welcome, {user.username}!</p>
      
      <h3>Account Balance: ${balance}</h3>
      
      <h4>Transaction History</h4>
      {transactions.map(transaction => (
        <div key={transaction.id}>
          <p>From: {transaction.sender}</p>
          <p>To: {transaction.receiver}</p>
          <p>Amount: ${transaction.amount}</p>
          <p>Timestamp: {new Date(transaction.timestamp).toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
};

export default Dashboard;