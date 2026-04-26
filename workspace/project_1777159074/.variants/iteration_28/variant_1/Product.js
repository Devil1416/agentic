import React from 'react';
import PropTypes from 'prop-types';

class Product extends React.Component {
    render() {
        const { product } = this.props;
        
        return (
            <div className="product">
                <h2 className="product-name">{product.name}</h2>
                <img src={product.image_url} alt={product.name} />
                <p className="product-price">Price: {product.price}</p>
            </div>
        );
    }
}

Product.propTypes = {
    product: PropTypes.shape({
        name: PropTypes.string,
        image_url: PropTypes.string,
        price: PropTypes.number
    }).isRequired
};

export default Product;