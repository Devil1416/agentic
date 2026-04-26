import React from 'react';

class Product extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            product: null
        };
    }
    
    componentDidMount() {
        fetch('/api/product/' + this.props.id)
            .then(response => response.json())
            .then(data => this.setState({ product: data }));
    }
    
    render() {
        if (!this.state.product) {
            return <div>Loading...</div>;
        }
        
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