I'm sorry for misunderstanding your request earlier. It seems you want to write a simple React application as frontend entrypoint. Here is the raw source code:

```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

This code is the entry point for your React application. It imports `react` and `react-dom`, which are required to run a React application. The `createRoot` method from `react-dom/client` creates a root instance that can be used to render your app into a DOM element.