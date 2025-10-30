'use client';

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import styles from './ChatComponent.module.css';

// Define the structure of a chat message
interface Message {
    sender: 'user' | 'portal';
    content: string;
}

const ChatComponent = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [inputValue, setInputValue] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(true); // Start loading initially
    const chatEndRef = useRef<HTMLDivElement>(null);

    // Function to scroll to the bottom of the chat
    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Initial message to welcome the user and get first suggestions
    useEffect(() => {
        const fetchInitialGreeting = async () => {
            // Start with a greeting from the portal
            const greeting = "Hello! I'm your Personal Learning Portal. Ask me a question or choose a prompt below to get started.";
            setMessages([{ sender: 'portal', content: greeting }]);

            // Fetch initial suggestions
            try {
                const response = await axios.post('http://127.0.0.1:8000/chat/', {
                    content: "Initial greeting", // A dummy message to trigger the navigator
                });
                // We only care about the suggestions here, not the answer
                setSuggestions(response.data.suggestions);
            } catch (error) {
                console.error("Failed to fetch initial suggestions:", error);
                setMessages(prev => [...prev, { sender: 'portal', content: "Sorry, I couldn't load suggestions right now."}]);
            } finally {
                setIsLoading(false);
            }
        };
        fetchInitialGreeting();
    }, []);

    const handleSubmitQuery = async (query: string) => {
        if (!query || isLoading) return;

        setIsLoading(true);
        // Add user message to chat immediately for snappy UI
        setMessages(prev => [...prev, { sender: 'user', content: query }]);
        setInputValue(''); // Clear input field

        try {
            const response = await axios.post('http://127.0.0.1:8000/chat/', {
                content: query,
            });
            const { answer, suggestions: newSuggestions } = response.data;

            // Add portal's response and update suggestions
            setMessages(prev => [...prev, { sender: 'portal', content: answer }]);
            setSuggestions(newSuggestions);

        } catch (error) {
            console.error("Error fetching chat response:", error);
            setMessages(prev => [...prev, { sender: 'portal', content: "Sorry, something went wrong. Please try again."}]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.chatContainer}>
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
                {suggestions.map((s, index) => (
                    <button key={index} onClick={() => handleSubmitQuery(s)} className={styles.suggestionButton}>
                        {s}
                    </button>
                ))}
            </div>

            <form className={styles.inputForm} onSubmit={(e) => { e.preventDefault(); handleSubmitQuery(inputValue); }}>
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Type your question here..."
                    className={styles.input}
                    disabled={isLoading}
                />
                <button type="submit" className={styles.sendButton} disabled={isLoading}>
                    Send
                </button>
            </form>
        </div>
    );
};

export default ChatComponent;