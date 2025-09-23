# Schema Design for Backend and Frontend

## Objective:
This document outlines the schema design for both backend and frontend components of our AI-driven learning application. The goal is to ensure consistent data structures that facilitate seamless interaction between the user interface and the underlying AI models.

## Frontend Structure:
Based on the requirements, the frontend will have the following key components:

### Sign up/ Login flow:
- **Sign-Up / Login**: For user authentication and profile management.
- **User Assessment**: Initial quiz to gauge user proficiency in AI concepts.

### Main Interface:
- **Chat Interface**: For user interactions with the AI.
- **Suggested Prompts**: To assist users in formulating effective prompts.
- **Prompt Refresh**: To generate new prompt suggestions.
- **Surprise Me**: A feature to provide random AI-related facts or tips catered to the user profile.
- **Response Display**: To show AI-generated responses.
- **Assessment Module**: For quizzes and evaluations.

### Schema Design:
#### Main Interface:
Request:

```json
{
  "requestId": "string",
  "userId": "string",
  "sessionId": "string",
  "message": "string",
  "selection": {
    "suggestedPrompts": true,
    "promptRefresh": true,
    "surpriseMe": true,
    "assessmentMode": false
  },
  "timestamp": "ISO8601 string"
}
```

Response:
```json
{
  "responseId": "string",
  "userId": "string",
  "sessionId": "string",
  "message": "string",
  "suggestedPrompts": ["string"],
  "links": ["string"],
  "assessmentMode": false,
  "assessmentDetails": {
    "questionId": "string",
    "options": ["string"],
    "correctOption": "string",
    "explanation": "string"
  },
  "timestamp": "ISO8601 string"
}
```

## Backend Structure:
Based on the requirements, the backend will have the following key components:

Learning Navigator Assistant:
Input: Context, User Profile, User Query

Output Schema:
```json
{
  "responseId": "string",
  "userId": "string",
  "sessionId": "string",
  "suggestedPrompts": ["string"],
  "assessmentMode": false,
  "timestamp": "ISO8601 string"
}
```

Trainer Agent:
Input: User Query, User Profile, Learning Context
Output Schema:
```json
{
  "responseId": "string",
  "userId": "string",
  "sessionId": "string",
  "message": "string",
  "assessmentMode": false,
  "timestamp": "ISO8601 string"
}
```

Curation Agent:
Input: User Query, User Profile, Learning Context
Output Schema:
```json
{
    "responseId": "string",
    "userId": "string",
    "sessionId": "string",
    "message": "string",
    "links": ["string"],
    "assessmentMode": false,
    "timestamp": "ISO8601 string"
}
```

## Assessment Agent:
Input: User Query, User Profile, Learning Context

Question Generation Output Schema:
```json
{
  "responseId": "string",
  "userId": "string",
  "sessionId": "string",
  "question": "string", 
  "options": ["string"],
  "correctOption": "string",
  "explanation": "string",
  "timestamp": "ISO8601 string",
  "assessmentMode": true
}
```



