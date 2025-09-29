# AI Proficiency Survey & Data Storage

## 1. Survey Design

### Survey Questions
- **Role (Job Function)**  
  Options: `Finance`, `Marketing`, `Product`, `Data Science`, `Engineering`, `Operations`, `Other`

- **AI Proficiency Level**  
  Options: `Beginner`, `Intermediate`, `Advanced`

- **Learning Goals**  
  Options (checkboxes):  
  - Understand AI basics  
  - Apply AI in my role (automation, analysis)  
  - Prompt engineering / building AI apps  
  - Learn technical foundations (ML, NLP, etc.)  
  - Keep up with AI trends and ethics  

---

## 2. Database Design

### Relational DB: PostgreSQL

#### Table: `users`
| Field             | Type       | Description                                |
|-------------------|-----------|--------------------------------------------|
| `user_id` (PK)    | UUID      | Unique user identifier                     |
| `email`           | VARCHAR   | Login credential                           |
| `role`            | VARCHAR   | Job function                               |
| `proficiency`     | VARCHAR   | Beginner / Intermediate / Advanced         |
| `learning_goals`  | JSONB     | Array of selected goals                    |
| `learning_style`  | VARCHAR   | User preference                            |
| `time_commitment` | VARCHAR   | Time per week                              |
| `created_at`      | TIMESTAMP | Account creation time                      |
| `updated_at`      | TIMESTAMP | Last update                                |

#### Table: `progress`
| Field              | Type       | Description                                |
|--------------------|-----------|--------------------------------------------|
| `progress_id` (PK) | UUID      | Unique progress record                     |
| `user_id` (FK)     | UUID      | Links to users table                       |
| `completed_modules`| JSONB     | List of completed module IDs               |
| `quiz_scores`      | JSONB     | Mapping of module → score                  |
| `last_login`       | TIMESTAMP | Last active session                        |

---

## 3. Vector DB: Weaviate (Content + User Context)

### Example Metadata
```json
{
  "user_id": "1234",
  "topic": "use_cases",
  "difficulty": "beginner",
  "role": "finance",
  "content_id": "abc123"
}
