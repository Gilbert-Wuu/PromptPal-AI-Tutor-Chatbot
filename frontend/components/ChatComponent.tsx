'use client';

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import styles from './ChatComponent.module.css';
import { useAuth } from '../contexts/AuthContext';

// Define the structure of a chat message
interface Message {
    sender: 'user' | 'portal';
    content: string;
}

interface Document {
    document_id: string;
    filename: string;
    file_type: string;
    upload_date: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const ChatComponent = () => {
    const { user } = useAuth();
    const [messages, setMessages] = useState<Message[]>([]);
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [inputValue, setInputValue] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(true); // Start loading initially
    const [isLoadingSuggestions, setIsLoadingSuggestions] = useState<boolean>(false);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
    const [showDocSelector, setShowDocSelector] = useState<boolean>(false);
    const chatEndRef = useRef<HTMLDivElement>(null);
    const hasInitialized = useRef<boolean>(false);

    // Load chat history from localStorage on mount
    useEffect(() => {
        if (!user?.user_id) return;

        const chatKey = `chat_session_${user.user_id}`;
        const savedSession = localStorage.getItem(chatKey);
        
        if (savedSession) {
            try {
                const { messages: savedMessages, suggestions: savedSuggestions, selectedDocIds: savedDocIds } = JSON.parse(savedSession);
                if (savedMessages && savedMessages.length > 0) {
                    setMessages(savedMessages);
                    setSuggestions(savedSuggestions || []);
                    setSelectedDocIds(savedDocIds || []);
                    hasInitialized.current = true; // Skip initial fetch if we have cached data
                    setIsLoading(false);
                }
            } catch (error) {
                console.error("Failed to load chat session:", error);
            }
        }
    }, [user?.user_id]);

    // Save chat history to localStorage whenever messages, suggestions, or selectedDocIds change
    useEffect(() => {
        if (!user?.user_id || messages.length === 0) return;

        const chatKey = `chat_session_${user.user_id}`;
        const sessionData = {
            messages,
            suggestions,
            selectedDocIds,
            timestamp: new Date().toISOString()
        };
        
        try {
            localStorage.setItem(chatKey, JSON.stringify(sessionData));
        } catch (error) {
            console.error("Failed to save chat session:", error);
        }
    }, [messages, suggestions, selectedDocIds, user?.user_id]);

    // Function to scroll to the bottom of the chat
    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Fetch user documents on mount
    useEffect(() => {
        const fetchDocuments = async () => {
            if (!user?.user_id) return;
            
            try {
                const response = await axios.get(`${API_BASE_URL}/api/documents/${user.user_id}`);
                setDocuments(response.data.documents || []);
            } catch (error) {
                console.error("Failed to fetch documents:", error);
            }
        };
        fetchDocuments();
    }, [user]);

    // Initial message to welcome the user and get first suggestions
    useEffect(() => {
        const fetchInitialGreeting = async () => {
            if (!user?.user_id || !user?.role) {
                setMessages([{ sender: 'portal', content: "Please log in to start chatting." }]);
                setIsLoading(false);
                return;
            }

            // Prevent duplicate calls
            if (hasInitialized.current) {
                return;
            }
            hasInitialized.current = true;

            // Start with a greeting from the portal
            const greeting = "Hello! I'm your Personal Learning Portal. Ask me a question or choose a prompt below to get started.";
            setMessages([{ sender: 'portal', content: greeting }]);

            // Fetch initial suggestions
            setIsLoadingSuggestions(true);
            try {
                const response = await axios.post(`${API_BASE_URL}/chat/`, {
                    user_id: user.user_id,
                    user_role: user.role,
                    is_initial: true,
                });
                
                // Extract suggestions from the response
                // For initial request, backend returns learning_options instead of suggestions
                const learningOptions = response.data.learning_options || [];
                const suggestions = response.data.suggestions || [];
                
                // Use learning_options if available (initial), otherwise use suggestions
                let suggestionTexts: string[] = [];
                if (learningOptions.length > 0) {
                    suggestionTexts = learningOptions.map((opt: any) => opt.title || opt.description);
                } else if (suggestions.length > 0) {
                    suggestionTexts = suggestions.map((s: any) => s.text || s);
                }
                
                setSuggestions(suggestionTexts);
            } catch (error) {
                console.error("Failed to fetch initial suggestions:", error);
                setMessages(prev => [...prev, { sender: 'portal', content: "Sorry, I couldn't load suggestions right now."}]);
            } finally {
                setIsLoading(false);
                setIsLoadingSuggestions(false);
            }
        };
        fetchInitialGreeting();
    }, [user]);

    const handleSubmitQuery = async (query: string) => {
        if (!query || isLoading || !user?.user_id || !user?.role) return;

        setIsLoading(true);
        setIsLoadingSuggestions(true);
        // Add user message to chat immediately for snappy UI
        setMessages(prev => [...prev, { sender: 'user', content: query }]);
        setInputValue(''); // Clear input field

        try {
            const response = await axios.post(`${API_BASE_URL}/chat/`, {
                content: query,
                user_id: user.user_id,
                user_role: user.role,
                selected_documents: selectedDocIds.length > 0 ? selectedDocIds : undefined,
            });
            const { answer, suggestions: newSuggestions, learning_options: learningOptions } = response.data;

            // Add portal's response and update suggestions
            setMessages(prev => [...prev, { sender: 'portal', content: answer }]);
            
            // Extract suggestion texts (handle both formats)
            let suggestionTexts: string[] = [];
            if (learningOptions && learningOptions.length > 0) {
                suggestionTexts = learningOptions.map((opt: any) => opt.title || opt.description);
            } else if (newSuggestions && newSuggestions.length > 0) {
                suggestionTexts = newSuggestions.map((s: any) => s.text || s);
            }
            
            setSuggestions(suggestionTexts);

        } catch (error) {
            console.error("Error fetching chat response:", error);
            setMessages(prev => [...prev, { sender: 'portal', content: "Sorry, something went wrong. Please try again."}]);
        } finally {
            setIsLoading(false);
            setIsLoadingSuggestions(false);
        }
    };

    const toggleDocumentSelection = (docId: string) => {
        setSelectedDocIds(prev => 
            prev.includes(docId) 
                ? prev.filter(id => id !== docId)
                : [...prev, docId]
        );
    };

    const clearChatHistory = () => {
        if (window.confirm('Are you sure you want to clear the chat history? This cannot be undone.')) {
            if (user?.user_id) {
                localStorage.removeItem(`chat_session_${user.user_id}`);
            }
            setMessages([]);
            setSuggestions([]);
            setSelectedDocIds([]);
            hasInitialized.current = false;
            
            // Re-initialize chat
            const greeting = "Hello! I'm your Personal Learning Portal. Ask me a question or choose a prompt below to get started.";
            setMessages([{ sender: 'portal', content: greeting }]);
            
            // Fetch fresh suggestions
            if (user?.user_id && user?.role) {
                setIsLoadingSuggestions(true);
                axios.post(`${API_BASE_URL}/chat/`, {
                    user_id: user.user_id,
                    user_role: user.role,
                    is_initial: true,
                }).then(response => {
                    const learningOptions = response.data.learning_options || [];
                    const suggestions = response.data.suggestions || [];
                    let suggestionTexts: string[] = [];
                    if (learningOptions.length > 0) {
                        suggestionTexts = learningOptions.map((opt: any) => opt.title || opt.description);
                    } else if (suggestions.length > 0) {
                        suggestionTexts = suggestions.map((s: any) => s.text || s);
                    }
                    setSuggestions(suggestionTexts);
                }).catch(error => {
                    console.error("Failed to fetch suggestions:", error);
                }).finally(() => {
                    setIsLoadingSuggestions(false);
                });
            }
        }
    };

    return (
        <div className={styles.chatContainer}>
            {/* Clear Chat Button */}
            {messages.length > 1 && (
                <div className={styles.clearChatContainer}>
                    <button onClick={clearChatHistory} className={styles.clearChatButton}>
                        Clear Chat History
                    </button>
                </div>
            )}
            
            <div className={styles.messageList}>
                {messages.map((msg, index) => (
                    <div key={index} className={`${styles.message} ${styles[msg.sender]}`}>
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                ))}
                {isLoading && <div className={`${styles.message} ${styles.portal}`}><span className={styles.loader}></span></div>}
                <div ref={chatEndRef} />
            </div>

            <div className={styles.suggestions}>
                {isLoadingSuggestions ? (
                    <div className={styles.suggestionsLoading}>
                        <span className={styles.loader}></span>
                        <span className={styles.loadingText}>Generating suggestions...</span>
                    </div>
                ) : (
                    suggestions.map((s, index) => (
                        <button key={index} onClick={() => handleSubmitQuery(s)} className={styles.suggestionButton}>
                            {s}
                        </button>
                    ))
                )}
            </div>

            <div className={styles.inputArea}>
                {/* Document Selector Dropdown */}
                {showDocSelector && (
                    <div className={styles.docListPopup}>
                        {documents.length > 0 ? (
                            <>
                                <div className={styles.docListHeader}>
                                    <span>Choose documents to include:</span>
                                    {selectedDocIds.length > 0 && (
                                        <button 
                                            className={styles.clearButton}
                                            onClick={() => setSelectedDocIds([])}
                                            type="button"
                                        >
                                            Clear all
                                        </button>
                                    )}
                                </div>
                                {documents.map(doc => (
                                    <label key={doc.document_id} className={styles.docItem}>
                                        <input
                                            type="checkbox"
                                            checked={selectedDocIds.includes(doc.document_id)}
                                            onChange={() => toggleDocumentSelection(doc.document_id)}
                                        />
                                        <span className={styles.docName}>{doc.filename}</span>
                                        <span className={styles.docType}>{doc.file_type}</span>
                                    </label>
                                ))}
                            </>
                        ) : (
                            <div className={styles.noDocuments}>
                                <p>No documents uploaded yet.</p>
                                <p>Upload documents in the "Add Content" section to use them in chat.</p>
                            </div>
                        )}
                    </div>
                )}
                
                <form className={styles.inputForm} onSubmit={(e) => { e.preventDefault(); handleSubmitQuery(inputValue); }}>
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Type your question here..."
                        className={styles.input}
                        disabled={isLoading}
                    />
                    <button 
                        type="button"
                        className={styles.docSelectorButton}
                        onClick={() => setShowDocSelector(!showDocSelector)}
                        title={selectedDocIds.length > 0 ? `${selectedDocIds.length} document(s) selected` : 'Select documents'}
                    >
                        📎 {selectedDocIds.length > 0 && `(${selectedDocIds.length})`}
                    </button>
                    <button type="submit" className={styles.sendButton} disabled={isLoading}>
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatComponent;