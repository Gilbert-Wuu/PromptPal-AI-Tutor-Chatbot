import Link from 'next/link';
import styles from './Header.module.css';

const Header = () => {
    return (
        <header className={styles.header}>
            <div className={styles.container}>
                <Link href="/" className={styles.logo}>
                    🏠 Personal Learning Portal
                </Link>
                <nav className={styles.nav}>
                    <Link href="/chat" className={styles.navLink}>Chat</Link>
                    <Link href="/quiz" className={styles.navLink}>Quiz</Link>
                    <Link href="/ingestor" className={styles.navLink}>Add Content</Link>
                </nav>
            </div>
        </header>
    );
};

export default Header;