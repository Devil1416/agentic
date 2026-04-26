I'm sorry for misunderstanding your request earlier. It seems you want to generate a React component for displaying product details. Here is the raw source code for `Product.js` file in React:

```javascript
import React from 'react';

class Product extends React.Component {
  render() {
    const { product } = this.props;
    
    return (
      <div className="product-container">
        <h2 className="product-name">{product.name}</h2>
        <img src={product.image_url} alt={product.name} />
        <p className="product-description">{product.description}</p>
        <p className="product-price">Price: {product.price}</p>
      </div>
    );
  }
}

export default Product;
```

This component expects a `product` prop, which should be an object with properties like `name`, `image_url`, `description` and `price`. The component renders the product's name, image, description and price in separate HTML elements. 

Please replace the placeholders (like `{product.name}`) with actual data from your application state or props.