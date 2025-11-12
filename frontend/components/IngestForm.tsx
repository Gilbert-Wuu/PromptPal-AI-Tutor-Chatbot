"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import styles from './IngestForm.module.css';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

interface Document {
    document_id: string;
    filename: string;
    file_type: string;
    file_size: number;
    upload_date: string;
    status: string;
    chunk_count: number;
}

const IngestForm = () => {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState<'upload' | 'manage'>('upload');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [pastedText, setPastedText] = useState<string>('');
    const [documents, setDocuments] = useState<Document[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [message, setMessage] = useState<string>('');

    // Load user's documents on mount and when switching tabs
    useEffect(() => {
        if (user) {
            fetchDocuments();
        }
    }, [user, activeTab]);

    const fetchDocuments = async (showSuccessMessage = false) => {
        if (!user) return;
        
        try {
            const response = await axios.get(`${API_BASE_URL}/api/documents/${user.user_id}`);
            setDocuments(response.data.documents);
            
            if (showSuccessMessage) {
                setMessage(`Refreshed successfully! Found ${response.data.documents.length} document(s).`);
            }
        } catch (error) {
            console.error('Error fetching documents:', error);
            if (showSuccessMessage) {
                setMessage('Error refreshing documents. Please try again.');
            }
        }
    };

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setSelectedFile(event.target.files[0]);
            setMessage('');
        }
    };

    const readFileContent = (file: File): Promise<string> => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target?.result as string);
            reader.onerror = reject;
            reader.readAsText(file);
        });
    };

    const handleFileSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        
        if (!user) {
            setMessage('Please log in to upload documents.');
            return;
        }
        
        if (!selectedFile) {
            setMessage('Please select a file first.');
            return;
        }

        // Check for duplicate filename
        const existingDoc = documents.find(doc => doc.filename === selectedFile.name);
        if (existingDoc) {
            const confirmUpload = window.confirm(
                `Warning: A document named "${selectedFile.name}" already exists in your library.\n\n` +
                `Existing document: ${existingDoc.chunk_count} chunks, uploaded on ${new Date(existingDoc.upload_date).toLocaleDateString()}\n\n` +
                `Do you want to continue and upload this as a new document?`
            );
            
            if (!confirmUpload) {
                setMessage('Upload cancelled - document with same name already exists.');
                return;
            }
        }

        setIsLoading(true);
        setMessage('');

        try {
            // Read file content
            const content = await readFileContent(selectedFile);
            
            // Upload to backend
            const response = await axios.post(`${API_BASE_URL}/api/documents/upload`, {
                user_id: user.user_id,
                filename: selectedFile.name,
                content: content,
                file_type: selectedFile.type || 'text/plain',
                file_size: selectedFile.size
            });

            setMessage(`Success! Uploaded "${selectedFile.name}" - ${response.data.chunk_count} chunks created.`);
            setSelectedFile(null);
            
            // Clear file input
            const fileInput = document.getElementById('file-upload') as HTMLInputElement;
            if (fileInput) fileInput.value = '';
            
            // Refresh documents list if on manage tab
            if (activeTab === 'manage') {
                fetchDocuments();
            }
        } catch (error: any) {
            console.error('Error uploading file:', error);
            setMessage(`Error: ${error.response?.data?.detail || 'Failed to upload file'}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleTextSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        
        if (!user) {
            setMessage('Please log in to upload documents.');
            return;
        }
        
        if (!pastedText.trim()) {
            setMessage('Please enter some text.');
            return;
        }

        // Generate filename
        const filename = `pasted-text-${Date.now()}.txt`;
        
        // Check for duplicate filename (unlikely but possible)
        const existingDoc = documents.find(doc => doc.filename === filename);
        if (existingDoc) {
            const confirmUpload = window.confirm(
                `Warning: A document named "${filename}" already exists.\n\n` +
                `Do you want to continue and upload this text?`
            );
            
            if (!confirmUpload) {
                setMessage('Upload cancelled - duplicate filename detected.');
                return;
            }
        }

        setIsLoading(true);
        setMessage('');

        try {
            const response = await axios.post(`${API_BASE_URL}/api/documents/upload`, {
                user_id: user.user_id,
                filename: filename,
                content: pastedText,
                file_type: 'text/plain',
                file_size: pastedText.length
            });

            setMessage(`Success! Uploaded text - ${response.data.chunk_count} chunks created.`);
            setPastedText('');
            
            // Refresh documents list if on manage tab
            if (activeTab === 'manage') {
                fetchDocuments();
            }
        } catch (error: any) {
            console.error('Error uploading text:', error);
            setMessage(`Error: ${error.response?.data?.detail || 'Failed to upload text'}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteDocument = async (documentId: string, filename: string) => {
        if (!user) return;
        
        if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
            return;
        }

        try {
            await axios.delete(`${API_BASE_URL}/api/documents/${documentId}?user_id=${user.user_id}`);
            setMessage(`Deleted "${filename}"`);
            // Immediately refresh the document list
            await fetchDocuments();
        } catch (error: any) {
            console.error('Error deleting document:', error);
            const errorMsg = error.response?.data?.detail || 'Error deleting document';
            setMessage(errorMsg);
        }
    };

    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    const formatDate = (dateString: string): string => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className={styles.container}>
            <div className={styles.tabs}>
                <button
                    className={`${styles.tabButton} ${activeTab === 'upload' ? styles.active : ''}`}
                    onClick={() => setActiveTab('upload')}
                >
                    Upload Documents
                </button>
                <button
                    className={`${styles.tabButton} ${activeTab === 'manage' ? styles.active : ''}`}
                    onClick={() => setActiveTab('manage')}
                >
                    My Documents
                </button>
            </div>

            <div className={styles.formContainer}>
                {activeTab === 'upload' && (
                    <div className={styles.uploadSection}>
                        <div className={styles.uploadBox}>
                            <h3>Upload File</h3>
                            <form onSubmit={handleFileSubmit}>
                                <p>Select a file to add to your knowledge base (.txt, .md, .pdf)</p>
                                <input 
                                    type="file" 
                                    id="file-upload" 
                                    accept=".txt,.md,.pdf" 
                                    onChange={handleFileChange} 
                                    className={styles.fileInput} 
                                />
                                {selectedFile && (
                                    <p className={styles.fileInfo}>
                                        Selected: {selectedFile.name} ({formatFileSize(selectedFile.size)})
                                    </p>
                                )}
                                <button 
                                    type="submit" 
                                    disabled={isLoading || !selectedFile} 
                                    className={styles.submitButton}
                                >
                                    {isLoading ? 'Uploading...' : 'Upload File'}
                                </button>
                            </form>
                        </div>

                        <div className={styles.divider}>OR</div>

                        <div className={styles.uploadBox}>
                            <h3>Paste Text</h3>
                            <form onSubmit={handleTextSubmit}>
                                <p>Paste text directly to add to your knowledge base</p>
                                <textarea
                                    value={pastedText}
                                    onChange={(e) => setPastedText(e.target.value)}
                                    placeholder="Paste your text here..."
                                    className={styles.textInput}
                                    rows={8}
                                />
                                <button 
                                    type="submit" 
                                    disabled={isLoading || !pastedText.trim()} 
                                    className={styles.submitButton}
                                >
                                    {isLoading ? 'Uploading...' : 'Upload Text'}
                                </button>
                            </form>
                        </div>
                    </div>
                )}

                {activeTab === 'manage' && (
                    <div className={styles.documentsSection}>
                        <div className={styles.documentsHeader}>
                            <h3>Your Documents</h3>
                            <button onClick={() => fetchDocuments(true)} className={styles.refreshButton}>
                                Refresh
                            </button>
                        </div>

                        {documents.length === 0 ? (
                            <p className={styles.emptyState}>
                                No documents uploaded yet. Go to the Upload tab to add your first document!
                            </p>
                        ) : (
                            <div className={styles.documentsList}>
                                {documents.map((doc) => (
                                    <div key={doc.document_id} className={styles.documentCard}>
                                        <div className={styles.documentInfo}>
                                            <div className={styles.documentName}>
                                                {doc.filename}
                                            </div>
                                            <div className={styles.documentMeta}>
                                                <span>{formatFileSize(doc.file_size)}</span>
                                                <span>•</span>
                                                <span>{doc.chunk_count} chunks</span>
                                                <span>•</span>
                                                <span>{formatDate(doc.upload_date)}</span>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleDeleteDocument(doc.document_id, doc.filename)}
                                            className={styles.deleteButton}
                                            title="Delete document"
                                        >
                                            Delete
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {message && (
                <div className={`${styles.message} ${message.includes('❌') ? styles.error : styles.success}`}>
                    {message}
                </div>
            )}
        </div>
    );
};

export default IngestForm;
