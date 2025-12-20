import { useEffect } from 'react';
import { LoginScreen } from './screens/LoginScreen';
import { DashboardScreen } from './screens/DashboardScreen';
import { useAdminStore } from './store/adminStore';

function App() {
  const { isAuthenticated, checkAuth } = useAdminStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  return <DashboardScreen />;
}

export default App;
