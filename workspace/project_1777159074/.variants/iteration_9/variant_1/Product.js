import React from 'react';

class Product extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            product: null
        };
    }
    
    componentDidMount() {
        // Fetch the product data here using props or from a service
    }

    render() {
        const { product } = this.state;
        
        if (!product) return <div>Loading...</div>;
        
        return (
            <div className="product-container">
                <h2>{product.name}</h2>
                <img src={product.image_url} alt={product.name} />
                <p>{product.description}</p>
                <p>Price: {product.price}</p>
            </div>
        );
    }
}

export default Product;