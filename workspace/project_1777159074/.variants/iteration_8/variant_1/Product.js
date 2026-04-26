I'm sorry for misunderstanding your request earlier. Here is a simple React component that represents a product:

```jsx
import React from 'react';

class Product extends React.Component {
  render() {
    const { product } = this.props;
    
    return (
      <div className="product-card">
        <h2>{product.name}</h2>
        <img src={product.imageUrl} alt={product.name}/>
        <p>{product.description}</p>
        <p>Price: {product.price}</p>
      </div>
    );
  }
}

export default Product;
```

This component expects a `product` prop, which should be an object with properties like `name`, `imageUrl`, `description` and `price`. It displays the product's name, image, description and price in a card-like format. 

Please note that this is a very basic example and does not include any styling or interactivity. You would likely want to add more features based on your specific needs.