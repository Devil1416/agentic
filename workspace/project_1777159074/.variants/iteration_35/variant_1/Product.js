I'm sorry for misunderstanding your request earlier. It seems you want a React component to display product details. Here is an example of how you could define such a component in JavaScript using the `react` library:

```jsx
import React from 'react';

class Product extends React.Component {
    render() {
        const { product } = this.props;
        
        return (
            <div className="product-container">
                <h2 className="product-title">{product.name}</h2>
                <img src={product.image_url} alt={product.name} />
                <p className="product-description">{product.description}</p>
                <p className="product-price">Price: {product.price}</p>
            </div>
        );
    }
}

export default Product;
```

This component expects a `product` prop, which should be an object with properties like `name`, `image_url`, `description`, and `price`. The component renders the product's name, image, description, and price in separate HTML elements. 

Please note that this is just a basic example. Depending on your project requirements, you might need to add more features or styles to it.