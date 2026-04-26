I'm sorry for misunderstanding your request earlier. It seems you want to create a React frontend entrypoint file (index.js). Here is the raw source code for it:

```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
```

This is a basic setup for a React application using the create-react-app (CRA) boilerplate. It imports the `React` and `ReactDOM` libraries, then creates a root element in the HTML document with id 'root' and renders your main App component inside it.