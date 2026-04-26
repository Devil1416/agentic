I'm sorry for misunderstanding your request earlier. It seems you want to generate a React component for displaying product details. Here is the raw source code of Product.js file:

```javascript
import React from 'react';

class Product extends React.Component {
  render() {
    const { product } = this.props;
    
    return (
      <div className="product-container">
        <h2 className="product-title">{product.name}</h2>
        <img src={product.imageUrl} alt={product.name} />
        <p className="product-description">{product.description}</p>
        <p className="product-price">Price: {product.price}</p>
      </div>
    );
  }
}

export default Product;
```
This component expects a product object as props with properties like name, imageUrl, description and price. It displays these details in the form of an HTML structure. The CSS classes used here are placeholders and should be replaced with actual class names you'll use for styling.