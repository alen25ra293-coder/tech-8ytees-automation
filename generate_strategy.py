import sys
import io
from dotenv import load_dotenv

load_dotenv()

from src.generators.strategy_pipeline import run_full_strategy_pipeline

def main():
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        elif hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        
    print("Starting Automated YouTube Strategy Generation...")
    
    channel_info = (
        "Tech 8ytees channel. Fast-paced vertical shorts (23-26 seconds). "
        "Focus on budget gadgets vs expensive premium alternatives."
    )
    
    report_path = run_full_strategy_pipeline(channel_context=channel_info)
    
    print(f"\nDone! Please review your new strategy report at: {report_path}")

if __name__ == "__main__":
    main()
