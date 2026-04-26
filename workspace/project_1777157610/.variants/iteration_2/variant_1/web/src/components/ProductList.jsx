import React from 'react';
import PropTypes from 'prop-types';

const ProductList = ({ products }) => {
    return (
        <div className="product-list">
            {products.map(product => 
                <div key={product.id} className="product">
                    <h2>{product.name}</h2>
                    <p>{product.description}</p>
                    <p>Price: ${product.price}</p>
                    {/* Add more product details as needed */}
                </div>)}
        </div>
    );
};

ProductList.propTypes = {
    products: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.number,
        name: PropTypes.string,
        description: PropTypes.string,
        price: PropTypes.number
    })).isRequired
};

export default ProductList;