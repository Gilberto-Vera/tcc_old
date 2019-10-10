from .models import Person, CourseClass, ClassSubject, Question, get_todays_recent_posts
from flask import Flask, request, session, redirect, url_for, render_template, flash

app = Flask(__name__)


@app.route('/')
def index():
    # session['username'] = 'sirlon'
    # session['type'] = 'teacher'
    # posts = get_todays_recent_posts()
    return render_template('index.html')


# REGISTRO, LOGIN E LOGOUT #
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        type = "student"

        if len(username) < 1:
            flash('Nome de usuário deve possuir pelo menos 1 caractere')
        elif len(password) < 5:
            flash('Senha deve ter pelo menos 5 caracteres')
        elif not Person(username).register(name, password, type):
            flash('Nome de usuário já existente')
        else:
            session['username'] = username
            session['name'] = name
            session['type'] = "student"
            flash('Login efetuado com sucesso.')
            return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Person(username).verify_password(password)
        if not user:
            flash('Nome de usuário ou senha incorretos')
        else:
            session['username'] = username
            session['type'] = user['type']
            session['person_name'] = user['name']
            flash('Login efetuado com sucesso.')
            return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Você saiu do sistema.')
    return redirect(url_for('index'))


# COURSE CLASS #
@app.route('/edit_course_class', methods=['GET', 'POST'])
def edit_course_class():
    check_if_teacher()

    if request.method == 'POST':
        cc = request.form['cc']
        title = request.form['title']

        if not CourseClass().edit(title, cc):
            flash('Erro ao alterar Disciplina')
        else:
            flash('Disciplina alterada com sucesso.')

    return redirect(url_for('open_course_class'))


@app.route('/open_edit_course_class/<title>')
def open_edit_course_class(title):
    check_if_teacher()

    return render_template(
        'edit_course_class.html',
        cc=title
    )


@app.route('/open_course_class')
def open_course_class():
    check_if_teacher()

    course_classes = CourseClass().get_course_classes()
    return render_template(
        'course_class.html',
        cc=course_classes
    )


@app.route('/create_course_class', methods=['GET', 'POST'])
def create_course_class():
    check_if_teacher()

    if request.method == 'POST':
        title = request.form['title']

        if not CourseClass().create(title):
            flash('Disciplina já existente')
        else:
            flash('Disciplina criada com sucesso.')

    return redirect(request.referrer)


@app.route('/delete_course_class/<title>')
def delete_course_class(title):
    check_if_teacher()

    if not CourseClass().delete(title):
        flash('Disciplina não encontrada')
    else:
        flash('Disciplina excluida com sucesso.')

    return redirect(request.referrer)

# QUESTIONS #
@app.route('/open_questions/<cs_title>/<cc_title>')
def open_questions(cs_title, cc_title):
    check_if_teacher()

    questions = list(Question().get_questions(cs_title, cc_title))

    return render_template(
        'question.html',
        cs=cs_title,
        cc=cc_title,
        q=questions
    )


@app.route('/create_question', methods=['GET', 'POST'])
def create_question():
    check_if_teacher()

    if request.method == 'POST':
        cs = request.form['cs']
        cc = request.form['cc']
        title = request.form['question_title']
        body = request.form['question_body']
        difficulty = request.form['difficulty']
        choice_a = request.form['choice_a']
        choice_b = request.form['choice_b']
        choice_c = request.form['choice_c']
        choice_d = request.form['choice_d']
        right_answer = request.form['right_answer']

        if not Question().create(cc, cs, title, body, difficulty, choice_a, choice_b, choice_c, choice_d, right_answer,
                                 session["username"]):
            flash('Erro ao cadastrar questão')
        else:
            flash('Questão criada com sucesso.')

    return redirect(request.referrer)


@app.route('/delete_question/<id>')
def delete_question(id):
    check_if_teacher()
    if not Question().delete(id):
        flash('Questão não encontrada')
    else:
        flash('Questão excluida com sucesso.')

    return redirect(request.referrer)

# CLASS SUBJECT #
@app.route('/edit_class_subject', methods=['GET', 'POST'])
def edit_class_subject():
    check_if_teacher()

    if request.method == 'POST':
        cc = request.form['cc']
        title = request.form['title']

        if not CourseClass().edit(title, cc):
            flash('Erro ao alterar Disciplina')
        else:
            flash('Disciplina alterada com sucesso.')

    return redirect(url_for('open_course_class'))


@app.route('/open_edit_class_subject/<title>/<cc>')
def open_edit_class_subject(title, cc):
    check_if_teacher()

    class_subjects = list(ClassSubject().get_class_subjects(cc))

    ps = ClassSubject().find_previous(title, cc)
    ns = ClassSubject().find_next(title, cc)

    return render_template(
        'edit_class_subject.html',
        cc=cc,
        title=title,
        ps=ps,
        ns=ns,
        cs=class_subjects
    )


@app.route('/open_class_subject/<title>')
def open_class_subject(title):
    check_if_teacher()

    class_subjects = list(ClassSubject().get_class_subjects(title))

    return render_template(
        'class_subject.html',
        cc=title,
        cs=class_subjects
    )


@app.route('/delete_class_subject/<cs_title>/<cc_title>')
def delete_class_subject(cs_title, cc_title):
    check_if_teacher()

    if not ClassSubject().delete(cs_title, cc_title):
        flash('Assunto não encontrada')
    else:
        flash('Assunto excluido com sucesso.')

    return redirect(request.referrer)


@app.route('/create_class_subject', methods=['GET', 'POST'])
def create_class_subject():
    check_if_teacher()

    if request.method == 'POST':
        title = request.form['subject_title']
        cc = request.form['cc']
        ps = request.form.get('previous_subject')
        ns = request.form.get('next_subject')

        if len(title) < 1:
            flash('O assunto deve possuir pelo menos 1 caractere')
        elif not ClassSubject().create(cc, title, ps, ns):
            flash('Assunto já existente')
        else:
            flash('Assunto criado com sucesso.')

    return redirect(request.referrer)


# MÉTODOS LEGADOS DO EXEMPLO #
@app.route('/add_post', methods=['POST'])
def add_post():
    title = request.form['title']
    tags = request.form['tags']
    text = request.form['text']

    if not title:
        flash('You must give your post a title.')
    elif not tags:
        flash('You must give your post at least one tag.')
    elif not text:
        flash('You must give your post a text body.')
    else:
        Person(session['username']).add_post(title, tags, text)

    return redirect(url_for('index'))


@app.route('/like_post/<post_id>')
def like_post(post_id):
    username = session.get('username')

    if not username:
        flash('You must be logged in to like a post.')
        return redirect(url_for('login'))

    Person(username).like_post(post_id)

    flash('Liked post.')
    return redirect(request.referrer)


@app.route('/profile/<username>')
def profile(username):
    logged_in_username = session.get('username')
    user_being_viewed_username = username

    user_being_viewed = Person(user_being_viewed_username)
    posts = user_being_viewed.get_recent_posts()

    similar = []
    common = []

    if logged_in_username:
        logged_in_user = Person(logged_in_username)

        if logged_in_user.username == user_being_viewed.username:
            similar = logged_in_user.get_similar_users()
        else:
            common = logged_in_user.get_commonality_of_user(user_being_viewed)

    return render_template(
        'profile.html',
        username=username,
        posts=posts,
        similar=similar,
        common=common
    )


# VERIFICA SE É PROFESSOR #
def check_if_teacher():
    username = session.get('username')
    t = session.get('type')

    if not username and t != 'teacher':
        flash('Você não está logado como professor.')
        return redirect(url_for('login'))
