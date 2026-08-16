/**
 * Test API Connection Script
 * This script tests if the frontend API service can connect to the backend.
 */

// Simple test without full frontend setup
const axios = require('axios');

const API_BASE_URL = 'http://localhost:8000';
const API_VERSION = '/api/v1';

async function testApiConnection() {
    console.log('🌐 Testing API connection...');
    
    try {
        // Test basic connectivity
        const response = await axios.get(`${API_BASE_URL}/health`);
        console.log('✅ Health check passed:', response.data);
        
        // Test API endpoints
        const endpoints = [
            'auth_register',
            'auth_login', 
            'users'
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await axios.get(`${API_BASE_URL}${API_VERSION}/${endpoint}`);
                console.log(`✅ ${endpoint}: ${response.status} - ${response.data.message || response.data}`);
            } catch (error) {
                if (error.response) {
                    console.log(`❌ ${endpoint}: ${error.response.status} - ${error.response.data.message || 'No message'}`);
                } else {
                    console.log(`❌ ${endpoint}: Connection failed - ${error.message}`);
                }
            }
        }
        
    } catch (error) {
        console.error('❌ Backend connection failed:', error.message);
        process.exit(1);
    }
}

testApiConnection();