import React from 'react';
import { useState } from 'react';
import axios from 'axios';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    
    const handleSubmit = async (event) => {
        event.preventDefault();
        
        try {
            await axios.post('/api/auth/login', { username: username, password: password });
            
            // Handle successful login here...
        } catch (error) {
            console.log(error);
        }
    };
    
    return (
        <form onSubmit={handleSubmit}>
            <input type="text" placeholder="Username" value={username} onChange={(event) => setUsername(event.target.value)} />
            <input type="password" placeholder="Password" value={password} onChange={(event) => setPassword(event.target.value)} />
            <button type="submit">Login</button>
        </form>
    );
};

export default Login;