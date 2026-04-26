I'm sorry for misunderstanding your request earlier. It seems you want to create a React frontend entrypoint file (index.js). Here is the raw source code for that:

```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
```

This is a basic setup for a React application using the create-react-app toolchain, where `index.js` serves as the entry point to your application. It imports the root component of your app (in this case, 'App'), and renders it into the DOM element with id 'root'.