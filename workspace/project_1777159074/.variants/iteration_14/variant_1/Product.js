import React from 'react';

class Product extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            product: null
        };
    }
    
    componentDidMount() {
        // Fetch the product data from the backend API
        fetch('http://localhost:8000/products/' + this.props.id)
            .then(response => response.json())
            .then(data => this.setState({product: data}));
    }
    
    render() {
        const product = this.state.product;
        
        if (!product) {
            return <div>Loading...</div>;
        }
        
        return (
            <div className="Product">
                <h2>{product.name}</h2>
                <img src={product.image_url} alt={product.name}/>
                <p>{product.description}</p>
                <p>${product.price}</p>
            </div>
        );
    }
}

export default Product;