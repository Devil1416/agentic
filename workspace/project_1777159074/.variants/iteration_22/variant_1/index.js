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

This code imports the necessary modules and renders your React application into a root element with id 'root'. Please ensure that you have an `index.html` file in your public directory (usually located at `public/index.html`) where this div is:

```html
<div id="root"></div>
```

Also, make sure to install the necessary React dependencies by running `npm i react react-dom` in your project root directory before you run this script.