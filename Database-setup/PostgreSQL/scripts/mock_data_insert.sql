-- ============================================
-- Mock Data Script
-- ============================================

-- Clear existing data (optional - comment out if you want to keep existing data)
-- TRUNCATE TABLE interactions CASCADE;
-- TRUNCATE TABLE progress CASCADE;
-- TRUNCATE TABLE users CASCADE;

-- ============================================
-- USERS MOCK DATA
-- ============================================

INSERT INTO users (email, role, short_term_summary, long_term_summary) VALUES
-- Finance Users
('sarah.chen@company.com', 'Finance', 
 'Recent sessions focused on understanding LLM fundamentals and prompt engineering for financial analysis. Completed modules on document Q&A and comparison analysis. Asked detailed questions about using AI for 10-K analysis and regulatory compliance. Struggling slightly with advanced prompt techniques.',
 'Strong analytical background with focus on financial documentation. Consistently interested in practical applications for regulatory compliance and financial reporting. Shows aptitude for structured thinking but needs more practice with creative prompt engineering. Key milestone: Successfully implemented document comparison workflow for quarterly reports.'),

('michael.ross@company.com', 'Finance',
 'Last three sessions covered AI safety and ethics in financial applications. Working through intermediate prompt engineering techniques. Recently explored use cases for risk assessment and portfolio analysis. Shows good understanding of context setting.',
 'Finance professional with 5+ years experience. Quick learner with systematic approach to AI concepts. Strengths: data analysis, compliance understanding. Weaknesses: technical implementation details. Completed 8 modules with average quiz score of 85%. Primary interest in automation of repetitive tasks.'),

-- Marketing Users
('emily.johnson@company.com', 'Marketing',
 'Currently exploring content generation and brand voice consistency using LLMs. Completed beginner prompt engineering modules. Recent focus on campaign ideation and A/B testing copy variations. Asking questions about maintaining brand guidelines in AI outputs.',
 'Creative marketer transitioning to AI-enhanced workflows. Excels at understanding user personas and crafting targeted messages. Learning curve with technical concepts but strong practical application skills. Milestone: Created automated email campaign generator. Consistently achieves 90%+ on creative application quizzes.'),

('david.kim@company.com', 'Marketing',
 'Working through advanced prompt techniques for market research analysis. Recent sessions on competitive analysis automation and sentiment analysis. Completed modules on clear instructions and output formatting. Interested in social media monitoring.',
 'Digital marketing specialist with strong analytical bent. Balanced creative and data-driven approach. Quick to grasp AI concepts and translate to marketing contexts. Weakness: Sometimes over-complicates prompts. Strength: Excellent at iterative refinement. 12 modules completed.'),

-- Product Users
('lisa.wang@company.com', 'Product',
 'Recent focus on user story generation and PRD automation. Exploring few-shot prompting for feature prioritization. Completed intermediate modules on context setting and chain-of-thought reasoning. Questions about integrating AI into product development cycles.',
 'Senior PM with technical background. Natural understanding of AI capabilities and limitations. Strengths: systematic thinking, user empathy, technical translation. Growth area: creative exploration of AI possibilities. Key achievement: Implemented AI-assisted user research workflow.'),

('james.martinez@company.com', 'Product',
 'Last sessions covered requirements gathering automation and stakeholder communication templates. Working on advanced prompt engineering for technical documentation. Shows strong grasp of structured output formatting.',
 'Product manager focusing on B2B solutions. Methodical learner with emphasis on practical implementation. Completed 15 modules with 88% average score. Particularly interested in AI for competitive analysis and roadmap planning. Building expertise in prompt templates.'),

-- Data Science Users
('priya.patel@company.com', 'Data Science',
 'Advanced user exploring fine-tuning concepts and model evaluation. Recent sessions on prompt optimization for data analysis tasks. Completed all fundamental modules. Current focus: integrating LLMs with existing ML pipelines.',
 'Experienced data scientist with deep technical knowledge. Fast learner who quickly grasps advanced concepts. Strengths: technical implementation, experimental design. Growth area: business application communication. Milestone: Created custom evaluation framework for LLM outputs. Perfect quiz scores across 20+ modules.'),

