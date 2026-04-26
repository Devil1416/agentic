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
This component takes in three props: `name`, `description` and `price` which are used to display the product's name, description and price respectively. It is a class-based component as it requires state management or lifecycle methods. If you prefer a functional component, you can rewrite this using React hooks.