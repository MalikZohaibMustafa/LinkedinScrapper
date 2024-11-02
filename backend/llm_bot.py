import os
import time
import environ
from typing import Any
from openai import RateLimitError
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

OPENAI_API_KEY = env('OPENAI_API_KEY')

class LLM_Bot:
    def __init__(self) -> None:
        self.headlineQPrompt = ChatPromptTemplate.from_messages([

            SystemMessage(
                content=(
                " You are an AI expert in LinkedIn profile optimization, "
                "specializing in crafting impactful headlines. "
                "Your task is to analyze a user's current LinkedIn headline and professional information, "
                "then ask 5 questions to help them improve it. "
                "Place all the questions together enclosed in triple backticks ```Questions``` Like this. "
                )
                ),
            HumanMessagePromptTemplate.from_template("Headline: {headline} \n About: {about}"),
        ]
        )
        self.newHeadlinePrompt = ChatPromptTemplate.from_messages([

            SystemMessage(
                
                content=
                (" You are an AI expert in LinkedIn profile optimization, "
                "specializing in crafting impactful headlines. "
                "Your task is to analyze a user's current LinkedIn headline and review the answers the user gave "
                "to create an optimized version of the headline. Return only the optimized headline. "
                "Ensure that the headline is clear, concise, has a professional tone, uses relevant keywords, offers Unique value proposition. "
                "The headline should have the following features:\n"
                "1. Should be 220 characters or less. \n"
                "2. Incorporates relevant industry keywords.\n"
                "3. Highlights the user's unique skills or expertise.\n"
                "4. Aligns with their career goals.\n"
                "5. Clearly states the user's professional identity.\n"
                "6. Incorporates relevant industry keywords.\n"
                "7. Uses action-oriented language where appropriate.\n"
                "8. Avoids clichés and overly general terms.\n"
                "Return only the optimized headline."

            )
            ),
            HumanMessagePromptTemplate.from_template("Headline: {headline} \n Questions and answers: {qa}"),
        ]

        )
        self.regenHeadlinePrompt =ChatPromptTemplate.from_messages([

            SystemMessage(
                
                content=
                (" You are an AI expert in LinkedIn profile optimization, "
                "specializing in crafting impactful headlines. "
                "The user did not like the previously generated headline. Regenerate it for them. "
                "Ensure that the headline is clear, concise, has a professional tone, uses relevant keywords, offers Unique value proposition. "
                "The headline should have the following features:\n"
                "1. Should be 220 characters or less. \n"
                "2. Incorporates relevant industry keywords.\n"
                "3. Highlights the user's unique skills or expertise.\n"
                "4. Aligns with their career goals.\n"
                "5. Clearly states the user's professional identity.\n"
                "6. Incorporates relevant industry keywords.\n"
                "7. Uses action-oriented language where appropriate.\n"
                "8. Avoids clichés and overly general terms.\n"
                "Return only the optimized headline."

            )
            ),
            HumanMessagePromptTemplate.from_template("Headline: {headline} "),
        ]

        )



        self.aboutQPrompt = ChatPromptTemplate.from_messages([

            SystemMessage(
                content=(" You are an AI expert in LinkedIn profile optimization, "
                "specializing in crafting compelling 'About' sections. "
                "Your task is to analyze a user's current LinkedIn 'About', "
                "then ask 5 questions to help them improve it. "
                "Place all the questions together enclosed in triple backticks ```Questions``` Like this. "
                
            )),
            HumanMessagePromptTemplate.from_template("About: {about}")
        ]

        )
        self.newAboutPrompt = ChatPromptTemplate.from_messages(
         [
             
         SystemMessage(
                content=(" You are an AI expert in LinkedIn profile optimization, "
                "specializing in crafting compelling 'About' sections. "
                "Your task is to analyze a user's current LinkedIn 'About', and review the answers the user gave "
                "to create an optimized version of the 'About' Sections.  "
                "The optimized 'About' Section should have the following features:\n"
                "1. Is between 2000-2600 characters (LinkedIn's limit) \n"
                "2. Starts with a strong, attention-grabbing opening statement\n"
                "3. Clearly communicates the user's professional identity and value proposition.\n"
                "4. Incorporates relevant industry keywords naturally.\n"
                "5. Highlights key achievements and skills with specific examples.\n"
                "6. Includes a brief career narrative that showcases progression and expertise.\n"
                "7. Ends with a clear call-to-action or statement of career aspirations.\n"
                "8. Uses a mix of short paragraphs and bullet points for readability.\n"
                "9. Maintains a professional yet personable tone.\n"
                "Return only the optimized 'About' Sections."
            )),
            HumanMessagePromptTemplate.from_template("About: {about} \n Questions and answers: {qa}"),

         ]   
        )
        self.regenAboutPrompt = ChatPromptTemplate.from_messages(
         [
             
         SystemMessage(
                content=(" You are an AI expert in LinkedIn profile optimization, "
                "specializing in crafting compelling 'About' sections. "
                "The user did not like the previous about section. Regenerate it for them. "
                "The optimized 'About' Section should have the following features:\n"
                "1. Is between 2000-2600 characters (LinkedIn's limit) \n"
                "2. Starts with a strong, attention-grabbing opening statement\n"
                "3. Clearly communicates the user's professional identity and value proposition.\n"
                "4. Incorporates relevant industry keywords naturally.\n"
                "5. Highlights key achievements and skills with specific examples.\n"
                "6. Includes a brief career narrative that showcases progression and expertise.\n"
                "7. Ends with a clear call-to-action or statement of career aspirations.\n"
                "8. Uses a mix of short paragraphs and bullet points for readability.\n"
                "9. Maintains a professional yet personable tone.\n"
                "Return only the optimized 'About' Sections."
            )),
            HumanMessagePromptTemplate.from_template("About: {about}"),

         ]   
        )



        self.newExperience = ChatPromptTemplate.from_messages(
         [
             
            SystemMessage(
                content=(" You are an AI expert in LinkedIn profile optimization, "
                "specializing in crafting compelling 'Experience' sections. "
                "Your task is to analyze a user's current LinkedIn 'Experience' section and "
                "to create an optimized version of the 'Experience' Sections."
                "Optimize by Refining each job title for clarity and searchability (if needed), "
                "Ensuring accurate company names and date ranges"
                "Crafting concise, impactful bullet points (3-5 per role) that:\n"
                "Start with strong action verbs\n"
                "Incorporate relevant industry keywords\n"
                "Highlight specific, quantifiable achievements (e.g., percentages, numbers, dollar amounts)\n"
                "Demonstrate skills and responsibilities relevant to target roles\n"
                "Showcase career progression and increasing responsibility\b"
                "Maintaining consistency in format and tone across all entries\n"

                "The optimized 'Experience' Section should have the following features for each entry:\n"

                "1. Job title accuracy and impact \n"
                "2. Company name and brief description\n"
                "3. Date range accuracy.\n"
                "4. Content of job descriptions.\n"
                "5. Use of action verbs and keywords.\n"
                "6. Quantifiable achievements and results.\n"
                "7. Relevance to career goals and target roles.\n"
                " Return only the optimized 'Experience' Sections. "
                

            )),
            HumanMessagePromptTemplate.from_template("Experience: {experience}"),
         ]

        )
        self.regenExperiencePrompt = ChatPromptTemplate.from_messages(
         [
             
            SystemMessage(
                content=(" You are an AI expert in LinkedIn profile optimization, "
                "specializing in crafting compelling 'Experience' sections. "
                "The user was not satisfied with the previous experience section. Regenerate it for them. "
                "Optimize by Refining each job title for clarity and searchability (if needed), "
                "Ensuring accurate company names and date ranges"
                "Crafting concise, impactful bullet points (3-5 per role) that:\n"
                "Start with strong action verbs\n"
                "Incorporate relevant industry keywords\n"
                "Highlight specific, quantifiable achievements (e.g., percentages, numbers, dollar amounts)\n"
                "Demonstrate skills and responsibilities relevant to target roles\n"
                "Showcase career progression and increasing responsibility\b"
                "Maintaining consistency in format and tone across all entries\n"

                "The optimized 'Experience' Section should have the following features for each entry:\n"

                "1. Job title accuracy and impact \n"
                "2. Company name and brief description\n"
                "3. Date range accuracy.\n"
                "4. Content of job descriptions.\n"
                "5. Use of action verbs and keywords.\n"
                "6. Quantifiable achievements and results.\n"
                "7. Relevance to career goals and target roles.\n"
                " Return only the optimized 'Experience' Sections. "
                

            )),
            HumanMessagePromptTemplate.from_template("Experience: {experience}"),
         ]

        )
        


        self.newProjects = ChatPromptTemplate.from_messages(
            [

            SystemMessage(
                content=(" You are an AI expert in LinkedIn profile optimization, "
                "specializing in crafting compelling 'Projects' sections. "
                "Your task is to analyze a user's current LinkedIn 'Projects' section and "
                "to create an optimized version of the 'Projects' Sections."
                "The 'Projects' Section should be optimzed by following these steps:\n"
                    "1. Project title clarity and impact\n"
                    "2. Project description content and length\n"
                    "3. Start and end dates (if applicable)\n"
                    "4. Team size and user's role (if mentioned)\n"
                    "5. Technologies or skills utilized\n"
                    "6. Measurable outcomes or results\n"
                    "7. Relevance to career goals and target roles\n"
                    "8. Concise comprehensive project description that "
                    "Clearly explains the project's purpose and scope, "
                    "Highlights the user's specific contributions and responsibilities, "
                    "Incorporates relevant industry keywords and technologies used. "
                    "Showcases measurable outcomes, achievements, or learnings and "
                    "Demonstrates skills relevant to the user's target roles \n "
                    "9 . Maintain a consistent format and tone across all entries\n"
                    "10. Prioritize projects that are most relevant to the user's current career goals or demonstrate key skills for their target roles.\n"
                    "11. Ensure the overall 'Projects' section:\n"
                    "Complements the 'Experience' section without unnecessary duplication, "
                    "Demonstrates a range of skills and competencies, "
                    "Aligns with the user's stated career goals and target roles and "
                    "Stays within LinkedIn's character limits for each entry\n"


                " Return only the optimized 'Projects' Sections. "
            )),
            HumanMessagePromptTemplate.from_template("projects: {projects}, experience: {experience} "),
            ]

        )
        
        self.regenNewProjectsPrompt =  ChatPromptTemplate.from_messages(
            [

            SystemMessage(
                content=(" You are an AI expert in LinkedIn profile optimization, "
                "specializing in crafting compelling 'Projects' sections. "
                "The user was not satisfied with the previous projects section. Regenerate it for them. "
                "The 'Projects' Section should be optimzed by following these steps:\n"
                    "1. Project title clarity and impact\n"
                    "2. Project description content and length\n"
                    "3. Start and end dates (if applicable)\n"
                    "4. Team size and user's role (if mentioned)\n"
                    "5. Technologies or skills utilized\n"
                    "6. Measurable outcomes or results\n"
                    "7. Relevance to career goals and target roles\n"
                    "8. Concise comprehensive project description that "
                    "Clearly explains the project's purpose and scope, "
                    "Highlights the user's specific contributions and responsibilities, "
                    "Incorporates relevant industry keywords and technologies used. "
                    "Showcases measurable outcomes, achievements, or learnings and "
                    "Demonstrates skills relevant to the user's target roles \n "
                    "9 . Maintain a consistent format and tone across all entries\n"
                    "10. Prioritize projects that are most relevant to the user's current career goals or demonstrate key skills for their target roles.\n"
                    "11. Ensure the overall 'Projects' section:\n"
                    "Complements the 'Experience' section without unnecessary duplication, "
                    "Demonstrates a range of skills and competencies, "
                    "Aligns with the user's stated career goals and target roles and "
                    "Stays within LinkedIn's character limits for each entry\n"


                " Return only the optimized 'Projects' Sections. "
            )),
            HumanMessagePromptTemplate.from_template("projects: {projects} "),
            ]

        )
        


        self.llm = ChatOpenAI(api_key=OPENAI_API_KEY)


    def getAboutQuestions(self, about: str) -> list[str] | None:
        retry_count = 0
        max_retries = 1
        print("here")
        chain =  self.aboutQPrompt | self.llm
        while retry_count < max_retries:
            try:
                res = chain.invoke({'about': about})
                print("Full response:", res)
                print(type(res))
                # Directly target the 'text' key and remove the first line with "```Questions```"
                full_text = res.content
                print("Full text received:", full_text)
                print(type(full_text))
                # Split the text into lines and remove the first one
                lines = full_text.split('\n')[1:]
                print("Lines after splitting:", lines)

                # Filter out empty lines and ensure there's meaningful content
                questions_split = [line.strip() for line in lines if len(line.strip()) > 2]
                print("Filtered questions:", questions_split)

                if len(questions_split) > 0:
                    return questions_split
                break  # If questions are found, exit loop
            except RateLimitError:
                print("Rate limit exceeded. Retrying after 60 seconds.")
                time.sleep(60)  # Sleep for 60 seconds before retrying
            except Exception as e:
                print(f"An error occurred: {e}")
                break  # Break out of the loop if there's an unexpected error
            
            retry_count += 1

        return None
    
    def getNewAbout(self, about: str, qa: str) -> str:
        chain = self.newAboutPrompt | self.llm
        try:
            res = chain.invoke({'about': about, 'qa': qa})
            return res.content
        except RateLimitError as e:
            print("Rate limit exceeded. Please try again later.")
            # Implement logic to handle the rate limit
            time.sleep(60)  # Sleep for 60 seconds before retrying
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""


    def regenAbout(self,about):

        chain = self.regenAboutPrompt | self.llm
        try:
            res = chain.invoke({'about': about})
            return res.content
        except RateLimitError as e:
            print("Rate limit exceeded. Please try again later.")
            # Implement logic to handle the rate limit
            time.sleep(60)  # Sleep for 60 seconds before retrying
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""




    def getHeadlineQuestions(self, headline: str,about:str) -> list[str] | None:
        retry_count = 0
        max_retries = 1
        chain = self.headlineQPrompt | self.llm
        while retry_count < max_retries:
            try:
                res = chain.invoke({'headline': headline,'about': about})
                print("Full response:", res)
                print(type(res))

                # Directly target the 'text' key and remove the first line with "```Questions```"
                full_text = res.content
                print("Full text received:", full_text)

                # Split the text into lines and remove the first one
                lines = full_text.split('\n')[1:]
                print("Lines after splitting:", lines)

                # Filter out empty lines and ensure there's meaningful content
                questions_split = [line.strip() for line in lines if len(line.strip()) > 2]
                print("Filtered questions:", questions_split)

                if len(questions_split) > 0:
                    return questions_split
                break  # If questions are found, exit loop
            except RateLimitError:
                print("Rate limit exceeded. Retrying after 60 seconds.")
                time.sleep(60)  # Sleep for 60 seconds before retrying
            except Exception as e:
                print(f"An error occurred: {e}")
                break  # Break out of the loop if there's an unexpected error
            
            retry_count += 1

        return None

    def getNewHeadline(self, headline: str, qa: str) -> str:
        chain = self.newHeadlinePrompt | self.llm
        try:
            res = chain.invoke({'headline': headline, 'qa': qa})
            return res.content
        except RateLimitError as e:
            print("Rate limit exceeded. Please try again later.")
            # Implement logic to handle the rate limit
            time.sleep(60)  # Sleep for 60 seconds before retrying
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""

    def regenHeadline(self,headline):

        chain = self.regenHeadlinePrompt | self.llm
        try:
            res = chain.invoke({'headline': headline})
            return res.content
        except RateLimitError as e:
            print("Rate limit exceeded. Please try again later.")
            # Implement logic to handle the rate limit
            time.sleep(60)  # Sleep for 60 seconds before retrying
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""



    def getNewExperience(self, experience:str) -> str:
        chain = self.newExperience | self.llm
        try:
            res = chain.invoke({'experience': experience})
            return res.content
        except RateLimitError as e:
            print("Rate limit exceeded. Please try again later.")
            # Implement logic to handle the rate limit
            time.sleep(60)

    def regenExperience(self,experience):
            
            chain = self.regenExperiencePrompt | self.llm
            try:
                res = chain.invoke({'experience': experience})
                return res.content
            except RateLimitError as e:
                print("Rate limit exceeded. Please try again later.")
                # Implement logic to handle the rate limit
                time.sleep(60)

    def getNewProjects(self, projects: str,experience:str) -> str:
        chain = self.newProjects | self.llm
        try:
            res = chain.invoke({'projects': projects,"experience" : experience})
            return res.content
        except RateLimitError as e:
            print("Rate limit exceeded. Please try again later.")
            # Implement logic to handle the rate limit
            time.sleep(60)

    def regenProjects(self,projects):
            
            chain = self.regenNewProjectsPrompt | self.llm
            try:
                res = chain.invoke({'projects': projects})
                return res.content
            except RateLimitError as e:
                print("Rate limit exceeded. Please try again later.")
                # Implement logic to handle the rate limit
                time.sleep(60)

            
if __name__ == "__main__":
    bot = LLM_Bot()
    about = "I am a software engineer with 5 years of experience in web development. I have worked on multiple projects using Python, Django, and React. I am passionate about creating scalable web applications that provide value to users."
    headline = "Software Engineer | Python Developer | Django Expert | React Developer"
    print("New Headline:", bot.getNewHeadline(headline, "Question 1: What is your current role? \n Answer 1: I am a software engineer at XYZ company."))
    print("New Experience:", bot.getNewExperience("Software Engineer at XYZ Company (2019-Present)"))
    print("New Projects:", bot.getNewProjects("Project Manager at ABC Company (2017-2019)", "Software Engineer at XYZ Company (2019-Present)"))
