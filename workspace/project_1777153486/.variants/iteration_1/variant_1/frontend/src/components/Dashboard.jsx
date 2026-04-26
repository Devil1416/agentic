import React from 'react';
import { useState, useEffect } from 'react';
import axios from 'axios';

const Dashboard = () => {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);
  
  useEffect(() => {
    getAccountDetails();
    getTransactionHistory();
  }, []);

  const getAccountDetails = async () => {
    try {
      const res = await axios.get('/api/accounts');
      setBalance(res.data.balance);
    } catch (err) {
      console.log('Error fetching account details: ', err);
    }
  };

  const getTransactionHistory = async () => {
    try {
      const res = await axios.get('/api/transactions');
      setTransactions(res.data.history);
    } catch (err) {
      console.log('Error fetching transaction history: ', err);
    }
  };
  
  return (
    <div>
      <h1>Dashboard</h1>
      <p>Current Balance: ${balance}</p>
      <h2>Transaction History</h2>
      {transactions.map((transaction, index) => (
        <div key={index}>
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