I'm sorry for misunderstanding your request earlier. It seems you want a React component to display product information. Here is an example of how this could be done:

```jsx
import React from 'react';

class Product extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      product: null,
    };
  }
  
  componentDidMount() {
    // Fetch the product data here and update the state with it
  }
  
  render() {
    const { product } = this.state;
    
    if (!product) return <p>Loading...</p>;
    
    return (
      <div className="Product">
        <h2>{product.name}</h2>
        <img src={product.imageUrl} alt={product.name} />
        <p>{product.description}</p>
        <p>${product.price}</p>
      </div>
    );
  }
}

export default Product;
```
This is a simple React component that fetches product data from an API when it mounts and displays the product's name, image, description, and price. The actual fetch call would depend on your backend setup. Please replace `// Fetch the product data here and update the state with it` with your own logic to get product details.