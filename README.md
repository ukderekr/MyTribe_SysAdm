MyTribe README

Overview

This project is a Django-based backend REST API integrated with a modern frontend (React/Quasar depending on context) to power a community platform. The backend exposes API endpoints for Posts, Events, Businesses, and ContentItems, and supports full CRUD functionality via Django REST Framework.

The project includes:
	•	Modular Django apps with models, serializers, views, URLs, and admin integrations.
	•	Fully RESTful API endpoints used by the JoinPage.tsx and other frontend components.
	•	Structured API helper utilities for GET/POST from the frontend.
	•	Media and image handling configured to serve image URLs stored in the database.

⸻

Technologies Used

Backend (Django / DRF)
	•	Django 4.x+
	•	Django REST Framework
	•	Python 3.x
	•	Modular models organized in separate files
	•	DRF serialisers for Posts, Events, Businesses, ContentItems
	•	DRF views & viewsets
	•	URL routing per-resource under /api/v1/
	•	Admin panel integration for all models

Frontend (React / TypeScript / Custom API Wrapper)
	•	React (TSX)
	•	TypeScript
	•	Custom Fetch wrapper for GET and POST requests
	•	Components such as JoinPage.tsx, NewsSection.tsx, etc.

⸻

Backend Structure

mytribe/
├── models.py (split models referenced)
├── serializers.py
├── views.py
├── urls.py
├── admin.py
└── ... other Django configs

API Endpoints (/api/v1/...)
	•	/posts/ — List & retrieve blog/news posts
	•	/events/ — List event information
	•	/businesses/ — Business directory
	•	/content/ — Custom content blocks

All endpoints return paginated responses in the format:

{
  "count": 0,
  "next": null,
  "previous": null,
  "results": [ ... ]
}


⸻

Frontend Integration

Base API URL

http://localhost:8000/api/v1

API Helpers

The frontend uses a reusable GET and POST helper:

async function get<T>(endpoint: string): Promise<T>;
async function post<T>(endpoint: string, body: any): Promise<T>;

Used inside components such as:
	•	JoinPage.tsx — Submits join form data to Django
	•	NewsSection.tsx — Retrieves news stories & associated images
	•	EventsSection.tsx — Fetches latest event info

⸻

Media & Images

Images stored as URLs in Django models can be consumed directly by the frontend. Ensure:
	•	MEDIA_URL and MEDIA_ROOT are configured
	•	Django is serving media during development:

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


⸻

Running the Project

Backend

cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py runserver

Available at:

http://localhost:8000/

Frontend

npm install
npm run dev

Runs at:

http://localhost:3000/

(or Quasar default port if using SPA)

⸻

Deployment Notes
	•	Use Gunicorn + Nginx for Django in production
	•	Serve media via Nginx static config
	•	Ensure CORS is enabled for frontend origin
	•	Environment variables for API base URL should be set per environment

⸻

Future Enhancements
	•	Authentication (Firebase or Django)
	•	Dashboard pages for Business & Events
	•	Admin tools for content management
	•	Improved caching & performance tuning

⸻

License

This project is licensed under the MIT License.

⸻

Maintainer

Vibe-coded by Derek Richards & AI-assisted tooling.