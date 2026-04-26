import React from 'react';
import { useState, useEffect } from 'react';

const Product = () => {
    const [product, setProduct] = useState({});

    useEffect(() => {
        // fetch product data here
    }, []);

    return (
        <div>
            {/* render product details here */}
        </div>
    );
};

export default Product;