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
            AND table_name IN ('users', 'progress', 'interactions')
            ORDER BY table_name
        """)
        
        print(f"\n✓ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # Check indexes
        indexes = await conn.fetch("""
            SELECT COUNT(*) as count
            FROM pg_indexes 
            WHERE schemaname = 'public'
        """)
        print(f"\n✓ Found {indexes[0]['count']} indexes")
        
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
        progress_count = await conn.fetchval("SELECT COUNT(*) FROM progress")
        interaction_count = await conn.fetchval("SELECT COUNT(*) FROM interactions")
        
        print(f"\n✓ Sample data:")
        print(f"  - Users: {user_count}")
        print(f"  - Progress records: {progress_count}")
        print(f"  - Interactions: {interaction_count}")
        
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


async def main():
    """Main setup function"""
    await verify_database()
    
    print("\nNext steps:")
    print("1. Review Vector_DB setup: cd ../Vector_DB")
    print("2. Initialize Weaviate: python scripts/setup_weaviate.py")
    print("3. Load sample data: python scripts/load_data.py")


if __name__ == "__main__":
    asyncio.run(main())
