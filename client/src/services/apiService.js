/**
 * Base API service for handling common request operations
 */
class ApiService {
  static adminKey = null; // Keep track of the key in memory

  /**
   * Helper to get standard headers, including admin key if available
   * @returns {Object} Headers object
   */
  static _getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    const adminKey = this.getAdminKey();
    if (adminKey) {
      headers['X-Admin-Key'] = adminKey;
    }
    return headers;
  }

  /**
   * Make a GET request to the API
   * @param {string} endpoint - API endpoint
   * @param {Object} params - Query parameters
   * @param {boolean} isAdminRequest - Whether this is an admin-authenticated request
   * @returns {Promise<any>} - API response
   */
  static async get(endpoint, params = {}, isAdminRequest = false) {
    const url = new URL(`${window.location.origin}/api${endpoint}`);
    
    // Add query parameters
    Object.keys(params).forEach(key => {
      url.searchParams.append(key, params[key]);
    });
    
    try {
      const headers = this._getHeaders();
      if (isAdminRequest && !headers['X-Admin-Key']) {
        throw new Error('Admin key not set for admin request');
      }

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: headers,
        credentials: 'include', // TODO: Review if needed
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({})); // Try to get error details
        throw new Error(errorData.error || `API error: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API GET request failed:', error);
      throw error;
    }
  }
  
  /**
   * Make a POST request to the API
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request body data
   * @param {boolean} isAdminRequest - Whether this is an admin-authenticated request
   * @returns {Promise<any>} - API response
   */
  static async post(endpoint, data = {}, isAdminRequest = false) {
    const url = new URL(`${window.location.origin}/api${endpoint}`);
    
    try {
      const headers = this._getHeaders();
      if (isAdminRequest && !headers['X-Admin-Key']) {
        throw new Error('Admin key not set for admin request');
      }

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: headers,
        credentials: 'include', // TODO: Review if needed
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `API error: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API POST request failed:', error);
      throw error;
    }
  }
  
  /**
   * Make a PUT request to the API
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request body data
   * @param {boolean} isAdminRequest - Whether this is an admin-authenticated request
   * @returns {Promise<any>} - API response
   */
  static async put(endpoint, data = {}, isAdminRequest = false) {
    const url = `${window.location.origin}/api${endpoint}`;
    
    try {
      const headers = this._getHeaders();
      if (isAdminRequest && !headers['X-Admin-Key']) {
        throw new Error('Admin key not set for admin request');
      }

      const response = await fetch(url, {
        method: 'PUT',
        headers: headers,
        credentials: 'include', // TODO: Review if needed
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `API error: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API PUT request failed:', error);
      throw error;
    }
  }
  
  /**
   * Make a DELETE request to the API
   * @param {string} endpoint - API endpoint
   * @param {boolean} isAdminRequest - Whether this is an admin-authenticated request
   * @returns {Promise<any>} - API response
   */
  static async delete(endpoint, isAdminRequest = false) {
    const url = `${window.location.origin}/api${endpoint}`;
    
    try {
      const headers = this._getHeaders();
      if (isAdminRequest && !headers['X-Admin-Key']) {
        throw new Error('Admin key not set for admin request');
      }

      const response = await fetch(url, {
        method: 'DELETE',
        headers: headers,
        credentials: 'include', // TODO: Review if needed
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `API error: ${response.status} ${response.statusText}`);
      }
      
      // Handle potential empty response body for DELETE
      const responseText = await response.text();
      return responseText ? JSON.parse(responseText) : {}; 

    } catch (error) {
      console.error('API DELETE request failed:', error);
      throw error;
    }
  }
  
  /**
   * Set an admin key for API requests
   * @param {string} key - Admin key
   */
  static setAdminKey(key) {
    this.adminKey = key;
    if (key) {
      localStorage.setItem('adminKey', key);
    } else {
      localStorage.removeItem('adminKey');
    }
  }
  
  /**
   * Get the stored admin key
   * @returns {string|null} - Admin key
   */
  static getAdminKey() {
    if (this.adminKey === null) { // Check if already loaded from localStorage
      this.adminKey = localStorage.getItem('adminKey');
    }
    return this.adminKey;
  }
  
  /**
   * Make an admin-authenticated GET request
   * @param {string} endpoint - API endpoint
   * @param {Object} params - Query parameters
   * @returns {Promise<any>} - API response
   */
  static async adminGet(endpoint, params = {}) {
    // Pass isAdminRequest = true to the base get method
    return this.get(endpoint, params, true);
  }
  
  /**
   * Make an admin-authenticated POST request
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request body data
   * @returns {Promise<any>} - API response
   */
  static async adminPost(endpoint, data = {}) {
    // Pass isAdminRequest = true to the base post method
    return this.post(endpoint, data, true);
  }

  /**
   * Make an admin-authenticated PUT request
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request body data
   * @returns {Promise<any>} - API response
   */
  static async adminPut(endpoint, data = {}) {
    return this.put(endpoint, data, true);
  }

  /**
   * Make an admin-authenticated DELETE request
   * @param {string} endpoint - API endpoint
   * @returns {Promise<any>} - API response
   */
  static async adminDelete(endpoint) {
    return this.delete(endpoint, true);
  }
}

export default ApiService; 