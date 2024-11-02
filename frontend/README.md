# LinkedinEnhancer
This is frontend of Linkedin Enhancer App

# Requirements:
- Python 3.10.9 or above (3.12.4 recommended)
- Django


# Follow steps to run
1. Create a new .env file in root of frontend project.
2. Add the details of env (structure provided below)
3. open terminal in root of frontend project
4. run `pip install -r requirements.txt`
5. run `python manage.py runserver`
6. Go to `127.0.0.1:8000`


# env structure
- DJANGO_SECRET = "Random key for JWT"
- OPENAI_API_KEY="ChatGPT API Comes Here"
- DATABASE_URL="SQL Databse URL/ Connection String"
- SCRAPER_API_URL="The Backend API Url Comes Here"
- MAINTENANCE_MODE=false

