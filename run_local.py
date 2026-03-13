import os
import sys

# Add the current directory to sys.path so we can import from the api folder
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from index import app

if __name__ == '__main__':
    print("Starting LeucoScan AI on localhost...")
    app.run(debug=True, port=5000)