('alex.nguyen@company.com', 'Data Science',
 'Working through advanced prompt engineering for code generation and debugging. Recent interest in RAG systems and vector databases. Completed modules on AI safety and ethical considerations. Questions about model limitations.',
 'ML engineer transitioning to LLM applications. Strong programming background with focus on production systems. Excels at technical implementation but working on business context understanding. 18 modules completed. Primary interest: Building scalable AI solutions.'),

-- Engineering Users
('robert.taylor@company.com', 'Engineering',
 'Currently learning prompt engineering for code review and documentation. Recent sessions on debugging assistance and test generation. Completed beginner modules. Showing interest in API integration patterns.',
 'Software engineer new to AI/ML. Pragmatic approach focused on immediate productivity gains. Strengths: systematic debugging, clear documentation. Learning curve: understanding model capabilities. Milestone: Automated 30% of code review process. Quiz average: 82%.'),

('maria.gonzalez@company.com', 'Engineering',
 'Exploring advanced techniques for system design and architecture documentation. Recent focus on using AI for technical debt identification. Completed intermediate prompt engineering. Questions about security considerations.',
 'Senior engineer with 10+ years experience. Cautious but thorough approach to AI adoption. Strong focus on reliability and security. Weakness: Sometimes overthinks prompt complexity. Strength: Excellent at creating reusable templates. 14 modules completed.'),

-- Operations Users
('kevin.lee@company.com', 'Operations',
 'Recent sessions on process automation and workflow optimization. Working through modules on clear instructions and output formatting. Interested in inventory management and supply chain applications. Completed basic prompt engineering.',
 'Operations manager seeking efficiency improvements. Practical mindset with focus on ROI. Strengths: process thinking, stakeholder management. Growth area: technical understanding. Key achievement: Reduced report generation time by 60%. Average quiz score: 78%.'),

('amanda.white@company.com', 'Operations',
 'Currently exploring AI for capacity planning and resource allocation. Recent focus on data extraction from operational reports. Completed intermediate modules. Questions about integration with existing systems.',
 'Operations analyst with strong Excel background. Methodical learner with attention to detail. Excels at identifying automation opportunities. Working on creative problem-solving with AI. 10 modules completed. Primary focus: Operational reporting automation.');

-- ============================================
-- PROGRESS MOCK DATA (Auto-created by trigger)
-- Note: The trigger automatically creates progress records,
-- but we'll update them with realistic data
-- ============================================

-- Update progress for Sarah Chen (Finance)
UPDATE progress SET
    completed_modules = '["ai_concept_001", "ai_concept_002", "ai_concept_003", "use_case_002", "use_case_003"]'::jsonb,
    quiz_scores = '{"ai_concept_001": 85, "ai_concept_002": 90, "ai_concept_003": 80, "use_case_002": 88, "use_case_003": 92}'::jsonb,
    interaction_log = '{
        "last_prompts": ["How do I analyze 10-K documents?", "Best practices for financial compliance checks"],
        "recent_topics": ["document_analysis", "compliance", "prompt_engineering"],
        "preferences": {"learning_style": "examples", "pace": "moderate", "focus_area": "practical_applications"}
    }'::jsonb,
    last_login = CURRENT_TIMESTAMP - INTERVAL '2 hours'
WHERE user_id = (SELECT user_id FROM users WHERE email = 'sarah.chen@company.com');

