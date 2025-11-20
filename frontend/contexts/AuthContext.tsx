'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

interface User {
    user_id: string;
    email: string;
    role: string;
    prompts?: string[];
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    login: (email: string) => Promise<{ success: boolean; error?: string }>;
    signUp: (email: string, role: string) => Promise<{ success: boolean; error?: string }>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const SESSION_TOKEN_KEY = 'session_token';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    // Load user from localStorage on mount
    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        const storedToken = localStorage.getItem(SESSION_TOKEN_KEY);
        if (storedToken) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        }
        if (storedUser) {
            setUser(JSON.parse(storedUser));
            setIsAuthenticated(true);
        }
    }, []);

    const persistSession = (userData: User, token: string) => {
        setUser(userData);
        setIsAuthenticated(true);
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem(SESSION_TOKEN_KEY, token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    };

    const login = async (email: string): Promise<{ success: boolean; error?: string }> => {
        try {
            const response = await axios.post(`${API_BASE_URL}/auth/login`, { email });
            const userData = {
                ...response.data.user,
                prompts: response.data.prompts || []
            };
            persistSession(userData, response.data.session_token);
            return { success: true };
        } catch (error: any) {
            const errorMessage = error.response?.data?.detail || 'Login failed';
            return { success: false, error: errorMessage };
        }
    };

    const signUp = async (email: string, role: string): Promise<{ success: boolean; error?: string }> => {
        try {
            const response = await axios.post(`${API_BASE_URL}/auth/signup`, { email, role });
            const userData = {
                ...response.data.user,
                prompts: response.data.prompts || []
            };
            persistSession(userData, response.data.session_token);
            return { success: true };
        } catch (error: any) {
            const errorMessage = error.response?.data?.detail || 'Signup failed';
            return { success: false, error: errorMessage };
        }
    };

    const logout = () => {
        // Clear user data
        const currentUser = user;
        localStorage.removeItem('user');
        localStorage.removeItem(SESSION_TOKEN_KEY);
        delete axios.defaults.headers.common['Authorization'];
        
        // Clear chat session for this user
        if (currentUser?.user_id) {
            localStorage.removeItem(`chat_session_${currentUser.user_id}`);
        }
        
        setUser(null);
        setIsAuthenticated(false);
    };

    return (
        <AuthContext.Provider value={{ user, isAuthenticated, login, signUp, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

