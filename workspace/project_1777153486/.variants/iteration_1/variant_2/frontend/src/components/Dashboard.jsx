import React from 'react';
import axios from 'axios';
import { useEffect, useState } from 'react';

const Dashboard = ({ token }) => {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    axios.get('/api/accounts', { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => {
        setBalance(res.data.balance);
      });
    
    axios.get('/api/transactions', { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => {
        setTransactions(res.data.transactions);
      });
  }, [token]);

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Balance: {balance}</p>
      <h2>Transaction History</h2>
      <ul>
        {transactions.map((transaction, index) => (
          <li key={index}>
            <p>Sender: {transaction.sender}</p>
            <p>Receiver: {transaction.receiver}</p>
            <p>Amount: {transaction.amount}</p>
            <p>Timestamp: {new Date(transaction.timestamp).toLocaleString()}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Dashboard;