-- Update progress for Emily Johnson (Marketing)
UPDATE progress SET
    completed_modules = '["ai_concept_001", "ai_concept_002", "ai_concept_004", "ai_concept_005", "use_case_001"]'::jsonb,
    quiz_scores = '{"ai_concept_001": 95, "ai_concept_002": 88, "ai_concept_004": 90, "ai_concept_005": 92, "use_case_001": 94}'::jsonb,
    interaction_log = '{
        "last_prompts": ["Generate email campaign for product launch", "Maintain brand voice in AI content"],
        "recent_topics": ["content_generation", "brand_consistency", "campaign_creation"],
        "preferences": {"learning_style": "visual", "pace": "fast", "focus_area": "creative_applications"}
    }'::jsonb,
    last_login = CURRENT_TIMESTAMP - INTERVAL '1 day'
WHERE user_id = (SELECT user_id FROM users WHERE email = 'emily.johnson@company.com');

-- Update progress for Priya Patel (Data Science)
UPDATE progress SET
    completed_modules = '["ai_concept_001", "ai_concept_002", "ai_concept_003", "ai_concept_004", "ai_concept_005", "ai_concept_006", "ai_concept_007", "ai_concept_008", "ai_concept_009", "ai_concept_010", "ai_concept_011", "ai_concept_012", "ai_concept_013", "ai_concept_014", "ai_concept_015", "ai_concept_016", "ai_concept_017", "ai_concept_018", "ai_concept_019", "ai_concept_020"]'::jsonb,
    quiz_scores = '{"ai_concept_001": 100, "ai_concept_002": 100, "ai_concept_003": 98, "ai_concept_004": 100, "ai_concept_005": 100, "ai_concept_006": 100, "ai_concept_007": 98, "ai_concept_008": 100, "ai_concept_009": 100, "ai_concept_010": 100}'::jsonb,
    interaction_log = '{
        "last_prompts": ["Optimize prompts for data pipeline", "RAG implementation best practices", "Fine-tuning strategies"],
        "recent_topics": ["advanced_techniques", "model_optimization", "system_integration"],
        "preferences": {"learning_style": "technical", "pace": "advanced", "focus_area": "technical_depth"}
    }'::jsonb,
    last_login = CURRENT_TIMESTAMP - INTERVAL '3 hours'
WHERE user_id = (SELECT user_id FROM users WHERE email = 'priya.patel@company.com');

-- Update progress for Robert Taylor (Engineering)
UPDATE progress SET
    completed_modules = '["ai_concept_001", "ai_concept_002", "ai_concept_003", "use_case_004"]'::jsonb,
    quiz_scores = '{"ai_concept_001": 80, "ai_concept_002": 85, "ai_concept_003": 82, "use_case_004": 78}'::jsonb,
    interaction_log = '{
        "last_prompts": ["Generate unit tests for Python", "Code review automation", "Documentation from code"],
        "recent_topics": ["code_generation", "testing", "documentation"],
        "preferences": {"learning_style": "hands-on", "pace": "steady", "focus_area": "developer_productivity"}
    }'::jsonb,
    last_login = CURRENT_TIMESTAMP - INTERVAL '6 hours'
WHERE user_id = (SELECT user_id FROM users WHERE email = 'robert.taylor@company.com');

-- Update progress for Kevin Lee (Operations)
UPDATE progress SET
    completed_modules = '["ai_concept_001", "ai_concept_002", "use_case_001"]'::jsonb,
    quiz_scores = '{"ai_concept_001": 75, "ai_concept_002": 80, "use_case_001": 78}'::jsonb,
    interaction_log = '{
        "last_prompts": ["Automate inventory reports", "Process optimization suggestions"],
        "recent_topics": ["automation", "reporting", "process_improvement"],
        "preferences": {"learning_style": "practical", "pace": "moderate", "focus_area": "operational_efficiency"}
    }'::jsonb,
    last_login = CURRENT_TIMESTAMP - INTERVAL '1 day 2 hours'
WHERE user_id = (SELECT user_id FROM users WHERE email = 'kevin.lee@company.com');

-- ============================================
-- INTERACTIONS MOCK DATA
-- ============================================

