import React from 'react';

class Product extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            product: {}
        };
    }
    
    componentDidMount() {
        // Fetch the product data using props id
        fetch(`/api/products/${this.props.id}`)
            .then(res => res.json())
            .then(product => this.setState({ product }));
    }
    
    render() {
        return (
            <div className="Product">
                <h2>{this.state.product.name}</h2>
                <img src={this.state.product.image_url} alt={this.state.product.name} />
                <p>{this.state.product.description}</p>
                <p>${this.state.product.price}</p>
            </div>
        );
    }
}

export default Product;