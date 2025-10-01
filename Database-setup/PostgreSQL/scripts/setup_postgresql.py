"""
PostgreSQL Database Setup Script
Connects to PostgreSQL and verifies schema
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "ai_tutor_db"),
    "user": os.getenv("POSTGRES_USER", "ai_tutor_admin"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


async def verify_database():
    """Verify database connection and schema"""
    print("=" * 60)
    print("PostgreSQL Database Verification")
    print("=" * 60)
    print("\nConnecting to PostgreSQL...")
    
    try:
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        print("✓ Successfully connected to PostgreSQL")
        
        # Check tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'progress')
            ORDER BY table_name
        """)
        
        print(f"\n✓ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # Check user table columns
        user_columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        
        print(f"\n✓ Users table has {len(user_columns)} columns:")
        for col in user_columns:
            print(f"  - {col['column_name']}: {col['data_type']}")
        
        # Verify summary columns exist
        summary_cols = [c for c in user_columns if 'summary' in c['column_name']]
        if len(summary_cols) == 2:
            print("\n✓ Summary columns found:")
            for col in summary_cols:
                print(f"  - {col['column_name']}")
        else:
            print("\n⚠ Warning: Summary columns not found. Run add_summary_columns.sql migration.")
        
        # Check indexes
        indexes = await conn.fetch("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        print(f"\n✓ Found {len(indexes)} indexes")
        
        # Check functions
        functions = await conn.fetch("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_schema = 'public'
            AND routine_type = 'FUNCTION'
            ORDER BY routine_name
        """)
        
        print(f"\n✓ Found {len(functions)} helper functions:")
        for func in functions:
            print(f"  - {func['routine_name']}")
        
        # Check sample data
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"\n✓ Found {user_count} sample users")
        
        # Show user summary
        if user_count > 0:
            users = await conn.fetch("""
                SELECT email, role, proficiency, 
                       CASE WHEN short_term_summary IS NOT NULL THEN 'Yes' ELSE 'No' END as has_short_summary,
                       CASE WHEN long_term_summary IS NOT NULL THEN 'Yes' ELSE 'No' END as has_long_summary
                FROM users
                ORDER BY created_at
            """)
            
            print("\nUser Summary:")
            for user in users:
                print(f"  - {user['email']}")
                print(f"    Role: {user['role']} | Proficiency: {user['proficiency']}")
                print(f"    Short-term summary: {user['has_short_summary']} | Long-term summary: {user['has_long_summary']}")
        
        # Check progress data
        progress_count = await conn.fetchval("""
            SELECT COUNT(*) FROM progress WHERE jsonb_array_length(completed_modules) > 0
        """)
        print(f"\n✓ Found {progress_count} users with completed modules")
        
        # Show detailed progress for one user
        if progress_count > 0:
            sample_progress = await conn.fetchrow("""
                SELECT 
                    u.email,
                    jsonb_array_length(p.completed_modules) as modules_completed,
                    (SELECT COUNT(*) FROM jsonb_object_keys(p.quiz_scores)) as quizzes_taken,
                    ROUND((SELECT AVG((value::text)::numeric) FROM jsonb_each(p.quiz_scores)), 2) as avg_score
                FROM users u
                JOIN progress p ON u.user_id = p.user_id
                WHERE jsonb_array_length(p.completed_modules) > 0
                LIMIT 1
            """)
            
            print(f"\nSample Progress ({sample_progress['email']}):")
            print(f"  - Completed modules: {sample_progress['modules_completed']}")
            print(f"  - Quizzes taken: {sample_progress['quizzes_taken']}")
            print(f"  - Average score: {sample_progress['avg_score']}")
        
        # Test helper functions
        print("\n✓ Testing helper functions...")
        test_results = await conn.fetch("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_schema = 'public'
            AND routine_type = 'FUNCTION'
            AND routine_name IN (
                'add_completed_module',
                'update_quiz_score',
                'log_user_interaction',
                'update_short_term_summary',
                'update_long_term_summary',
                'get_user_context'
            )
        """)
        
        if len(test_results) >= 6:
            print("  ✓ All required helper functions are available")
        else:
            print(f"  ⚠ Warning: Only {len(test_results)}/6 helper functions found")
        
        # Test get_user_context function with a sample user
        if user_count > 0:
            sample_user = await conn.fetchrow("SELECT user_id FROM users LIMIT 1")
            context = await conn.fetchrow(
                "SELECT * FROM get_user_context($1)",
                sample_user['user_id']
            )
            if context:
                print("  ✓ get_user_context() function working correctly")
        
        await conn.close()
        print("\n" + "=" * 60)
        print("Database Verification Complete!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Docker container is running: docker-compose ps")
        print("2. Check .env file has correct credentials")
        print("3. Verify database initialized: docker-compose logs postgres")
        return False


async def test_queries():
    """Run test queries to verify functionality"""
    print("\n" + "=" * 60)
    print("Running Test Queries")
    print("=" * 60)
    
    try:
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        
        # Test 1: Query user profile summary view
        print("\n1. Testing user_profile_summary view...")
        profiles = await conn.fetch("SELECT * FROM user_profile_summary LIMIT 3")
        print(f"   ✓ Retrieved {len(profiles)} user profiles")
        
        # Test 2: Search by learning goal
        print("\n2. Testing JSONB query (learning_goals)...")
        users_with_goal = await conn.fetch("""
            SELECT email, learning_goals 
            FROM users 
            WHERE learning_goals @> '["prompt_engineering"]'::jsonb
        """)
        print(f"   ✓ Found {len(users_with_goal)} users with 'prompt_engineering' goal")
        
        # Test 3: Full-text search on summaries
        print("\n3. Testing full-text search on summaries...")
        search_results = await conn.fetch("""
            SELECT email, short_term_summary 
            FROM users 
            WHERE to_tsvector('english', COALESCE(short_term_summary, '')) 
                  @@ plainto_tsquery('english', 'prompt')
        """)
        print(f"   ✓ Found {len(search_results)} users with 'prompt' in summaries")
        
        # Test 4: Quiz performance aggregation
        print("\n4. Testing quiz score aggregation...")
        role_stats = await conn.fetch("""
            SELECT 
                u.role,
                COUNT(*) as user_count,
                ROUND(AVG((SELECT AVG((value::text)::numeric) FROM jsonb_each(p.quiz_scores))), 2) as avg_score
            FROM users u
            JOIN progress p ON u.user_id = p.user_id
            WHERE jsonb_typeof(p.quiz_scores) = 'object'
            GROUP BY u.role
        """)
        print(f"   ✓ Aggregated quiz scores by role:")
        for stat in role_stats:
            print(f"     - {stat['role']}: {stat['user_count']} users, avg score {stat['avg_score']}")
        
        await conn.close()
        print("\n✓ All test queries completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test query error: {e}")
        return False


async def main():
    """Main setup function"""
    success = await verify_database()
    
    if success:
        response = input("\nRun test queries? (y/n): ")
        if response.lower() == 'y':
            await test_queries()
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review Vector_DB setup: cd ../Vector_DB")
    print("2. Initialize Weaviate: python scripts/setup_weaviate.py")
    print("3. Load sample data: python scripts/load_data.py")


if __name__ == "__main__":
    asyncio.run(main())
