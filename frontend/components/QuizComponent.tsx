'use client';

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import styles from './QuizComponent.module.css';

// Define the structure of our data
interface Topic {
    id: number;
    topic: string;
}

interface Question {
    question_text: string;
    options: { [key: string]: string };
    correct_answer: string;
    explanation: string;
}

interface QuizData {
    topic: string;
    questions: Question[];
}

const QuizComponent = () => {
    // State management for the entire quiz flow
    const [topics, setTopics] = useState<Topic[]>([]);
    const [selectedTopic, setSelectedTopic] = useState<string>('');
    const [quizData, setQuizData] = useState<QuizData | null>(null);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);
    const [userAnswers, setUserAnswers] = useState<{ [key: number]: string }>({});
    const [quizState, setQuizState] = useState<'topic_selection' | 'loading' | 'in_progress' | 'results'>('topic_selection');
    const [score, setScore] = useState<number>(0);

    // Fetch topics when the component mounts
    useEffect(() => {
        const fetchTopics = async () => {
            try {
                const response = await axios.get('http://127.0.0.1:8000/topics/');
                setTopics(response.data);
            } catch (error) {
                console.error("Failed to fetch topics:", error);
            }
        };
        fetchTopics();
    }, []);

    const handleStartQuiz = async () => {
        if (!selectedTopic) return;
        setQuizState('loading');
        try {
            // NOTE: Using your AssessmentAgent directly for simplicity.
            // In a real app, you'd call your `/assessment/start` endpoint.
            const response = await axios.post('http://127.0.0.1:8000/assessment/start', {
                topic: selectedTopic,
            });
            if (response.data && response.data.quiz_data) {
                setQuizData(response.data.quiz_data);
                setQuizState('in_progress');
            } else {
                console.error("The key 'quiz_data' was not found in the API response:", response.data);
                setQuizState('topic_selection');
            }

        } catch (error) {
            console.error("Failed to start quiz:", error);
            setQuizState('topic_selection');
        }
    };

    const handleAnswerSelect = (questionIndex: number, answer: string) => {
        setUserAnswers({ ...userAnswers, [questionIndex]: answer });
    };

    const handleNextQuestion = () => {
        if (currentQuestionIndex < quizData!.questions.length - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
        } else {
            // End of quiz, calculate score and show results
            let finalScore = 0;
            quizData!.questions.forEach((q, index) => {
                if (userAnswers[index] === q.correct_answer) {
                    finalScore++;
                }
            });
            setScore(finalScore);
            setQuizState('results');
        }
    };

    const restartQuiz = () => {
        // Reset all state to start over
        setSelectedTopic('');
        setQuizData(null);
        setCurrentQuestionIndex(0);
        setUserAnswers({});
        setScore(0);
        setQuizState('topic_selection');
    };

    // --- Render different views based on the quiz state ---

    if (quizState === 'loading') {
        return <div className={styles.container}><div className={styles.loader}></div><p>Generating your quiz...</p></div>;
    }

    if (quizState === 'results') {
        return (
            <div className={`${styles.container} ${styles.resultsContainer}`}>
                <h2>Quiz Results</h2>
                <p className={styles.score}>You scored {score} out of {quizData!.questions.length}</p>
                <div className={styles.review}>
                    {quizData!.questions.map((q, index) => (
                        <div key={index} className={styles.reviewItem}>
                            <p><strong>{index + 1}. {q.question_text}</strong></p>
                            <p className={userAnswers[index] === q.correct_answer ? styles.correct : styles.incorrect}>
                                Your answer: {q.options[userAnswers[index]]}
                            </p>
                            {userAnswers[index] !== q.correct_answer && (
                                <p className={styles.correct}>Correct answer: {q.options[q.correct_answer]}</p>
                            )}
                            <p className={styles.explanation}><em>Explanation: {q.explanation}</em></p>
                        </div>
                    ))}
                </div>
                <button onClick={restartQuiz} className={styles.button}>Try Another Topic</button>
            </div>
        );
    }

    if (quizState === 'in_progress' && quizData) {
        const currentQuestion = quizData.questions[currentQuestionIndex];
        return (
            <div className={styles.container}>
                <h2>{quizData.topic} Quiz</h2>
                <div className={styles.progress}>Question {currentQuestionIndex + 1} of {quizData.questions.length}</div>
                <p className={styles.questionText}>{currentQuestion.question_text}</p>
                <div className={styles.options}>
                    {Object.entries(currentQuestion.options).map(([key, value]) => (
                        <button
                            key={key}
                            onClick={() => handleAnswerSelect(currentQuestionIndex, key)}
                            className={`${styles.optionButton} ${userAnswers[currentQuestionIndex] === key ? styles.selected : ''}`}
                        >
                            <span className={styles.optionKey}>{key.toUpperCase()}</span> {value}
                        </button>
                    ))}
                </div>
                <button onClick={handleNextQuestion} disabled={!userAnswers[currentQuestionIndex]} className={styles.button}>
                    {currentQuestionIndex === quizData.questions.length - 1 ? 'Finish Quiz' : 'Next Question'}
                </button>
            </div>
        );
    }

    // Default view: Topic Selection
    return (
        <div className={styles.container}>
            <h2>Start a New Quiz</h2>
            <p>Select a topic from your learned subjects to test your knowledge.</p>
            <select
                value={selectedTopic}
                onChange={(e) => setSelectedTopic(e.target.value)}
                className={styles.select}
            >
                <option value="" disabled>-- Choose a topic --</option>
                {topics.map(topic => (
                    <option key={topic.id} value={topic.topic}>{topic.topic}</option>
                ))}
            </select>
            <button onClick={handleStartQuiz} disabled={!selectedTopic} className={styles.button}>
                Start Quiz
            </button>
        </div>
    );
};

export default QuizComponent;