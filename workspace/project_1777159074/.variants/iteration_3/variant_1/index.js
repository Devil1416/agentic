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

This code imports the necessary modules for React and creates a root element in your HTML document where your app will be mounted. It then renders your App component inside that root element. 

Please ensure to replace `'./App'` with the correct path to your main application component if it is not located at './App'.