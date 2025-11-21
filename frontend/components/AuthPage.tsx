'use client';

import { useState } from 'react';
import styles from './AuthPage.module.css';
import { useAuth } from '../contexts/AuthContext';

// Available role options
const ROLE_OPTIONS = [
    'Executive Assistant',
    'Compliance Analyst',
    'Client Service Associate',
    'Marketing Associate',
    'Operations Associate',
    'HR Coordinator',
    'Investor Relations Coordinator',
    'Administrative Assistant',
    'Project Coordinator',
    'Product Specialist',
    'Portfolio Operations Assistant',
    'Communications Specialist',
    'Training & Development Associate',
    'Sales Representative'
];

const AuthPage = () => {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [role, setRole] = useState('');
    const [error, setError] = useState('');
    const { login, signUp } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!email || !email.includes('@')) {
            setError('Please enter a valid email address');
            return;
        }

        if (isLogin) {
            // Login
            const result = await login(email);
            if (!result.success) {
                setError(result.error || 'Login failed');
            }
        } else {
            // Sign up
            if (!role || role.trim() === '') {
                setError('Please enter your role');
                return;
            }
            const result = await signUp(email, role.trim());
            if (!result.success) {
                setError(result.error || 'Signup failed');
            }
        }
    };

    const toggleMode = () => {
        setIsLogin(!isLogin);
        setError('');
        setEmail('');
        setRole('');
    };

    return (
        <div className={styles.container}>
            <div className={styles.authBox}>
                <h1 className={styles.title}>
                    {isLogin ? 'Welcome Back' : 'Create Account'}
                </h1>
                <p className={styles.subtitle}>
                    {isLogin 
                        ? 'Sign in to access your learning portal' 
                        : 'Sign up to start your learning journey'}
                </p>

                <form onSubmit={handleSubmit} className={styles.form}>
                    <div className={styles.inputGroup}>
                        <label htmlFor="email" className={styles.label}>
                            Email Address
                        </label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="your.email@example.com"
                            className={styles.input}
                            required
                        />
                    </div>

                    {!isLogin && (
                        <div className={styles.inputGroup}>
                            <label htmlFor="role" className={styles.label}>
                                Role
                            </label>
                            <select
                                id="role"
                                value={role}
                                onChange={(e) => setRole(e.target.value)}
                                className={styles.input}
                                required
                            >
                                <option value="">Select your role...</option>
                                {ROLE_OPTIONS.map((roleOption) => (
                                    <option key={roleOption} value={roleOption}>
                                        {roleOption}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                    {error && <div className={styles.error}>{error}</div>}

                    <button type="submit" className={styles.submitButton}>
                        {isLogin ? 'Sign In' : 'Sign Up'}
                    </button>
                </form>

                <div className={styles.toggleContainer}>
                    <p className={styles.toggleText}>
                        {isLogin ? "Don't have an account?" : 'Already have an account?'}
                    </p>
                    <button onClick={toggleMode} className={styles.toggleButton}>
                        {isLogin ? 'Sign Up' : 'Sign In'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AuthPage;

