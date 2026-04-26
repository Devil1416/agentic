I'm sorry for misunderstanding your request earlier. However, it seems like you want to create a React frontend entrypoint file that is not written in Python but JavaScript (JS). Here is the raw source code for `index.js`:

```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
```

This code imports the necessary modules and renders the `App` component into a root element in your HTML file. Make sure to have an element with id 'root' in your HTML file for this to work. 

Please note that you need to have React and react-dom installed as dependencies in your project for this code to run correctly. You can install them by running `npm i react react-dom` in the terminal from within your project directory.