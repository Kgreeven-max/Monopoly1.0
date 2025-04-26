import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSocket } from './SocketContext'; 

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null); // Holds { id, username, role } or null
    const [adminKey, setAdminKey] = useState(null); // Store admin key separately
    const [loading, setLoading] = useState(true); // Loading during initial session check
    const [error, setError] = useState(null);
    const [pendingAuthPlayerId, setPendingAuthPlayerId] = useState(null); // Temp storage for ID before socket auth
    const [playerInfo, setPlayerInfo] = useState(null);
    
    const { socket, isConnected, connectSocket, disconnectSocket } = useSocket();
    const navigate = useNavigate();
    const location = useLocation();
    
    // --- Derived State --- 
    const isAuthenticated = !!user;
    const role = user?.role;

    // --- Effects --- 

    // 1. Check for persisted session on initial load
    useEffect(() => {
        setLoading(true);
        const storedUserInfo = localStorage.getItem('userInfo');
        const storedAdminKey = localStorage.getItem('adminKey'); // Check for admin key too

        if (storedAdminKey) {
            console.log('[AuthContext] Restoring admin session.');
            // Validate key? For now, assume stored key is valid
            setAdminKey(storedAdminKey);
            // Create a dummy admin user object for consistency
            setUser({ id: 'admin', username: 'Administrator', role: 'admin' });
            if (!isConnected) connectSocket(); // Connect socket for admin too
        }
        else if (storedUserInfo) {
            try {
                const userInfo = JSON.parse(storedUserInfo);
                if (userInfo && userInfo.id && userInfo.role && userInfo.role !== 'admin') { // Ensure it's not admin
                    console.log('[AuthContext] Restoring player session for:', userInfo);
                    setUser(userInfo);
                    if (!isConnected) connectSocket(); 
                } else {
                     localStorage.removeItem('userInfo'); // Clear invalid data
                }
            } catch (e) {
                console.error("Failed to parse stored user info:", e);
                localStorage.removeItem('userInfo');
            }
        }
         setLoading(false); 
    }, [connectSocket]); // connectSocket dependency is fine here

    // 2. Authenticate socket for players
    useEffect(() => {
        if (isConnected && socket && pendingAuthPlayerId) {
            console.log(`[AuthContext] Socket connected, emitting authenticate_socket for pending player ${pendingAuthPlayerId}`);
            socket.emit('authenticate_socket', { player_id: pendingAuthPlayerId });
            setPendingAuthPlayerId(null); // Clear pending ID after emitting
        }
    }, [isConnected, socket, pendingAuthPlayerId]);

    // 3. Navigate after user state is successfully set
    useEffect(() => {
        if (user?.role === 'player' && user.id) {
            console.log(`[AuthContext] User state updated for player ${user.username}, navigating to /player/${user.id}`);
            navigate(`/player/${user.id}`);
        } else if (user?.role === 'admin') {
            console.log(`[AuthContext] User state updated for admin, navigating to /admin`);
            navigate('/admin'); 
        } else if (user?.role === 'display') {
            console.log(`[AuthContext] User state updated for display, navigating to /board`);
            navigate('/board'); // Navigate display to /board
        }
    }, [user, navigate]);

    // Check URL path on initial load to auto-authenticate for display mode
    useEffect(() => {
        const initAuth = async () => {
            // If on board page, auto-authenticate as display
            if (location.pathname === '/board') {
                console.log('[AuthContext] Auto-authenticating for display mode');
                setUser({ 
                    id: 'display-' + Date.now(),
                    role: 'display',
                    username: 'Display'
                });
                setLoading(false);
            } else {
                // Otherwise check for saved auth
                const savedUser = localStorage.getItem('user');
                const savedAdmin = localStorage.getItem('adminKey');
                const savedPlayer = localStorage.getItem('playerInfo');
                
                if (savedUser) {
                    setUser(JSON.parse(savedUser));
                }
                if (savedAdmin) {
                    setAdminKey(savedAdmin);
                }
                if (savedPlayer) {
                    setPlayerInfo(JSON.parse(savedPlayer));
                }
                setLoading(false);
            }
        };
        
        initAuth();
    }, [location.pathname]);

    // --- Auth Functions --- 

    const registerPlayer = useCallback(async (username, pin) => {
        setError(null);
        setLoading(true);
        console.log('[AuthContext] Attempting registration...');

        // Ensure socket connection is initiated
        if (!isConnected) {
            connectSocket();
        }
        
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST', // Assuming register is POST
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, pin }),
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                // Try to get error from backend, fallback to statusText or generic message
                throw new Error(data.error || data.message || `HTTP error! status: ${response.status}`);
            }

            console.log('[AuthContext] Registration API successful:', data);
            const newUser = { id: data.player_id, username: username, role: 'player' };
            
            // Store user info and set pending ID for socket auth
            localStorage.setItem('userInfo', JSON.stringify(newUser));
            setAdminKey(null); // Clear admin key if player registers
            localStorage.removeItem('adminKey');
            setUser(newUser); 
            setPendingAuthPlayerId(newUser.id); // Trigger socket auth effect
            
            // Navigation will happen via the useEffect hook watching `user` state
            return { success: true, player_id: newUser.id };

        } catch (err) {
            console.error('[AuthContext] Registration failed:', err);
            setError(err.message || 'Registration failed.');
            setUser(null);
            localStorage.removeItem('userInfo');
            return { success: false, error: err.message || 'Registration failed.' };
        } finally {
            setLoading(false);
        }
    }, [connectSocket, isConnected]); // Dependencies

    const loginPlayer = useCallback(async (username, pin) => {
        setError(null);
        setLoading(true);
        console.log('[AuthContext] Attempting player login...');

        if (!isConnected) {
            connectSocket();
        }

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, pin }), // Send username for login
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                 throw new Error(data.error || data.message || `HTTP error! status: ${response.status}`);
            }
            
            console.log('[AuthContext] Player Login API successful:', data);
            const loggedInUser = { id: data.player_id, username: data.username, role: 'player' };

            localStorage.setItem('userInfo', JSON.stringify(loggedInUser));
            setAdminKey(null); // Clear admin key on player login
            localStorage.removeItem('adminKey');
            setUser(loggedInUser);
            setPendingAuthPlayerId(loggedInUser.id); // Trigger socket auth effect

            return { success: true, player_id: loggedInUser.id };

        } catch (err) {
            console.error('[AuthContext] Player Login failed:', err);
            setError(err.message || 'Login failed.');
            setUser(null);
            localStorage.removeItem('userInfo');
            return { success: false, error: err.message || 'Login failed.' };
        } finally {
            setLoading(false);
        }
    }, [connectSocket, isConnected]);

    // --- NEW Admin Login Function ---
    const loginAdmin = useCallback(async (key) => {
        setError(null);
        setLoading(true);
        console.log('[AuthContext] Attempting admin login...');

        if (!isConnected) {
            connectSocket(); // Ensure socket connection for admin too
        }
        
        try {
            // Simulate API call for validation (replace with actual API call if needed)
            const response = await fetch('/api/auth/admin/login', {
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ admin_key: key })
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Invalid admin key');
            }

            console.log('[AuthContext] Admin Login API successful');
            const adminUser = { id: 'admin', username: 'Administrator', role: 'admin' };
            
            localStorage.setItem('adminKey', key); // Persist admin key
            localStorage.removeItem('userInfo'); // Remove player info if admin logs in
            setAdminKey(key);
            setUser(adminUser);
            setPendingAuthPlayerId(null); // Admins don't need player socket auth
            
            // Navigation happens in useEffect watching `user`
            return { success: true };

        } catch (err) {  
            console.error('[AuthContext] Admin login failed:', err);
            setError(err.message || 'Admin login failed.');
            setUser(null);
            setAdminKey(null);
            localStorage.removeItem('adminKey');
            return { success: false, error: err.message || 'Admin login failed.' };
        } finally {
            setLoading(false);
        }
    }, [connectSocket, isConnected]); // Dependencies

    const logout = useCallback(() => {
        console.log('[AuthContext] Logging out...');
        setUser(null);
        setAdminKey(null); // Clear admin key on logout
        setPendingAuthPlayerId(null);
        localStorage.removeItem('userInfo');
        localStorage.removeItem('adminKey'); // Remove admin key on logout
        if (isConnected) {
            disconnectSocket(); // Disconnect socket only if it was connected
        }
        navigate('/'); // Redirect immediately on logout
    }, [disconnectSocket, navigate, isConnected]); // Added isConnected dependency
    
    // --- Display Initialization Function ---
    const initializeDisplay = useCallback(async () => {
        setError(null);
        setLoading(true);
        console.log('[AuthContext] Attempting to initialize display...');

        // Display doesn't strictly NEED a socket connection unless it needs
        // direct interaction later, but connecting might be useful for consistency.
        if (!isConnected) {
            connectSocket();
        }
        
        try {
            // Call backend to initialize display (no key required)
            const response = await fetch('/api/auth/display/initialize', {
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Display initialization failed');
            }

            console.log('[AuthContext] Display initialized successfully');
            // Create a dummy user object for display role
            const displayUser = { id: 'display', username: 'Game Display', role: 'display' };
            
            localStorage.removeItem('userInfo'); // Remove player info 
            localStorage.removeItem('adminKey'); // Remove admin key
            setUser(displayUser);
            setAdminKey(null); // Clear admin key state
            setPendingAuthPlayerId(null); // Displays don't authenticate as players
            
            // Navigation happens in useEffect watching `user`
            return { success: true };

        } catch (err) {  
            console.error('[AuthContext] Display initialization failed:', err);
            setError(err.message || 'Display initialization failed.');
            setUser(null);
            // Clear any persisted display state if needed
            return { success: false, error: err.message || 'Display initialization failed.' };
        } finally {
            setLoading(false);
        }
    }, [connectSocket, isConnected]); // Dependencies

    // Context Value - Add adminKey
    const value = {
        user,
        isAuthenticated,
        role,
        loading,
        error,
        adminKey, 
        loginPlayer,
        logout, 
        registerPlayer,
        loginAdmin, 
        initializeDisplay,
        playerInfo
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}