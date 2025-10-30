'use client';

import { useAuth } from '../contexts/AuthContext';
import AuthPage from './AuthPage';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
    const { isAuthenticated } = useAuth();

    if (!isAuthenticated) {
        return <AuthPage />;
    }

    return <>{children}</>;
};

export default ProtectedRoute;

