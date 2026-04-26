import axios from 'axios';

const API_URL = "http://localhost:8000/api";

class ProductService {
    getProducts() {
        return axios.get(API_URL + '/products');
    }

    createProduct(product) {
        return axios.post(API_URL + '/products', product);
    }

    updateProduct(id, product) {
        return axios.put(API_URL + `/products/${id}`, product);
    }

    deleteProduct(id) {
        return axios.delete(API_URL + `/products/${id}`);
    }
}

export default new ProductService();