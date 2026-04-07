import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2min for search+fetch operations
});

export default client;
