I'm sorry for misunderstanding your request earlier. It seems you want to create a React frontend entrypoint file (index.js). Here is the raw source code for it:

```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

This code imports the necessary modules for React and renders your main App component into a root div in your HTML file. Please ensure that you have an 'App' component defined in your project structure.