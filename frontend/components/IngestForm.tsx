"use client";

import React, { useState } from 'react';
import axios from 'axios';
import styles from './IngestForm.module.css';

const IngestForm = () => {
    const [activeTab, setActiveTab] = useState<'pdf' | 'text'>('pdf');
    const [pdfFile, setPdfFile] = useState<File | null>(null);
    const [pastedText, setPastedText] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [message, setMessage] = useState<string>('');

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setPdfFile(event.target.files[0]);
        }
    };

    const handlePdfSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!pdfFile) {
            setMessage('Please select a PDF file first.');
            return;
        }

        setIsLoading(true);
        setMessage('');
        const formData = new FormData();
        formData.append('file', pdfFile);

        try {
            const response = await axios.post('http://127.0.0.1:8000/ingest-pdf/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setMessage(`✅ Success! Ingested ${response.data.chunks_ingested} chunks from ${response.data.source}.`);
        } catch (error) {
            console.error('Error ingesting PDF:', error);
            setMessage('❌ Error ingesting PDF. Please check the console.');
        } finally {
            setIsLoading(false);
            setPdfFile(null);
            const fileInput = document.getElementById('pdf-upload') as HTMLInputElement;
            if(fileInput) fileInput.value = '';
        }
    };

    const handleTextSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!pastedText.trim()) {
            setMessage('Please paste some text.');
            return;
        }

        setIsLoading(true);
        setMessage('');

        try {
            const response = await axios.post('http://127.0.0.1:8000/ingest-text/', {
                text: pastedText,
                source_identifier: "manual_text"
            });
            setMessage(`✅ Success! Ingested ${response.data.chunks_ingested} chunks from pasted text.`);
        } catch (error) {
            console.error('Error ingesting text:', error);
            setMessage('❌ Error ingesting text. Please check the console.');
        } finally {
            setIsLoading(false);
            setPastedText('');
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.tabs}>
                <button
                    className={`${styles.tabButton} ${activeTab === 'pdf' ? styles.active : ''}`}
                    onClick={() => setActiveTab('pdf')}
                >
                    Upload PDF
                </button>
                <button
                    className={`${styles.tabButton} ${activeTab === 'text' ? styles.active : ''}`}
                    onClick={() => setActiveTab('text')}
                >
                    Paste Text
                </button>
            </div>

            <div className={styles.formContainer}>
                {activeTab === 'pdf' && (
                    <form onSubmit={handlePdfSubmit}>
                        <p>Select a PDF file to add to the knowledge base.</p>
                        <input type="file" id="pdf-upload" accept=".pdf" onChange={handleFileChange} className={styles.fileInput} />
                        <button type="submit" disabled={isLoading || !pdfFile} className={styles.submitButton}>
                            {isLoading ? 'Ingesting...' : 'Ingest PDF'}
                        </button>
                    </form>
                )}

                {activeTab === 'text' && (
                    <form onSubmit={handleTextSubmit}>
                        <p>Paste text to add to the knowledge base.</p>
                        <textarea
                            value={pastedText}
                            onChange={(e) => setPastedText(e.target.value)}
                            placeholder="Paste your text here..."
                            className={styles.textInput}
                            rows={8}
                        />
                        <button type="submit" disabled={isLoading || !pastedText.trim()} className={styles.submitButton}>
                            {isLoading ? 'Ingesting...' : 'Ingest Text'}
                        </button>
                    </form>
                )}
            </div>

            {isLoading && <div className={styles.loader}></div>}
            {message && <p className={styles.message}>{message}</p>}
        </div>
    );
};

export default IngestForm;
