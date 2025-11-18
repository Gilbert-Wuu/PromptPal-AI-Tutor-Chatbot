'use client';

import Link from 'next/link';
import Image from 'next/image';
import styles from './Header.module.css';
import { useAuth } from '../contexts/AuthContext';

const Header = () => {
    const { user, logout } = useAuth();

    return (
        <header className={styles.header}>
            <div className={styles.container}>
                <Link href="/" className={styles.logo}>
                    <Image 
                        src="/images/logo.png" 
                        alt="AI Learning Portal Logo" 
                        width={50} 
                        height={50}
                        className={styles.logoImage}
                        style={{ objectFit: 'contain' }}
                    />
                    <span className={styles.logoText}>AI Learning Portal</span>
                </Link>
                <nav className={styles.nav}>
                    <Link href="/quiz" className={styles.featureButton}>
                        <span className={styles.icon}>📖</span>
                        <span>Take a Quiz</span>
                    </Link>
                    <Link href="/ingestor" className={styles.featureButton}>
                        <span className={styles.icon}>+</span>
                        <span>Add Content</span>
                    </Link>
                    {user && (
                        <div className={styles.userSection}>
                            <span className={styles.userInfo}>
                                {user.email} ({user.role})
                            </span>
                            <button onClick={logout} className={styles.logoutButton}>
                                Logout
                            </button>
                        </div>
                    )}
                </nav>
            </div>
        </header>
    );
};

export default Header;