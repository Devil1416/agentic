import React from 'react';

class Product extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            product: {}
        };
    }
    
    componentDidMount() {
        // Fetch the product data here using props or state id
    }
    
    render() {
        return (
            <div className="product-container">
                <h2>{this.state.product.name}</h2>
                <img src={this.state.product.image_url} alt={this.state.product.name} />
                <p>{this.state.product.description}</p>
                <p>Price: {this.state.product.price}</p>
            </div>
        );
    }
}

export default Product;