I'm sorry for misunderstanding your request earlier. It seems like you want a React frontend entrypoint file (index.js). Here is the raw source code for it:

```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
```

This code sets up the React application by rendering the App component into a root div in your HTML file, and it also includes some performance reporting functionality. Please ensure that you have installed all necessary dependencies (react, react-dom) for this to work correctly.