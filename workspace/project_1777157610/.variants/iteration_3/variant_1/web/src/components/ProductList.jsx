import React from 'react';
import PropTypes from 'prop-types';
import ProductService from './api/productService';

class ProductList extends React.Component {
  constructor(props) {
    super(props);
    this.state = { products: [] };
  }
  
  componentDidMount() {
    ProductService.getProducts().then((products) => {
      this.setState({ products });
    });
  }
  
  render() {
    return (
      <div>
        {this.state.products.map(product => 
          <div key={product.id}>
            <h2>{product.name}</h2>
            <p>{product.description}</p>
            <p>Price: ${product.price}</p>
            {/* Add more product details as needed */}
          </div>
        )}
      </div>
    );
  }
}

ProductList.propTypes = {
  products: PropTypes.array,
};

export default ProductList;