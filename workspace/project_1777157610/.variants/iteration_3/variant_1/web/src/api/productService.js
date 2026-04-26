import axios from 'axios';

const apiUrl = '/api/products';

export const getProducts = async () => {
    try {
        const response = await axios.get(apiUrl);
        return response.data;
    } catch (error) {
        console.log('Error fetching products: ', error);
        throw error;
    }
};

export const getProductById = async (id) => {
    try {
        const response = await axios.get(`${apiUrl}/${id}`);
        return response.data;
    } catch (error) {
        console.log('Error fetching product: ', error);
        throw error;
    }
};

export const createProduct = async (productData) => {
    try {
        const response = await axios.post(apiUrl, productData);
        return response.data;
    } catch (error) {
        console.log('Error creating product: ', error);
        throw error;
    }
};

export const updateProduct = async (id, productData) => {
    try {
        const response = await axios.put(`${apiUrl}/${id}`, productData);
        return response.data;
    } catch (error) {
        console.log('Error updating product: ', error);
        throw error;
    }
};

export const deleteProduct = async (id) => {
    try {
        await axios.delete(`${apiUrl}/${id}`);
    } catch (error) {
        console.log('Error deleting product: ', error);
        throw error;
    }
};