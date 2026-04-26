import React from 'react';

class Product extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            product: {}
        };
    }
    
    componentDidMount() {
        fetch('http://localhost:8000/products/' + this.props.match.params.id)
            .then(response => response.json())
            .then(data => this.setState({ product: data }));
    }
    
    render() {
        return (
            <div>
                <h1>{this.state.product.name}</h1>
                <img src={this.state.product.image_url} alt={this.state.product.name}/>
                <p>{this.state.product.description}</p>
                <p>Price: {this.state.product.price}</p>
            </div>
        );
    }
}

export default Product;