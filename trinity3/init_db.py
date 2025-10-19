"""Initialize Trinity 3.0 Database"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.prediction_service import PredictionService

if __name__ == "__main__":
    print("Initializing Trinity 3.0 database...")
    
    try:
        # Create prediction service - this will initialize all tables
        prediction_service = PredictionService()
        print("✅ Database initialized successfully!")
        print("   - predictions table created")
        print("   - backtests table created")
        print("   - simulations table created")
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        sys.exit(1)