-- Sarah Chen's recent interactions
INSERT INTO interactions (user_id, log, timestamp) VALUES
((SELECT user_id FROM users WHERE email = 'sarah.chen@company.com'),
 'User: How can I use AI to analyze 10-K documents more efficiently?
AI Tutor: Great question! Analyzing 10-K documents with AI can significantly improve your efficiency. Here are the key approaches:

1. **Document Q&A**: Upload the 10-K and ask specific questions like "What were the main risk factors?" or "Summarize the MD&A section"
2. **Comparison Analysis**: Compare multiple years to identify changes in risk factors, financial metrics, or business strategy
3. **Key Information Extraction**: Use prompts to extract specific data points like revenue segments, geographic breakdowns, or executive compensation

For prompt engineering, try this structure:
"Analyze the uploaded 10-K document and provide:
- Top 5 financial risks mentioned
- Year-over-year revenue changes by segment
- Key strategic initiatives discussed in MD&A
Format as a structured summary with bullet points"

Would you like to practice with a specific section of a 10-K?',
 CURRENT_TIMESTAMP - INTERVAL '2 hours'),

((SELECT user_id FROM users WHERE email = 'sarah.chen@company.com'),
 'User: Yes, I want to focus on extracting and comparing risk factors across multiple years. What''s the best approach?
AI Tutor: Excellent focus area! Risk factor comparison is crucial for understanding evolving business challenges. Here''s a systematic approach:

**Step 1: Structured Extraction Template**
```
For each 10-K document, extract:
1. List all risk factors with brief descriptions
2. Categorize risks (operational, financial, regulatory, market, technological)
3. Identify new risks not present in previous year
4. Note risks that were removed
5. Highlight changes in risk priority/ordering
```

**Step 2: Comparison Framework**
Use this prompt template:
"Compare risk factors between [Year1] and [Year2] 10-K filings:
- New risks added
- Risks removed
- Material changes in existing risk descriptions
- Changes in risk ordering/emphasis
Create a risk evolution matrix"

**Step 3: Trend Analysis**
Track risk themes over 3-5 years to identify:
- Emerging patterns
- Increasing/decreasing emphasis
- Industry-wide vs company-specific risks

Try this with your next set of 10-Ks and let me know what insights you discover!',
 CURRENT_TIMESTAMP - INTERVAL '1 hour 45 minutes'),

-- Emily Johnson's interactions
((SELECT user_id FROM users WHERE email = 'emily.johnson@company.com'),
 'User: I need to create email campaigns that maintain our brand voice. How do I ensure AI-generated content stays on-brand?
AI Tutor: Maintaining brand voice consistency is essential for marketing success! Here''s how to ensure AI-generated content stays on-brand:

**1. Create a Brand Voice Profile**
Include in your prompts:
- Tone attributes (e.g., "professional yet approachable")
- Key phrases and terminology your brand uses
- Things to avoid (jargon, certain words, etc.)

**2. Use Few-Shot Examples**
Provide 2-3 examples of on-brand content:
```
Example 1: [Your previous successful email]
Example 2: [Another on-brand message]

Now create a similar email for [new campaign] maintaining this voice.
```

**3. Structured Brand Guidelines in Prompts**
"Create an email campaign with these brand requirements:
- Tone: Friendly, knowledgeable, not salesy
- Style: Short sentences, active voice, conversational
- Must include: Our signature greeting
- Avoid: Technical jargon, aggressive CTAs"

**4. Iterative Refinement**
Start with a base generation, then refine:
"Adjust this email to be more [specific brand attribute]"

Would you like to work through an example with your specific brand guidelines?',
 CURRENT_TIMESTAMP - INTERVAL '1 day'),

