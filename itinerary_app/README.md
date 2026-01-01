# Tour Itinerary Generator App

This application is a local Flask-based tool that wraps the Tour Generator HTML to provide Save/Load functionality.

## Prerequisites

- Python 3.x
- pip

## Installation

1.  Navigate to the `itinerary_app` directory:
    ```bash
    cd "Happy Holidayz website/happyholidayz/itinerary_app"
    ```
2.  Install Flask:
    ```bash
    pip install flask
    ```

## Running the App

1.  Run the application:
    ```bash
    python app.py
    ```
2.  Open your browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Features

- **Tour Generator**: All the original functionality of the Tour Generator is preserved.
- **Save Project**: Enter a project name and click "Save Project" to save your current form data to a JSON file in the `saved_itineraries` folder.
- **Load Project**: Select a saved project from the dropdown and click "Load Project" to restore all form fields.

## File Structure

- `app.py`: Main Flask application.
- `saved_itineraries/`: Directory where saved JSON files are stored.
- **Remote Template**: The app fetches the `tour-generator-yellow-finalv2.html` template directly from the `happyholidayz` GitHub repository.
