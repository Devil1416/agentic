import React from 'react';
import PropTypes from 'prop-types';

const ProductList = ({ products }) => {
    return (
        <div className="product-list">
            {products.map(product => 
                <div key={product.id} className="product-item">
                    <h2 className="product-title">{product.name}</h2>
                    <img src={product.image_url} alt={product.name} />
                    <p className="product-price">{product.price}</p>
                </div>)}
        </div>
    );
};

ProductList.propTypes = {
    products: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.number.isRequired,
        name: PropTypes.string.isRequired,
        image_url: PropTypes.string.isRequired,
        price: PropTypes.number.isRequired
    })).isRequired
};

export default ProductList;