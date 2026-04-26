I'm sorry for misunderstanding your request earlier. It seems you want a React component to represent a product in an e-commerce application. Here is the raw source code of Product.js:

```javascript
import React from 'react';

class Product extends React.Component {
  render() {
    return (
      <div className="product">
        <h2 className="product-name">{this.props.name}</h2>
        <img src={this.props.imageUrl} alt={this.props.name} />
        <p className="product-description">{this.props.description}</p>
        <p className="product-price">Price: {this.props.price}</p>
      </div>
    );
  }
}

export default Product;
```
This component takes in four props: name, imageUrl, description, and price. It displays the product's name, image, description, and price. The class-based syntax is used to define this React component.