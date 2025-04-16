const API_BASE_URL = '/api';

// Helper function to handle API responses
const handleResponse = async (response) => {
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'An error occurred');
  }
  return data;
};

// Authentication API
export const auth = {
  login: async (credentials) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    return handleResponse(response);
  },

  register: async (playerData) => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(playerData),
    });
    return handleResponse(response);
  },
};

// Game API
export const game = {
  getState: async () => {
    const response = await fetch(`${API_BASE_URL}/game/state`);
    return handleResponse(response);
  },

  start: async (settings) => {
    const response = await fetch(`${API_BASE_URL}/game/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    return handleResponse(response);
  },

  end: async () => {
    const response = await fetch(`${API_BASE_URL}/game/end`, {
      method: 'POST',
    });
    return handleResponse(response);
  },
};

// Player API
export const player = {
  getStatus: async (playerId) => {
    const response = await fetch(`${API_BASE_URL}/player/${playerId}/status`);
    return handleResponse(response);
  },

  rollDice: async () => {
    const response = await fetch(`${API_BASE_URL}/player/roll`, {
      method: 'POST',
    });
    return handleResponse(response);
  },

  endTurn: async () => {
    const response = await fetch(`${API_BASE_URL}/player/end-turn`, {
      method: 'POST',
    });
    return handleResponse(response);
  },
};

// Property API
export const property = {
  purchase: async (propertyId) => {
    const response = await fetch(`${API_BASE_URL}/property/${propertyId}/purchase`, {
      method: 'POST',
    });
    return handleResponse(response);
  },

  improve: async (propertyId) => {
    const response = await fetch(`${API_BASE_URL}/property/${propertyId}/improve`, {
      method: 'POST',
    });
    return handleResponse(response);
  },

  mortgage: async (propertyId) => {
    const response = await fetch(`${API_BASE_URL}/property/${propertyId}/mortgage`, {
      method: 'POST',
    });
    return handleResponse(response);
  },
};

// Finance API
export const finance = {
  getLoan: async (amount) => {
    const response = await fetch(`${API_BASE_URL}/finance/loan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount }),
    });
    return handleResponse(response);
  },

  createCD: async (amount, term) => {
    const response = await fetch(`${API_BASE_URL}/finance/cd`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount, term }),
    });
    return handleResponse(response);
  },

  getHELOC: async (propertyId, amount) => {
    const response = await fetch(`${API_BASE_URL}/finance/heloc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ propertyId, amount }),
    });
    return handleResponse(response);
  },
};

// Admin API
export const admin = {
  getGameModes: async () => {
    const response = await fetch(`${API_BASE_URL}/admin/game-modes`);
    return handleResponse(response);
  },

  updateGameMode: async (settings) => {
    const response = await fetch(`${API_BASE_URL}/admin/game-mode`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    return handleResponse(response);
  },

  manageBots: async (action, botData) => {
    const response = await fetch(`${API_BASE_URL}/admin/bots`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, ...botData }),
    });
    return handleResponse(response);
  },

  getSystemStatus: async () => {
    const response = await fetch(`${API_BASE_URL}/admin/status`);
    return handleResponse(response);
  },
};

// Remote Play API
export const remote = {
  createTunnel: async () => {
    const response = await fetch(`${API_BASE_URL}/remote/tunnel`, {
      method: 'POST',
    });
    return handleResponse(response);
  },

  getTunnelStatus: async () => {
    const response = await fetch(`${API_BASE_URL}/remote/tunnel/status`);
    return handleResponse(response);
  },

  closeTunnel: async () => {
    const response = await fetch(`${API_BASE_URL}/remote/tunnel`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
}; 