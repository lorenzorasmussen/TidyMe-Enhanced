## How to Run the Python Server

This document provides instructions on how to set up and run the small Python server with an SQLite database.

### Prerequisites

*   Python 3.x installed on your system.
*   `pip` (Python package installer) installed.

### Installation

1.  **Install Flask:**
    If you don't have Flask installed, open your terminal and run:
    ```bash
    pip install Flask
    ```

### Running the Server

1.  **Navigate to the project directory:**
    Open your terminal and change your current directory to where `app.py` is located:
    ```bash
    cd /Users/lorenzorasmussen/Projects/TidyMe
    ```

2.  **Run the Flask application:**
    Execute the `app.py` script using Python:
    ```bash
    python app.py
    ```

    You should see output similar to this, indicating the server is running:
    ```
     * Serving Flask app 'app'
     * Debug mode: on
     WARNING: This is a development server. Do not use it in a production deployment.
     Use a production WSGI server instead.
     * Running on http://127.0.0.1:5000
    Press CTRL+C to quit
    ```

### Database File

*   An SQLite database file named `database.db` will be automatically created in the same directory as `app.py` when the server is run for the first time.

### API Endpoints

Once the server is running, you can interact with it using a tool like `curl`, Postman, or by writing a simple client. The server exposes the following RESTful API endpoints for managing `items`:

*   **GET /items**
    *   Retrieves all items.
    *   Example: `curl http://127.0.0.1:5000/items`

*   **GET /items/<id>**
    *   Retrieves a single item by its ID.
    *   Example: `curl http://127.0.0.1:5000/items/1`

*   **POST /items**
    *   Creates a new item.
    *   Requires a JSON body with `name` (required) and `description` (optional).
    *   Example: `curl -X POST -H "Content-Type: application/json" -d '{"name": "New Item", "description": "This is a new item."}' http://127.0.0.1:5000/items`

*   **PUT /items/<id>**
    *   Updates an existing item by its ID.
    *   Requires a JSON body with `name` and `description`.
    *   Example: `curl -X PUT -H "Content-Type: application/json" -d '{"name": "Updated Item", "description": "This item has been updated."}' http://127.0.0.1:5000/items/1`

*   **DELETE /items/<id>**
    *   Deletes an item by its ID.
    *   Example: `curl -X DELETE http://127.0.0.1:5000/items/1`
