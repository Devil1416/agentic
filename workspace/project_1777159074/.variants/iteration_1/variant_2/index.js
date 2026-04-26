I'm sorry for misunderstanding your request earlier. It seems you want to create a simple React application as an entrypoint of your frontend. Here is the raw source code for `index.js` in a React app created with Vite:

```javascript
import { render } from 'react-dom';
import App from './App';

render(<App />, document.getElementById('root'));
```

This will mount your main application component (which you should have defined as `./App`) at the root of your HTML file (assuming it has an element with id 'root'). 

Please ensure that this file is located in the correct directory and all dependencies are installed correctly. If you're using a package manager like npm or yarn, make sure to run `npm install react react-dom` before running this script.