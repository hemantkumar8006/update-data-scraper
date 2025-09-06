import os
import sys

def check_requirements():
    """Check if all requirements are met"""
    print("Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please copy env.example to .env and configure your API keys")
        return False
    
    print("✅ .env file found")
    
    # Check if required directories exist
    required_dirs = ['config', 'scrapers', 'ai_processors', 'data', 'mcp_server', 'utils', 'logs']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"❌ Directory {dir_name} not found")
            return False
    
    print("✅ All required directories exist")
    
    # Check if database exists, if not create it
    if not os.path.exists('data/exam_updates.db'):
        print("Creating database...")
        try:
            from data.storage import DataStorage
            DataStorage().init_database()
            print("✅ Database created successfully")
        except Exception as e:
            print(f"❌ Failed to create database: {e}")
            return False
    else:
        print("✅ Database exists")
    
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Exam Update Scraping System")
    print("=" * 50)
    
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        sys.exit(1)
    
    print("\n✅ All requirements met!")
    print("\nStarting the system...")
    
    # Import and run the main application
    try:
        from main import main as main_app
        main_app()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error starting the system: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
