import React, { useEffect, useState } from 'react';
import ProductList from './components/ProductList';
import productService from './api/productService';

const App = () => {
  const [products, setProducts] = useState([]);
  
  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const res = await productService.getAll();
      setProducts(res.data);
    } catch (err) {
      console.error('Error fetching products:', err);
    }
  };
  
  return (
    <div className="App">
      <h1>Product List</h1>
      <ProductList products={products} />
    </div>
  );
};

export default App;