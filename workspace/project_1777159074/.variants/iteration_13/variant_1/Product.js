I'm sorry for misunderstanding your request earlier. It seems you want the raw React code for a product component. Here it is:

```jsx
import React from 'react';

class Product extends React.Component {
  render() {
    return (
      <div className="product-container">
        <h2 className="product-title">{this.props.name}</h2>
        <img src={this.props.imageUrl} alt={this.props.name} />
        <p className="product-description">{this.props.description}</p>
        <p className="product-price">Price: {this.props.price}</p>
      </div>
    );
  }
}

export default Product;
```
This component expects to receive `name`, `imageUrl`, `description` and `price` as props from its parent component. It displays these properties in a user-friendly way. Please replace the placeholders with your actual data.