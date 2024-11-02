from flask import Flask,render_template,request
from linkeden import Bot,ProfileScrapper




class App:
    def __init__(self) -> None:
        self.app = Flask(__name__)
        self.scrapper = ProfileScrapper()
        self.bot = Bot()
        
        @self.app.route("/")
        def index():
            return render_template('index.html')

        @self.app.route("/questions",methods=['POST'])
        def questions():
            print(request.form)
            url = request.form['url']
            print(url)
            about  = self.scrapper(rf"{url}")
            print(about)
            questions = self.bot.getQuestions(about)


            print(questions)
            questions=questions[1:-1]
            numOfQuestions = len(questions)
            return render_template('questions.html',about=about,questions=questions,numOfQuestions=numOfQuestions)
        

        @self.app.route("/newAbout",methods=['POST'])
        def newAbout():
            about = """As a dedicated computer science student at Bahria University, I am passionate about leveraging technology to solve complex problems. My academic journey has provided me with a solid foundation in various aspects of computer science, including data science, AI engineering, and web development.

My journey in the tech industry is characterized by a relentless pursuit of knowledge and excellence. I am continually seeking out new learning opportunities and staying updated with the latest industry advancements. This commitment to growth has shaped me into a versatile and adaptable professional.

I am eager to take on new challenges and opportunities that allow me to apply my skills in innovative ways. I am open to collaborating on projects across different domains and industries, as versatility and adaptability are key to success in the tech world.

Feel free to connect with me to discuss potential collaborations and opportunities, or simply to share insights about the ever-changing world of technology."""
            numOfQuestions = request.form['numOfQuestions']
            numOfQuestions = int(numOfQuestions)
            # numOfQuestions = 7
            print(numOfQuestions)
            qa = ''
            for i in range(1,int(numOfQuestions)+1):
                question = request.form[f'question_{i}']
                answer = request.form[f'answer_{i}']
                qa += f"Question {i}: {question}\n"
                qa += f"Answer {i}: {answer}\n"
                

            print(qa)
            newAbout = self.bot.getNewAbout(about,qa)
            return render_template('newAbout.html',newAbout=newAbout,oldAbout=about)
        self.app.run(debug=True)

if __name__ == "__main__":
    app = App()
