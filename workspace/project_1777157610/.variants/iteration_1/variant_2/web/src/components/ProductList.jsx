import React from 'react';
import PropTypes from 'prop-types';
import ProductService from './api/productService';

class ProductList extends React.Component {
  constructor(props) {
    super(props);
    this.state = { products: [] };
  }
  
  componentDidMount() {
    ProductService.getAllProducts().then((products) => {
      this.setState({ products });
    });
  }
  
  render() {
    return (
      <ul>
        {this.state.products.map(product => 
          <li key={product.id}>
            <h2>{product.name}</h2>
            <p>{product.description}</p>
            <p>${product.price}</p>
          </li>  
        )}
      </ul>
    );
  }
}

ProductList.propTypes = {
  products: PropTypes.array,
};

export default ProductList;