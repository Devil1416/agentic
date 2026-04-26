I'm sorry for misunderstanding your request earlier. It seems you want to generate a React component for displaying product details. Here is the raw source code for `Product.js`:

```javascript
import React from 'react';

class Product extends React.Component {
  render() {
    const { product } = this.props;
    
    return (
      <div className="product-container">
        <h2 className="product-name">{product.name}</h2>
        <img src={product.imageUrl} alt={product.name} />
        <p className="product-description">{product.description}</p>
        <p className="product-price">Price: {product.price}</p>
      </div>
    );
  }
}

export default Product;
```
This code defines a React component `Product` that takes in a product object as props and displays its name, image, description, and price. The CSS classes used are just placeholders and should be replaced with the actual class names you want to use for styling. 

Please ensure that your project has all necessary dependencies installed (like 'react' and 'prop-types') before running this code. Also, make sure to pass a product object in the form: `{name: '', imageUrl: '', description: '', price: ''}` when you use this component. 

If there are any other requirements or specifics about your project that I may have missed, please provide more details so I can assist you better.