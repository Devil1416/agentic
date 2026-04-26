import React from 'react';
import { useState } from 'react';

const Product = ({ product }) => {
  const [quantity, setQuantity] = useState(1);

  return (
    <div>
      <h2>{product.name}</h2>
      <p>Price: ${product.price}</p>
      <p>Description: {product.description}</p>
      <button onClick={() => setQuantity(quantity + 1)}>+</button>
      <span>{quantity} in stock</span>
    </div>
  );
};

export default Product;