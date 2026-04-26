import React from 'react';
import { useState } from 'react';
import axios from 'axios';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = async (event) => {
        event.preventDefault();
        
        try {
            await axios({
                method: 'post',
                url: '/api/auth/login',
                data: {
                    username: username,
                    password: password
                }
            });
            
            // Handle successful login here (e.g., redirect to dashboard)
        } catch (error) {
            console.log(error);
        }
    };
    
    return (
        <form onSubmit={handleSubmit}>
            <label htmlFor="username">Username:</label>
            <input type="text" id="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
            
            <label htmlFor="password">Password:</label>
            <input type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            
            <button type="submit">Login</button>
        </form>
    );
};

export default Login;