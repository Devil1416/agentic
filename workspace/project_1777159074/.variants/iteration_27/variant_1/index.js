I'm sorry for misunderstanding your request earlier. It seems you want to create a React frontend entrypoint file (index.js). Here is the raw source code for it:

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

This code imports the necessary modules for React and renders your main App component inside it. The `ReactDOM.createRoot` method is used to create a root instance of your application, which can be attached to an HTML element with id 'root'. This is common in modern React applications where you would typically have a single root div in your index.html file.