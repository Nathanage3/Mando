- **[E-commerce](https://github.com/Nathanage3/E-commerce.git)**: <br /> -**ProLearn: A Full-Stack Course E-Commerce Platform**
A feature-rich, full-stack e-commerce platform for selling and managing online courses, built with a decoupled architecture. The backend is a robust RESTful API powered by Django & Django REST Framework, and the frontend is a dynamic, responsive client built with React.

This repository contains the backend (API) portion of the project.

Link to Frontend Repository: https://github.com/Nathanage3/E-commerce.git  (frontend branch)

Live Demo: https://mandotest.netlify.app/

- **Note to Employers & Recruiters**

As the primary backend developer on this collaborative project, my responsibilities included:

    Designing the complete database schema and models.

    Developing the entire RESTful API, including all business logic.

    Implementing secure, token-based user authentication (JWT).

    Writing logic for course management, filtering, user enrollments, and payment processing.

    Managing the project using a feature-branch Git workflow for seamless collaboration.

🚀 **Core Features**

User Authentication: Secure user registration and login using JSON Web Tokens (JWT).

Course Catalog: Browse, search, and filter courses by category, price, and rating.

Course Management (Instructor): Full CRUD (Create, Read, Update, Delete) functionality for courses, modules, and lessons.

Shopping Cart: Persistent shopping cart for authenticated users.

Secure Checkout: Integration with a payment processor (e.g., Stripe) to handle transactions.

User Dashboard: "My Courses" section for users to access their enrolled content.

- **🛠️ Technical Stack**

**Backend (This Repository)**

  Framework: Django

  API: Django REST Framework (DRF)

  Authentication: DRF Simple JWT (Token-Based Authentication)

  Database: PostgreSQL (production-ready, configured for local development with SQLite)

  CORS: django-cors-headers for managing cross-origin requests from the React frontend.

**Frontend (Client)**

  Library: React.js

  Routing: React Router

  API Client: Axios (for making requests to the Django API)

  State Management: Redux / Context API

  Styling: Styled-Components / Tailwind CSS / CSS Modules

- **🔐 API Architecture & Endpoints**

The backend is built around a clean, well-structured set of RESTful API endpoints.

Endpoint&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Method(s)&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Description

/api/auth/register/&emsp;&emsp;&emsp;&emsp;POST&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Handles new user registration.  <br />                         
/api/auth/token/&emsp;&emsp;&emsp;&emsp;POST&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emspObtains JWT access and refresh tokens for login.  <br />   
/api/auth/token/refresh/&emsp;&emsp;POST&emsp;&emsp;&emsp;&emsp;Refreshes an expired access token.  <br />   
/api/courses/&emsp;&emsp;&emsp;&emsp;&emsp;GET&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Get a list of all courses with filtering and search.  <br />   
/api/courses/<id>/&emsp;&emsp;&emsp;&emsp;GET&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Get detailed information for a single course.  <br />    
/api/courses/instructor/&emsp;&emsp;&emsp;GET, POST&emsp;&emsp;&emsp;List or create courses for the authenticated instructor.  <br />   
/api/courses/instructor/<id>/&emsp;&emsp;GET, PUT, DELETE&emsp;&emsp;Get, update, or delete a specific course owned by the instructor.  <br />   
/api/courses/<id>/reviews/&emsp;&emsp;GET, POST&emsp;&emsp;&emsp;&emsp;Get all reviews for a course or post a new review.  <br />   
/api/cart/&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;GET, POST&emsp;&emsp;&emsp;&emsp;Get the user's cart or add an item to it.  <br />   
/api/cart/remove/&emsp;&emsp;&emsp;&emsp;POST&emsp;&emsp;&emsp;&emsp;&emsp;Remove an item from the user's cart.  <br />   
/api/checkout/&emsp;&emsp;&emsp;&emsp;&emsp;POST&emsp;&emsp;&emsp;&emsp;Processes the user's cart and initiates the payment flow.  <br />   
/api/users/me/&emsp;&emsp;&emsp;&emsp;&emsp;GET, PUT&emsp;&emsp;&emsp;Get or update the authenticated user's profile.  <br />   
/api/users/me/courses/&emsp;&emsp;&emsp;&emsp;GET&emsp;&emsp;&emsp;Get a list of all courses the user is enrolled in.  <br />   

Ratings & Reviews: Authenticated users can leave reviews and ratings on courses they are enrolled in.

- **📦 Local Installation & Setup**

To run the backend server locally, follow these steps:

1. Clone the repository:

git clone [https://github.com/](https://github.com/)[Nathanage3/E-commerce.git
cd E-commerce


2. Create and activate a virtual environment:

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate


3. Install dependencies:

pip install -r requirements.txt


4. Set up environment variables:

Create a .env file in the root directory by copying the example file.

cp .env.example .env


Open the .env file and fill in the required variables (like SECRET_KEY). You can generate a new Django secret key here.

5. Run database migrations:

python manage.py migrate


6. Run the development server:

python manage.py runserver


The backend API will now be running at http://127.0.0.1:8000.

7. Set up the Frontend:

Clone the frontend repository and follow its README.md file for installation.

Ensure the frontend's API (Axios) base URL is pointed at http://127.0.0.1:8000.

**🤝 Collaboration**

This project was a collaborative effort, developed using a feature-branch Git workflow. This decoupled approach allowed for parallel development on the backend API and the frontend client, with clear API contracts ensuring smooth integration.

 👤 Author
Sisay Alemayehu

Upwork Profile: https://www.upwork.com/freelancers/~015945afc425acd0da

LinkedIn: https://www.linkedin.com/in/nathan-hailu/

GitHub: https://github.com/Nathanage3

<br />
