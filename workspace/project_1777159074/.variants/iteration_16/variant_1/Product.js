I'm sorry for misunderstanding your request but it seems you want to generate a React component named `Product` which is not possible with Python as the language specified in the prompt. The code you provided should be written in JavaScript (or TypeScript if you prefer) and specifically for React. 

Here's an example of how you might write this file:

```jsx
import React from 'react';

class Product extends React.Component {
    render() {
        return (
            <div className="product">
                <h2 className="product-name">{this.props.name}</h2>
                <p className="product-description">{this.props.description}</p>
                <img src={this.props.imageUrl} alt={this.props.name}/>
                <p className="product-price">Price: {this.props.price}</p>
            </div>
        );
    }
}

export default Product;
```

This component expects to receive `name`, `description`, `imageUrl` and `price` as props from its parent component. It displays the product's name, description, image, and price in a user-friendly way. 

Please note that this is just an example and might need adjustments based on your specific requirements or project setup.