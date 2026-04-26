I'm sorry for misunderstanding your request earlier. It seems like you want to create a React frontend entrypoint file (index.js). Here is the raw source code for it:

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

This code imports the necessary modules for React and creates a root element in your HTML file where your app will be rendered. It also wraps your App component with `<React.StrictMode>` which is useful for highlighting potential issues in an application but it introduces extra checks and warnings to the console.