-- Priya Patel's advanced interactions
((SELECT user_id FROM users WHERE email = 'priya.patel@company.com'),
 'User: I''m implementing a RAG system for our internal documentation. What are the key considerations for prompt optimization in this context?
AI Tutor: Excellent question! RAG system prompt optimization requires careful consideration of several technical factors:

**1. Retrieval-Augmented Prompt Structure**
```python
def create_rag_prompt(query, context_chunks, metadata):
    return f"""
    Using the following context, answer the query.
    
    Context (relevance scores included):
    {format_contexts(context_chunks, metadata)}
    
    Query: {query}
    
    Instructions:
    - Synthesize information from multiple sources
    - Indicate confidence based on context relevance
    - Flag if context is insufficient
    """
```

**2. Context Window Optimization**
- Balance context richness vs token limits
- Implement dynamic context selection based on relevance scores
- Consider hierarchical summarization for large document sets

**3. Prompt Engineering for Accuracy**
Key techniques:
- **Source Attribution**: "Cite specific documents when answering"
- **Confidence Scoring**: "Rate answer confidence based on context quality"
- **Fallback Behavior**: "If context insufficient, indicate what additional information needed"

**4. Performance Optimization**
- Cache frequently used prompts
- Implement prompt compression techniques
- Use prompt templates with variable injection

**5. Evaluation Framework**
```python
# Metrics to track
- Retrieval precision/recall
- Answer accuracy vs ground truth
- Response latency
- User satisfaction scores
```

Want to dive deeper into embedding strategies or reranking approaches?',
 CURRENT_TIMESTAMP - INTERVAL '3 hours'),

-- Robert Taylor's engineering focused interaction
((SELECT user_id FROM users WHERE email = 'robert.taylor@company.com'),
 'User: How can I use AI to generate unit tests for my Python code?
AI Tutor: Great application for improving code quality! Here''s how to effectively generate unit tests with AI:

**1. Basic Test Generation Prompt**
```
Generate comprehensive unit tests for this Python function:
[paste your function]

Requirements:
- Use pytest framework
- Include edge cases
- Test happy path and error conditions
- Add descriptive test names
- Include assertions for all return values
```

**2. Structured Approach for Complex Functions**
```python
# Provide context about the function
"""
Function purpose: [describe what it does]
Input types: [expected input types]
Output: [expected output]
Dependencies: [external dependencies]
"""

# Then request specific test scenarios
Generate tests for:
1. Normal inputs
2. Boundary conditions  
3. Invalid inputs
4. Performance considerations
```

**3. Test-Driven Development (TDD) Approach**
You can even use AI to help with TDD:
"Given these requirements: [requirements]
1. Generate test cases first
2. Then provide implementation
3. Ensure 100% test coverage"

**4. Best Practices Template**
```python
# AI-generated tests should include:
import pytest
from unittest.mock import Mock, patch

class TestYourFunction:
    def setup_method(self):
        # Setup test data
        
    def test_normal_case(self):
        # Happy path test
        
    def test_edge_case(self):
        # Boundary conditions
        
    def test_error_handling(self):
        # Error scenarios
```

Try this with one of your functions and I can help refine the tests!',
 CURRENT_TIMESTAMP - INTERVAL '6 hours'),

-- Kevin Lee's operations interaction
((SELECT user_id FROM users WHERE email = 'kevin.lee@company.com'),
 'User: I need to automate our inventory reporting process. Where do I start?
AI Tutor: Let''s build an automation strategy for your inventory reporting! Here''s a step-by-step approach:

**1. Current Process Analysis**
First, let''s map what you''re automating:
- What data sources do you use? (ERP, spreadsheets, databases?)
- What calculations/transformations are needed?
- Who receives these reports and how often?
- What format do stakeholders prefer?

**2. AI-Powered Automation Opportunities**

**Data Extraction & Cleaning**
Prompt template:
```
Extract inventory data from this report:
- Product SKUs and quantities
- Location/warehouse information  
- Reorder points and current stock levels
- Flag any anomalies or missing data
Format as structured JSON
```

**Analysis & Insights Generation**
```
Analyze this inventory data and provide:
1. Stock-out risks (items below reorder point)
2. Overstock situations (excess inventory)
3. Slow-moving items (low turnover)
4. Trend analysis vs last period
5. Recommended actions
```

**3. Report Generation Framework**
Create templates for different stakeholders:
- Executive summary (high-level metrics)
- Warehouse operations (detailed stock levels)
- Purchasing team (reorder recommendations)

**4. Implementation Phases**
Phase 1: Automate data extraction (Week 1-2)
Phase 2: Add analysis layer (Week 3-4)
Phase 3: Customize outputs by role (Week 5-6)

What''s your current biggest pain point in the reporting process?',
 CURRENT_TIMESTAMP - INTERVAL '1 day 2 hours');

