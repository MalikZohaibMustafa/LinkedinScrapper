from pathlib import Path
from django.shortcuts import render
from django.shortcuts import redirect
import markdown
import requests
from gpt_llm.llm_bot import LLM_Bot
from django.contrib import messages
from django.http import JsonResponse
from django.http import request
import json
import logging
logger = logging.getLogger(__name__)
import os
import environ


env = environ.Env()
environ.Env.read_env() 

llm_bot = LLM_Bot()

def index(request):
    
    return render(request, 'index.html')

# SCRAPER_API_URL = env('SCRAPER_API_URL')
SCRAPER_API_URL = os.getenv('SCRAPER_API_URL', 'default_value')

print("SCRAPER_API_URL", SCRAPER_API_URL)

headers = {
    'ngrok-skip-browser-warning': 'true'
}


from django.http import JsonResponse

def scrape(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        if not url.startswith('https'):
            return JsonResponse({'status': 'error', 'message': 'Please enter a valid URL starting with https://'})

        try:
            headers = {
                'ngrok-skip-browser-warning': 'true'
            }

            SCRAPER_API_URL = env('SCRAPER_API_URL')
            SCRAPER_API_URL = os.getenv('SCRAPER_API_URL', 'default_value')

            print("URL: ", SCRAPER_API_URL)

            response = requests.post(f"{SCRAPER_API_URL}/scrape", headers=headers, json={'url': url})
            if response.status_code == 302:
                print("Redirect detected, location:", response.headers.get('Location'))
            print("URL_Response: ", response.json())

            response_data = response.json()
            print("URL_Response: ", response_data)

            if response_data['status'] == 'success':
                data = response_data['data']
                
                # Store scraped data in session
                request.session['scraped_data'] = data

                # Return JSON response for AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success'})

                # For normal form submissions, render the recommendation page
                return render(request, 'recommendation.html', data)
            else:
                return JsonResponse({'status': 'error', 'message': response_data.get('message', 'Unknown error')})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def getQuestions(request):
    if request.method == 'POST':
        if 'data' not in request.session:
            return JsonResponse({'error': 'Session expired. Please try again.'})

        data = request.session['data']
        about = data['about']
        headline = data['headline']

        questions_about = llm_bot.getAboutQuestions(about)
        questions_headline = llm_bot.getHeadlineQuestions(headline=headline, about=about)

        return JsonResponse({
            'questions': questions_about + questions_headline
        })


def preprocess_text(text):
    # Replace **text** with <strong>text</strong>
    return markdown.markdown(text)
def getRecommendation(request):
    # Check if data is available in the session
    scraped_data = request.session.get('scraped_data')
    manual_data = request.session.get('manual_data')

    # Print the session data for debugging
    print("Scraped Data:", scraped_data)
    print("Manual Data:", manual_data)

    # If neither scraped data nor manual data is available, redirect to the index
    if not scraped_data and not manual_data:
        return redirect('index')

    # Use the scraped data, which has been updated with manual data
    data = scraped_data

    # Extract the relevant data from the session
    headline = data.get('headline', '')
    about = data.get('about', '')
    experience = data.get('experience', '')
    projects = data.get('projects', '')

    # Generate recommendations (or use as is)
    newAbout = llm_bot.getNewAbout(about, "")
    newHeadline = llm_bot.getNewHeadline(headline, "")
    newExperience = llm_bot.getNewExperience(experience)
    newProjects = llm_bot.getNewProjects(projects, experience)

    # Render the recommendations page with the data
    return render(request, 'recommendation.html', {
        'newAbout': newAbout,
        'about': about,
        'newHeadline': newHeadline,
        'headline': headline,
        'newExperience': newExperience,
        'experience': experience,
        'newProjects': newProjects,
        'projects': projects
    })

def manualUpload(request):
    if request.method == 'POST':
        # Get the manually entered data
        headline = request.POST.get('headline')
        about = request.POST.get('about')
        experience = request.POST.get('experience')
        projects = request.POST.get('projects')

        # If scraped_data exists, update it with manual data
        scraped_data = request.session.get('scraped_data', {})

        # Update the scraped data with manual data (overwriting only the provided fields)
        scraped_data.update({
            'headline': headline,
            'about': about,
            'experience': experience,
            'projects': projects,
        })

        # Store the updated scraped data back in the session
        request.session['scraped_data'] = scraped_data

        # Ensure session is marked as modified
        request.session.modified = True

        return redirect('getRecommendation')

    return render(request, 'manualUpload.html')

def regenerate(request):
    types = {
        "about": llm_bot.regenAbout,
        "headline": llm_bot.regenHeadline,
        "experience": llm_bot.regenExperience,
        "projects": llm_bot.regenProjects
    }
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        
        function = types[data['section']]
        res = function(data['text'])
        res = types[data['section']](data['text'])
        
        return  JsonResponse({"res":res})
