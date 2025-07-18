# Luciana – Property Meeting Platform

Luciana is a prototype meeting platform created for a user interface practical course. It helps property owners and housing associations organise meetings, share agendas and keep track of attendees in one place. Planned meetings can be synchronised with Google Calendar so everyone stays informed.

## Getting Started

1. Create and activate a Python virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   # On Windows
   # venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Run the development server:

   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5000/`.

## Deployment

To deploy the prototype on Google App Engine:

```bash
gcloud config set project <your-project-id>
gcloud app deploy
```

This repository is provided for educational purposes as part of a practical course on user interface design.
