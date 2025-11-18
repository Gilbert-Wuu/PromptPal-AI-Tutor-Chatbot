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
    const [isWelcomeView, setIsWelcomeView] = useState<boolean>(true); // Track if we're in welcome view
    const chatEndRef = useRef<HTMLDivElement>(null);
    const docSelectorRef = useRef<HTMLDivElement>(null); // Ref for document selector popup
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
                    setIsWelcomeView(false); // If we have messages, show conversation view
                    hasInitialized.current = true; // Skip initial fetch if we have cached data
                    setIsLoading(false);
                }
            } catch (error) {
                console.error("Failed to load chat session:", error);
            }
        }

        // Listen for reset event from Header (when logo is clicked)
        const handleReset = () => {
            setMessages([]);
            setSuggestions([]);
            setSelectedDocIds([]);
            setIsWelcomeView(true);
            hasInitialized.current = false;
            setIsLoading(true);
        };

        window.addEventListener('resetChat', handleReset);
        return () => window.removeEventListener('resetChat', handleReset);
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

    // Close document selector when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (docSelectorRef.current && !docSelectorRef.current.contains(event.target as Node)) {
                // Check if the click is also not on the button that toggles the selector
                const target = event.target as HTMLElement;
                if (!target.closest(`.${styles.docSelectorButton}`)) {
                    setShowDocSelector(false);
                }
            }
        };

        // Add event listener when popup is shown
        if (showDocSelector) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        // Cleanup
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [showDocSelector]);

    const handleSubmitQuery = async (query: string) => {
        if (!query || isLoading || !user?.user_id || !user?.role) return;

        // Switch from welcome view to conversation view
        if (isWelcomeView) {
            setIsWelcomeView(false);
        }

        setIsLoading(true);
        setIsLoadingSuggestions(true);
        
        // Display the original query in UI
        setMessages(prev => [...prev, { sender: 'user', content: query }]);
        setInputValue(''); // Clear input field

        // Format query for backend: add "How to use AI in" prefix
        const formattedQuery = `How to use AI in ${query}`;

        try {
            const response = await axios.post(`${API_BASE_URL}/chat/`, {
                content: formattedQuery,  // Send formatted query to backend
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

    const refreshSuggestions = async () => {
        if (!user?.user_id || !user?.role || isLoadingSuggestions) return;
        
        setIsLoadingSuggestions(true);
        try {
            const response = await axios.post(`${API_BASE_URL}/chat/`, {
                user_id: user.user_id,
                user_role: user.role,
                is_initial: true,
            });
            
            const learningOptions = response.data.learning_options || [];
            const suggestions = response.data.suggestions || [];
            let suggestionTexts: string[] = [];
            if (learningOptions.length > 0) {
                suggestionTexts = learningOptions.map((opt: any) => opt.title || opt.description);
            } else if (suggestions.length > 0) {
                suggestionTexts = suggestions.map((s: any) => s.text || s);
            }
            
            setSuggestions(suggestionTexts);
        } catch (error) {
            console.error("Failed to refresh suggestions:", error);
        } finally {
            setIsLoadingSuggestions(false);
        }
    };

    const clearChatHistory = () => {
        if (user?.user_id) {
            localStorage.removeItem(`chat_session_${user.user_id}`);
        }
        setMessages([]);
        setSuggestions([]);
        setSelectedDocIds([]);
        hasInitialized.current = false;
        setIsWelcomeView(true); // Return to welcome view
        setIsLoading(true);
        
        // Fetch fresh suggestions for welcome view
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
                setIsLoading(false);
            });
        } else {
            setIsLoading(false);
        }
    };

    // WELCOME VIEW - Similar to Figma Make
    if (isWelcomeView) {
        return (
            <div className={styles.welcomeContainer}>
                <div className={styles.welcomeContent}>
                    <div className={styles.welcomeHeader}>
                        <div className={styles.sparkle}>✨</div>
                        <h1 className={styles.welcomeTitle}>Ready to unlock the power of AI?</h1>
                        <p className={styles.welcomeSubtitle}>Discover how AI tools can transform your {user?.role} daily work and boost your productivity - no technical background needed!</p>
                    </div>

                    <div className={styles.welcomeInputSection}>
                        <form 
                            className={styles.welcomeInputForm} 
                            onSubmit={(e) => { 
                                e.preventDefault(); 
                                if (inputValue.trim()) handleSubmitQuery(inputValue); 
                            }}
                        >
                            <input
                                type="text"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                placeholder="What do you want to learn..."
                                className={styles.welcomeInput}
                                disabled={isLoading}
                                autoFocus
                            />
                            <button type="submit" className={styles.welcomeSendButton} disabled={isLoading || !inputValue.trim()}>
                                →
                            </button>
                        </form>
                    </div>

                    <div className={styles.welcomeSuggestionsContainer}>
                        <h2 className={styles.suggestionsHeader}>How to use AI in tasks like ...</h2>
                        <div className={styles.welcomeSuggestions}>
                            {isLoadingSuggestions ? (
                                <div className={styles.loadingContainer}>
                                    <span className={styles.loader}></span>
                                    <span className={styles.loadingText}>Generating personalized prompts...</span>
                                </div>
                            ) : (
                                suggestions.slice(0, 5).map((suggestion, index) => (
                                    <button
                                        key={index}
                                        onClick={() => handleSubmitQuery(suggestion)}
                                        className={styles.welcomeSuggestionCard}
                                    >
                                        <div className={styles.suggestionContent}>
                                            <span className={styles.suggestionText}>{suggestion}</span>
                                        </div>
                                    </button>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // CONVERSATION VIEW - Similar to Leonardo AI
    return (
        <div className={styles.conversationContainer}>
            {/* Clear Chat Button */}
            {messages.length > 0 && (
                <button onClick={clearChatHistory} className={styles.newChatButton} title="Start new chat">
                    + New Chat
                </button>
            )}
            
            {/* Messages */}
            <div className={styles.messageList}>
                {messages.map((msg, index) => (
                    <div key={index} className={`${styles.message} ${styles[msg.sender]}`}>
                        <div className={styles.messageContent}>
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className={`${styles.message} ${styles.portal}`}>
                        <div className={styles.messageContent}>
                            <span className={styles.loader}></span>
                        </div>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            {/* Suggestions above input */}
            {suggestions.length > 0 && (
                <div className={styles.conversationSuggestionsContainer}>
                    <div className={styles.suggestionsHeaderRow}>
                        <h3 className={styles.conversationSuggestionsHeader}>How to use AI in</h3>
                        {!isLoadingSuggestions && (
                            <button 
                                onClick={refreshSuggestions} 
                                className={styles.refreshButton}
                                title="Get new suggestions"
                            >
                                🔄
                            </button>
                        )}
                    </div>
                    <div className={styles.conversationSuggestions}>
                        {isLoadingSuggestions ? (
                            <div className={styles.suggestionsLoading}>
                                <span className={styles.loader}></span>
                                <span className={styles.loadingText}>Generating suggestions...</span>
                            </div>
                        ) : (
                            suggestions.slice(0, 5).map((s, index) => (
                                <button 
                                    key={index} 
                                    onClick={() => handleSubmitQuery(s)} 
                                    className={styles.conversationSuggestionButton}
                                >
                                    {s}
                                </button>
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* Input Area */}
            <div className={styles.inputArea}>
                {/* Document Selector Dropdown */}
                {showDocSelector && (
                    <div ref={docSelectorRef} className={styles.docListPopup}>
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
                
                <form className={styles.inputForm} onSubmit={(e) => { e.preventDefault(); if (inputValue.trim()) handleSubmitQuery(inputValue); }}>
                    <button 
                        type="button"
                        className={styles.docSelectorButton}
                        onClick={() => setShowDocSelector(!showDocSelector)}
                        title={selectedDocIds.length > 0 ? `${selectedDocIds.length} document(s) selected` : 'Select documents'}
                    >
                        📎 {selectedDocIds.length > 0 && `(${selectedDocIds.length})`}
                    </button>
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="What do you want to see..."
                        className={styles.input}
                        disabled={isLoading}
                    />
                    <button type="submit" className={styles.sendButton} disabled={isLoading || !inputValue.trim()}>
                        →
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatComponent;