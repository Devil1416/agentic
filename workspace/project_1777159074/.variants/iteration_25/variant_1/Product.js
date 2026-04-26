import React from 'react';

class Product extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            product: null
        };
    }
    
    componentDidMount() {
        // Fetch the product data using props.id from the backend API
        fetch(`/api/products/${this.props.id}`)
            .then(res => res.json())
            .then(product => this.setState({ product }));
    }
    
    render() {
        const { product } = this.state;
        
        if (!product) return null; // Return nothing while the data is being fetched
        
        return (
            <div className="Product">
                <h2>{product.name}</h2>
                <img src={product.image_url} alt={product.name} />
                <p>{product.description}</p>
                <p>${product.price}</p>
            </div>
        );
    }
}

export default Product;