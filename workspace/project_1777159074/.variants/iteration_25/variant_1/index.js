I'm sorry for misunderstanding your request earlier. It seems you want to create a React frontend entrypoint file in JavaScript (index.js). Here is the raw source code:

```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

This code imports the necessary modules for React and creates a root element in your HTML file where your app will be mounted. It also wraps your App component with `<React.StrictMode>` to help catch potential issues. 

Please make sure that you have an 'App' component defined somewhere else in your project, as the import './App' assumes there is a file named 'App.js' or 'App.jsx' in the same directory as this index.js file. If it doesn't exist, you will need to create one.