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
      const fetchedProducts = await productService.getAllProducts();
      setProducts(fetchedProducts);
    } catch (error) {
      console.log('Error fetching products: ', error);
    }
  };
  
  return (
    <div className="App">
      <h1>E-commerce Platform</h1>
      <ProductList products={products} />
    </div>
  );
};

export default App;