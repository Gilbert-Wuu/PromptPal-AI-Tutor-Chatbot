import IngestForm from '../../components/IngestForm';
import '../globals.css';

export default function Home() {
    return (
        <main>
            <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                <h1>Knowledge Base Ingestor</h1>
                <p>Use the form below to add new content to your knowledge base.</p>
            </div>
            <IngestForm />
        </main>
    );
}