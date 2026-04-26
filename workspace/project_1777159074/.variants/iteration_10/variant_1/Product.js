I'm sorry for misunderstanding your request earlier. Here is a simple React component that represents a product:

```jsx
import React from 'react';

class Product extends React.Component {
    render() {
        return (
            <div className="product">
                <h2 className="product-name">{this.props.name}</h2>
                <p className="product-description">{this.props.description}</p>
                <p className="product-price">Price: {this.props.price}</p>
            </div>
        );
    }
}

export default Product;
```
This component takes in three props: `name`, `description` and `price` which are used to display the product's name, description and price respectively. It is a class-based component because it uses ES6 syntax for defining classes and methods. If you prefer a functional component, here's how you could write it:

```jsx
import React from 'react';

const Product = ({name, description, price}) => {
    return (
        <div className="product">
            <h2 className="product-name">{name}</h2>
            <p className="product-description">{description}</p>
            <p className="product-price">Price: {price}</p>
        </div>
    );
};

export default Product;
```
Both of these components can be used in a parent component like so:

```jsx
import React from 'react';
import Product from './components/Product';

class App extends React.Component {
    render() {
        return (
            <div className="app">
                <h1>Welcome to our store</h1>
                <Product name="Product 1" description="This is a product" price={9.99}/>
                // more products here...
            </div>
        );
    }
}
```