'use client';

import styles from './page.module.css';
import ChatComponent from '../components/ChatComponent';

export default function HomePage() {
    return (
        <main className={styles.main}>
            <div className={styles.chatSection}>
                <div className={styles.chatHeader}>
                    <h1 className={styles.title}>AI Learning Portal</h1>
                    <p className={styles.subtitle}>
                        Your personalized AI-powered learning assistant
                    </p>
                </div>
                <div className={styles.chatWrapper}>
                    <ChatComponent />
                </div>
            </div>
        </main>
    );
}