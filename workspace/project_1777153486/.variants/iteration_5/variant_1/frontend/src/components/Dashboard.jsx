import React from 'react';
import { useEffect } from 'react';
import axios from 'axios';

const Dashboard = () => {
    const [balance, setBalance] = React.useState(0);
    const [transactions, setTransactions] = React.useState([]);
    
    useEffect(() => {
        axios.get('/api/accounts/balance')
            .then((response) => {
                setBalance(response.data.balance);
            })
            .catch((error) => console.log('Error fetching balance: ', error));
        
        axios.get('/api/transactions')
            .then((response) => {
                setTransactions(response.data.transactions);
            })
            .catch((error) => console.log('Error fetching transactions: ', error));
    }, []);
    
    return (
        <div>
            <h1>Dashboard</h1>
            <p>Current Balance: {balance}</p>
            <h2>Transaction History</h2>
            {transactions.map((transaction, index) => (
                <div key={index}>
                    <p>From: {transaction.sender}</p>
                    <p>To: {transaction.receiver}</p>
                    <p>Amount: {transaction.amount}</p>
                    <p>Timestamp: {new Date(transaction.timestamp).toLocaleString()}</p>
                </div>
            ))}
        </div>
    );
};

export default Dashboard;