Below is a sample **Project Requirements Document** that captures the major pieces of functionality and the data model you described, using **Python/Flask** with **SQLAlchemy** (and Supabase as the underlying database).

---

## 1. Project Overview

The purpose of this web application is to provide college‐access support by allowing users to:
1. View resources (such as scholarships, fly‐ins, and precollege programs).
2. Mark resources of interest (“star” them) and track their progress toward applying to those resources.
3. Read and post informational blog entries (for those with the Blogger role).
4. Manage “tasks” and “to‐dos” that guide them through each resource’s application requirements.

---

## 2. Technology Stack

1. **Backend**: Python (3.x) + Flask
2. **Database**: Supabase (PostgreSQL under the hood), accessed via SQLAlchemy models.
3. **ORM**: SQLAlchemy (with a migration tool such as Alembic recommended)
4. **Front End**: Could be Flask templates (Jinja2), or a separate frontend that interacts via REST API endpoints in Flask.
5. **Deployment**: Supabase for hosting the DB, and any hosting platform (AWS, Heroku, etc.) for the Flask application (details can vary).

---

## 3. User & Authentication Requirements

1. **User Accounts**  
   - Must be able to create a new user account (username/email/password) and log in.
   - Passwords should be hashed and salted (e.g. using a library like `bcrypt` or `werkzeug.security` in Flask).

2. **Roles**  
   - **User**: the standard user who can view resources, apply to them (i.e., star or designate interest), and track tasks.
   - **Blogger**: a subset of users who have permission to create, update, and delete blog posts that all other users can read.

3. **Authorization**  
   - Only users with the Blogger role can manage blog posts (create/edit/delete).
   - All users (including Bloggers) can view resources, star them, and manage tasks on their own applications.

---

## 4. Resource & Tag Requirements

1. **Resource**  
   - Each Resource represents some kind of opportunity: scholarships, fly‐ins, precollege programs, etc.
   - Data fields might include:
     - `id` (primary key)  
     - `name` (string)  
     - `description` (text)  
     - `category` or `type` (optional if you decide to store in tags only)  
     - `deadline` or other relevant dates  
   - Resources can be **bulk‐loaded** from a CSV file (e.g., an admin or script can read CSV rows and create Resource objects in the database).

2. **Tags**  
   - A Resource can have multiple Tags. For example, a Resource might have tags like “STEM,” “Women,” “Low Income,” etc.
   - Use an **association table** (`resource_tags`) to represent the **many‐to‐many** relationship:
     - `resource_tags`:
       - `id` (primary key)  
       - `resource_id` (foreign key to `Resource.id`)  
       - `tag_id` (foreign key to `Tag.id`)

3. **Tag**  
   - Data fields might include:
     - `id` (primary key)  
     - `name` (string, e.g. “STEM,” “Business,” “First‐Gen,” etc.)

---

## 5. Task & Form Requirements

1. **Task**  
   - Each Resource can have one or more **Tasks**, describing the steps needed to successfully complete or obtain that Resource.
   - Data fields:
     - `id` (primary key)  
     - `resource_id` (foreign key to `Resource.id`)  
     - `name` or `title` (string)  
     - `description` (text)  
     - `due_date` (date/datetime) if applicable
   - Examples of tasks:
     - “Submit personal statement by X date”  
     - “Gather recommendation letters”  

2. **Form** (Optional / As needed)  
   - If your Resource requires custom forms (e.g., questions that the user must fill out), you might have a **Form** model.
   - Data fields:
     - `id` (primary key)  
     - `task_id` or `resource_id` (depends on design, foreign key)  
     - `form_fields` (JSON or text representation of questions)  
   - Alternatively, you can store the actual question–answer pairs in a separate table, or just keep them in a `Todo` or `Answers` table.  

---

## 6. Application & Todo Requirements

### 6.1 Application

1. **Application** is an **association object** between `User` and `Resource`.
   - When a user “stars” or otherwise designates interest in a Resource, an **Application** object is created.
2. Schema example:
   ```sql
   Application:
   - id (primary key)
   - user_id (foreign key to User.id)
   - resource_id (foreign key to Resource.id)
   - status (string or enum: e.g. "in_progress", "submitted", "accepted", "rejected")
   - created_at, updated_at (timestamps)
   ```
3. **Behavior**:
   - A single user may create multiple Applications if they are interested in multiple Resources.
   - The user can track the progress/status of each Application individually.

### 6.2 Todo

1. **Todo** items are child objects of **Application** that represent the user’s personal tasks for that Resource.
   - Each Resource’s Task objects will “spawn” corresponding Todos for the user once they create an Application.
2. Schema example:
   ```sql
   Todo:
   - id (primary key)
   - application_id (foreign key to Application.id)
   - task_id (foreign key to Task.id)
   - status (string or boolean: e.g. "not_started", "in_progress", "completed")
   - user_notes (text)  # optional field
   - due_date (may inherit from the Task, or be copied)
   ```
3. **Behavior**:
   - When a user creates a new Application for a Resource, automatically generate corresponding Todos for each Task that Resource defines.
   - The user can mark each Todo as completed, add personal notes, etc.

---

## 7. Blogging Requirements

