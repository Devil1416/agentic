I'm sorry for misunderstanding your request earlier. It seems you want to create a React frontend entrypoint file (index.js). Here is the raw source code for it:

```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
```

This is a basic setup for a React application using the `react-dom` package to render your app into an HTML element with id 'root'. The `./App` imports the App component from './App', which should be defined in another file. 

Please ensure that you have installed react and react-dom via npm or yarn before running this code. You can install it by running:
```bash
npm install react react-dom
```
or
```bash
yarn add react react-dom
```