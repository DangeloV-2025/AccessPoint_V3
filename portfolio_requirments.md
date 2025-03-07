1. New Feature: Portfolios

The Portfolio feature will allow users to showcase their college applications, essays, and acceptances in a structured way. This will provide a space for users to track their progress and share their achievements with others.

2. New Pages & Functionality

2.1 Portfolio Page

Each user will have a Portfolio Page where they can:

Update Applications: Users can add or modify details about the colleges they applied to, their application status, and outcomes.

Upload and Manage Essays: Users can store and display essays they used for different applications.

Track College Acceptances: Users can list the colleges they got accepted into, along with relevant details (e.g., scholarship offers, honors programs, etc.).

2.2 Bios Page

Each user will have a Bio Card displaying:

Their name and basic information.

A list of colleges they were accepted into.

A brief personal statement (optional) about their journey through the college application process.

2.3 Portfolios Overview Page

A public or admin-accessible page where all user portfolios can be viewed.

Displays all colleges a user got accepted to and links to their essays (if shared).

Filter and search functionality to browse portfolios based on college acceptances, intended major, or other relevant criteria.

3. Technology Stack

Backend

Python (Flask) for managing user profiles and portfolio data.

SQLAlchemy + Supabase for data storage and retrieval.

Frontend

Flask Jinja2 templates OR a separate React.js frontend interacting with REST API endpoints.

Interactive UI elements for updating applications and essays.

Deployment

Supabase for the database.

AWS/Heroku/Vercel for hosting the Flask backend and frontend.

4. Data Model (SQLAlchemy)

User

id (Primary Key)

username (String, Unique)

email (String, Unique)

password_hash (String)

bio (Text, Optional)

CollegeApplication

id (Primary Key)

user_id (Foreign Key to User.id)

college_name (String)

status (Enum: "applied", "accepted", "rejected", "waitlisted")

scholarships_awarded (Text, Optional)

Essay

id (Primary Key)

user_id (Foreign Key to User.id)

title (String)

content (Text)

college_id (Foreign Key to CollegeApplication.id, Optional)

is_public (Boolean, default=False)

Portfolio

id (Primary Key)

user_id (Foreign Key to User.id)

bio_card (Text, Optional)

colleges_accepted (Array of CollegeApplication references)

5. API Endpoints

Authentication

POST /register (Register new user)

POST /login (User login)

POST /logout (User logout)

Portfolios

GET /portfolios (View all portfolios)

GET /portfolio/<user_id> (View a specific user’s portfolio)

POST /portfolio (Create or update portfolio details)

College Applications

GET /applications (List all applications for the logged-in user)

POST /applications (Add a new college application)

PUT /applications/<id> (Update application status)

Essays

GET /essays (List essays for the logged-in user)

POST /essays (Upload a new essay)

PUT /essays/<id> (Edit essay)

DELETE /essays/<id> (Delete an essay)

6. Security & Validation

Authentication: Users must be logged in to modify portfolios, applications, and essays.

Privacy Controls: Users can choose whether to make their essays and portfolios publicly visible.

Data Validation: Ensure unique college names in applications, enforce character limits for bio and essay content.

7. Summary & Next Steps

This feature introduces a new Portfolio System that enables users to track and showcase their college applications, acceptances, and essays. The core components include:

A Portfolio Page for each user.

A Bios Page summarizing user achievements.

A Public Portfolio Overview to explore multiple user profiles.

Next Steps:

Implement database models in Flask with SQLAlchemy.

Build API endpoints for managing applications, essays, and portfolios.

Develop frontend pages for user interaction.

Implement authentication & privacy settings to control access to portfolios and essays.