-- ============================================
-- ADDITIONAL HELPER DATA
-- ============================================

-- Add some variety in progress records for other users
UPDATE progress SET
    completed_modules = '["ai_concept_001", "ai_concept_002", "ai_concept_003", "ai_concept_004", "use_case_001", "use_case_003"]'::jsonb,
    quiz_scores = '{"ai_concept_001": 88, "ai_concept_002": 85, "ai_concept_003": 90, "ai_concept_004": 87}'::jsonb,
    last_login = CURRENT_TIMESTAMP - INTERVAL '4 hours'
WHERE user_id = (SELECT user_id FROM users WHERE email = 'michael.ross@company.com');

UPDATE progress SET
    completed_modules = '["ai_concept_001", "ai_concept_002", "ai_concept_005", "ai_concept_006", "use_case_002"]'::jsonb,
    quiz_scores = '{"ai_concept_001": 92, "ai_concept_002": 89, "ai_concept_005": 94, "ai_concept_006": 91}'::jsonb,
    last_login = CURRENT_TIMESTAMP - INTERVAL '8 hours'
WHERE user_id = (SELECT user_id FROM users WHERE email = 'david.kim@company.com');

UPDATE progress SET
    completed_modules = '["ai_concept_001", "ai_concept_002", "ai_concept_003", "ai_concept_004", "ai_concept_005", "ai_concept_006", "ai_concept_007", "ai_concept_008", "use_case_001", "use_case_002", "use_case_003", "use_case_004"]'::jsonb,
    quiz_scores = '{"ai_concept_001": 95, "ai_concept_002": 92, "ai_concept_003": 88, "ai_concept_004": 90, "ai_concept_005": 93, "ai_concept_006": 89}'::jsonb,
    last_login = CURRENT_TIMESTAMP - INTERVAL '12 hours'
WHERE user_id = (SELECT user_id FROM users WHERE email = 'lisa.wang@company.com');

UPDATE progress SET
    completed_modules = '["ai_concept_001", "ai_concept_002", "ai_concept_003", "ai_concept_004", "ai_concept_005", "ai_concept_006", "ai_concept_007", "ai_concept_008", "ai_concept_009", "ai_concept_010", "ai_concept_011", "ai_concept_012", "ai_concept_013", "ai_concept_014", "ai_concept_015"]'::jsonb,
    quiz_scores = '{"ai_concept_001": 87, "ai_concept_002": 89, "ai_concept_003": 85, "ai_concept_004": 88, "ai_concept_005": 90}'::jsonb,
    last_login = CURRENT_TIMESTAMP - INTERVAL '16 hours'
WHERE user_id = (SELECT user_id FROM users WHERE email = 'james.martinez@company.com');

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check data insertion
-- SELECT COUNT(*) as user_count FROM users;
-- SELECT COUNT(*) as progress_count FROM progress;
-- SELECT COUNT(*) as interaction_count FROM interactions;

-- View sample data
-- SELECT u.email, u.role, p.last_login, 
--        jsonb_array_length(p.completed_modules) as modules_completed,
--        jsonb_object_keys(p.quiz_scores) as quiz_modules
-- FROM users u
-- JOIN progress p ON u.user_id = p.user_id
-- LIMIT 5;

-- Check interactions
-- SELECT u.email, COUNT(i.interaction_id) as interaction_count,
--        MAX(i.timestamp) as last_interaction
-- FROM users u
-- LEFT JOIN interactions i ON u.user_id = i.user_id
-- GROUP BY u.email
-- ORDER BY interaction_count DESC;
