import React from 'react';

class Product extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            product: null
        };
    }
    
    componentDidMount() {
        // Fetch the product data from API using fetch or axios
        // Update state with fetched product data
    }
    
    render() {
        const { product } = this.state;
        
        if (!product) return null;  // Return null while loading
        
        return (
            <div className="product-container">
                <h2>{product.name}</h2>
                <img src={product.image_url} alt={product.name} />
                <p>{product.description}</p>
                <p><strong>Price: </strong>${product.price}</p>
            </div>
        );
    }
}

export default Product;