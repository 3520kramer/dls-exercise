from flask import Flask, render_template

app = Flask(__name__)

def listcomp():
    return [i for i in range(10)]

posts = [
    {
        'Name':'Person 1'
    },
    {
        'Name': listcomp()
    }
]



# decorator which takes in the route from the url
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', posts=posts) # posts is a variable we can use in our html

@app.route('/about')
def about():
    return render_template('about.html', title='About')

# makes it runnable from python by typing 'python demo_app.py' in terminal
if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=80)