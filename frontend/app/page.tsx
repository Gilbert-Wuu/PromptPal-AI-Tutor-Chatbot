import Link from 'next/link';
import styles from './page.module.css';

export default function HomePage() {
    return (
        <main className={styles.main}>
            <div className={styles.header}>
                <h1 className={styles.title}>Personal Learning Portal</h1>
                <p className={styles.subtitle}>
                    Your AI-powered assistant for deep, personalized learning.
                </p>
            </div>

            <div className={styles.grid}>
                <Link href="/chat" className={styles.card}>
                    <h2>Chat 💬</h2>
                    <p>Start a conversation, ask questions, and explore new topics with your trainer.</p>
                </Link>

                <Link href="/quiz" className={styles.card}>
                    <h2>Take a Quiz 🧠</h2>
                    <p>Test your knowledge on learned topics with assessments.</p>
                </Link>

                <Link href="/ingestor" className={styles.card}>
                    <h2>Add Content 📤</h2>
                    <p>Expand the portal's knowledge base by uploading documents and videos.</p>
                </Link>
            </div>
        </main>
    );
}