1. **Blog** (Posts)
   - A `BlogPost` model or similar, with fields like:
     - `id` (primary key)  
     - `title` (string)  
     - `content` (text)  
     - `created_at` (datetime)  
     - `author_id` (foreign key to `User.id`)
2. **Behavior**:
   - Only users with the Blogger role can create, edit, or delete `BlogPost` objects.
   - All users can read blog posts.

---

## 8. Data Model (SQLAlchemy Sketch)

Here is a rough outline for the SQLAlchemy models. (In practice, you will have each model in its own file or the same file with separate classes.)

```python
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
)
from sqlalchemy.orm import relationship
from datetime import datetime
from your_database_setup import Base  # or declarative_base()

# Many-to-many for Resource <-> Tag
resource_tags = Table(
    'resource_tags', Base.metadata,
    Column('id', Integer, primary_key=True),  # If desired, or omit & use composite PK
    Column('resource_id', Integer, ForeignKey('resources.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")  # "user" or "blogger"

    # Relationship to Application
    applications = relationship("Application", back_populates="user")

class Resource(Base):
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    # other fields as necessary

    # Many to many with Tag
    tags = relationship(
        "Tag",
        secondary=resource_tags,
        back_populates="resources"
    )

    # One to many with Task
    tasks = relationship("Task", back_populates="resource")

    # Relationship to Application
    applications = relationship("Application", back_populates="resource")

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    # Link back to Resource
    resources = relationship(
        "Resource",
        secondary=resource_tags,
        back_populates="tags"
    )

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)

    # Link back to Resource
    resource = relationship("Resource", back_populates="tasks")

    # Relationship to Todo
    todos = relationship("Todo", back_populates="task")

class Application(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
    status = Column(String, default="in_progress")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Link to user
    user = relationship("User", back_populates="applications")

    # Link to resource
    resource = relationship("Resource", back_populates="applications")

    # One to many to Todo
    todos = relationship("Todo", back_populates="application")

class Todo(Base):
    __tablename__ = 'todos'
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('applications.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    status = Column(String, default="not_started")
    user_notes = Column(Text)
    due_date = Column(DateTime)

    # Link back to application
    application = relationship("Application", back_populates="todos")
    # Link to task
    task = relationship("Task", back_populates="todos")

class BlogPost(Base):
    __tablename__ = 'blog_posts'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Link to user
    author = relationship("User")
```

---

## 9. API Endpoints (Illustrative)

Below is a very high‐level outline; in a real app, you would flesh out each endpoint with authentication checks, JSON responses, error handling, etc.

1. **Auth Routes**  
   - `POST /login`  
   - `POST /logout`  
   - `POST /register`

2. **User / Blogger**  
   - `GET /blog` (list blog posts)  
   - `POST /blog` (create new post) – restricted to Blogger role  
   - `PUT /blog/<post_id>` (edit post) – restricted to author  
   - `DELETE /blog/<post_id>` – restricted to author

3. **Resources**  
   - `GET /resources` (list all resources)  
   - `GET /resources/<id>` (view a single resource, tasks, tags, etc.)  
   - (Admin routes for bulk‐upload from CSV can be hidden behind admin privileges if necessary)

4. **Applications**  
   - `POST /applications` (create an application by “starring” a resource)  
   - `GET /applications` (view all applications belonging to the current user)  
   - `GET /applications/<id>` (view the details of one application, including todos)  
   - `PUT /applications/<id>` (update the status, etc.)

5. **Todos**  
   - `PUT /todos/<id>` (mark as complete, add notes, etc.)

---

## 10. CSV Import Requirement

1. **CSV Format**  
   - The CSV might have columns for: `name`, `description`, `deadline`, `tags`, etc.
2. **Import Flow**  
   - An admin route or script reads each row, creates a new `Resource`, then processes the comma‐separated `tags` column to create new `Tag` objects (or link existing ones).
   - Imported resources become immediately visible in the “Resources” page.

---

## 11. Security & Validation

1. **User Authentication** must protect the routes for creating an Application, tasks, and blog posts (for Bloggers).
2. **Role Checking**: only Blogger role can manage Blog content.
3. **Data Validation**:  
   - Ensure date fields for tasks are in valid date range.  
   - Avoid duplicate resource entries on CSV import.

---

## 12. Summary & Next Steps

This requirement document outlines:
- **Entities**: User, Resource, Tag, Task, Application, Todo, BlogPost.  
- **Relationships**:  
  - **User** ↔ **Application** ↔ **Resource** (many‐to‐many via the Application association).  
  - **Resource** ↔ **Tag** (many‐to‐many).  
  - **Resource** ↔ **Task** (one‐to‐many).  
  - **Application** ↔ **Todo** (one‐to‐many) which references **Task**.  
  - **User** with role Blogger can create **BlogPosts**.
- **Core Features**: CSV loading for resources, user “starring” of resources, dynamic tasks → todos creation, and blog functionality.

**Next Steps**:
- Set up Flask routes for each resource and perform CRUD operations.
- Implement user authentication (e.g., Flask-Login or custom JWT solution).
- Write the migration scripts (Alembic).
- Implement a front-end user experience that displays resources, tasks, and allows marking them complete.

By following this outline, you have a clear blueprint for the data model, RESTful routes, and functionality needed to build out your **college access web application** with Python, Flask, and Supabase.