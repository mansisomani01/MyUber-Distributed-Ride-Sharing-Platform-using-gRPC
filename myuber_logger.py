import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("myuber.log"),  # Log to file
                        logging.StreamHandler()  # Log to console
                    ])

# Create a logger instance for MyUber
logger = logging.getLogger("MyUber")
