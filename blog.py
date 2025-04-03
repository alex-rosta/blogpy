from flask import Flask, render_template, request, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os
from flask_flatpages import FlatPages
from flask_frozen import Freezer
from dotenv import load_dotenv

DEBUG = True
FLATPAGES_AUTO_RELOAD = DEBUG
FLATPAGES_EXTENSION = '.md'
FLATPAGES_ROOT = 'content'
POST_DIR = 'posts'
UPLOAD_FOLDER = os.path.join(FLATPAGES_ROOT, POST_DIR)

app = Flask(__name__)
app.secret_key = os.getenv('secret_key')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'md'}

flatpages = FlatPages(app)
freezer = Freezer(app)

load_dotenv()

# Configure OAuth
oauth = OAuth(app)
github = oauth.register(
    name= os.getenv('name'),
    client_id=os.getenv('client_id'),
    client_secret=os.getenv('client_secret'),
    redirect_uri=os.getenv('redirect_uri'),
    access_token_url=os.getenv('access_token_url'),
    authorize_url=os.getenv('authorize_url'),
    api_base_url=os.getenv('api_base_url'),
    client_kwargs={'scope': 'user:email'},
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = github.authorize_access_token()
    user = github.get('user').json()
    session['user'] = user
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/uploads/', methods=['GET', 'POST'])
def uploads():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    if user['login'] != os.getenv('allowed_user'):
        return redirect(url_for('login')), session.pop('user', None)
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400
        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return "File uploaded successfully", 200
    return render_template('uploads.html')

@app.route('/posts/')
def posts():
    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]
    posts.sort(key=lambda item: item['date'], reverse=False)
    return render_template('posts.html', posts=posts)

@app.route('/posts/<name>/')
def post(name):
    path = '{}/{}'.format(POST_DIR, name)
    post = flatpages.get_or_404(path)
    return render_template('post.html', post=post)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)