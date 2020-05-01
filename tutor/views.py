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
        confirm_password = request.form['confirm_password']
        p_type = "student"

        if not Person(username).confirm_passwords(password, confirm_password):
            flash('As senhas não são iguais')
            return render_template('register.html',
                                   name=name,
                                   username=username
                                   )

        elif Person(username).find():
            flash('Nome de usuário já existente')
            return render_template('register.html')

        else:
            session['username'] = username
            session['name'] = name
            session['type'] = p_type
            Person(username).register(name, password, p_type)
            flash('Cadastro efetuado com sucesso.')
            return redirect(url_for('login'))

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

            # if user['type'] == 'student':
            # chamar funções das duas listas
            # return render_template('index.html, param=param)

            return render_template('index.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Você saiu do sistema.')
    return redirect(url_for('index'))


# COURSE CLASS #
@app.route('/enrollment_course_class/<cc>/<user>')
def enrollment_course_class(cc, user):
    check_if_student()
    if not CourseClass().enrollment(cc, user):
        flash('Erro ao matricular-se Disciplina')
    else:
        flash('Matrícula realizada com sucesso.')

    return redirect(url_for('open_course_class_student',
                            user=user))


@app.route('/edit_course_class/<user>', methods=['GET', 'POST'])
def edit_course_class(user):
    check_if_teacher()

    if request.method == 'POST':
        cc = request.form['cc']
        title = request.form['title']

        if not CourseClass().edit(title, cc):
            flash('Erro ao alterar Disciplina')
        else:
            flash('Disciplina alterada com sucesso.')

    course_classes = list(CourseClass().get_course_classes(user))
    return render_template(
        'course_class.html',
        cc=course_classes
    )

@app.route('/open_edit_course_class/<title>')
def open_edit_course_class(title):
    check_if_teacher()

    return render_template(
        'edit_course_class.html',
        cc=title
    )


@app.route('/open_course_class/<user>')
def open_course_class(user):
    check_if_teacher()

    course_classes = list(CourseClass().get_course_classes(user))
    return render_template(
        'course_class.html',
        cc=course_classes
    )


@app.route('/open_course_class_student/<user>')
def open_course_class_student(user):
    check_if_student()

    student_course_classes = CourseClass().get_student_course_classes(user)
    no_student_course_classes = CourseClass().get_no_student_course_classes(user)

    return render_template(
        'course_class_student.html',
        scc=student_course_classes,
        nscc=no_student_course_classes
    )


@app.route('/create_course_class', methods=['GET', 'POST'])
def create_course_class():
    check_if_teacher()

    if request.method == 'POST':
        title = request.form['title']
        username = request.form['username']

        if len(title) < 1:
            flash('A Disciplina deve possuir pelo menos 1 caractere')
        elif not CourseClass().create(title, username):
            flash('Disciplina já existente')
        else:
            flash('Disciplina criada com sucesso.')

    return redirect(request.referrer)


@app.route('/confirm_delete_course_class/<title>')
def confirm_delete_course_class(title):
    check_if_teacher()

    flash('Tem certeza de deseja excluir essa Disciplina?')

    return render_template(
        'confirm_delete_course_class.html',
        cc=title
    )


@app.route('/delete_course_class/<title>')
def delete_course_class(title):
    check_if_teacher()

    if not CourseClass().find_single_course_class(title):
        flash('Disciplina com relacionamento, não pode ser excluida.')
    else:
        CourseClass().delete(title)
        flash('Disciplina excluida com sucesso.')

    return redirect(url_for('open_course_class'))


# CLASS SUBJECT #
@app.route('/edit_class_subject/', methods=['GET', 'POST'])
def edit_class_subject():
    check_if_teacher()

    if request.method == 'POST':
        cc = request.form['cc']
        title = request.form['title']
        st = request.form['subject_title']
        ps = request.form['previous_subject']
        ns = request.form['next_subject']
        sm = request.form['support_material']
        cb = request.form['checkbox_initial']

        if not ClassSubject().edit(st, title, cc, ps, ns, sm, cb):
            flash('Erro ao alterar assunto')
        else:
            flash('Assunto alterado com sucesso.')

    return redirect(url_for('open_class_subject', title=cc))


@app.route('/open_edit_class_subject/<title>/<cc>')
def open_edit_class_subject(title, cc):
    check_if_teacher()

    class_subjects = list(ClassSubject().get_class_subjects_and_course_class(cc))

    cs = ClassSubject().find_in_course(cc, title)
    ini = ClassSubject().get_initial_value(title, cc)

    ps = ClassSubject().find_previous(title, cc)
    ns = ClassSubject().find_next(title, cc)

    return render_template(
        'edit_class_subject.html',
        cc=cc,
        title=title,
        ps=ps,
        ns=ns,
        cs=class_subjects,
        support_material=cs.evaluate()["support_material"],
        initial=ini
    )


@app.route('/open_class_subject/<title>')
def open_class_subject(title):
    check_if_teacher()

    class_subjects = list(ClassSubject().get_class_subjects_with_previous_and_forward(title))

    return render_template(
        'class_subject.html',
        cc=title,
        cs=class_subjects
    )


@app.route('/confirm_delete_class_subject/<cs_title>/<cc_title>')
def confirm_delete_class_subject(cs_title, cc_title):
    check_if_teacher()

    flash('Tem certeza de deseja excluir esse assunto?')

    return render_template(
        'confirm_delete_class_subject.html',
        cc=cc_title,
        cs=cs_title
    )


@app.route('/delete_class_subject/<cs_title>/<cc_title>')
def delete_class_subject(cs_title, cc_title):
    check_if_teacher()

    if not ClassSubject().find_single_class_subject(cs_title, cc_title):
        flash('Assunto possui questões, não pode ser excluído.')
    elif not ClassSubject().get_initial_value(cs_title, cc_title):
        flash('Assunto inicial, não pode ser excluído.')
    else:
        ClassSubject().delete(cs_title, cc_title)
        flash('Assunto excluído com sucesso.')

    return redirect(url_for('open_class_subject', title=cc_title))


@app.route('/create_class_subject', methods=['GET', 'POST'])
def create_class_subject():
    check_if_teacher()

    if request.method == 'POST':
        title = request.form['subject_title']
        cc = request.form['cc']
        support_material = request.form['support_material']
        ps = request.form.get('previous_subject')
        ns = request.form.get('next_subject')

        if len(title) < 1:
            flash('O assunto deve possuir pelo menos 1 caractere')
        elif not ClassSubject().create(cc, title, ps, ns, support_material):
            flash('Assunto já existente')
        else:
            flash('Assunto criado com sucesso.')

    return redirect(request.referrer)


# QUESTIONS #
@app.route('/edit_question/<question_id>/<cs>/<cc>', methods=['GET', 'POST'])
def edit_question(question_id, cs, cc):
    check_if_teacher()

    if request.method == 'POST':
        title = request.form['question_title']
        body = request.form['question_body']
        support_material = request.form['support_material']
        difficulty = request.form['difficulty']
        choice_a = request.form['choice_a']
        choice_b = request.form['choice_b']
        choice_c = request.form['choice_c']
        choice_d = request.form['choice_d']
        right_answer = request.form['right_answer']

        if len(title) < 1:
            flash('O título da questão deve possuir pelo menos 1 caractere')
            return redirect(url_for('open_edit_questions', question_id=question_id, cs_title=cs, cc_title=cc))

        else:
            Question().edit(question_id, title, body, support_material, difficulty, choice_a, choice_b, choice_c,
                            choice_d, right_answer)
            flash('Questão alterado com sucesso.')
            return redirect(url_for('open_questions', cs_title=cs, cc_title=cc))


@app.route('/open_edit_questions/<question_id>/<cs_title>/<cc_title>')
def open_edit_questions(question_id, cs_title, cc_title):
    check_if_teacher()

    question = Question().get_question(question_id).evaluate()

    return render_template(
        'edit_question.html',
        cc=cc_title,
        cs=cs_title,
        q=question
    )


@app.route('/open_answer_questions/<cc_title>/<user>')
def open_answer_questions(cc_title, user):
    check_if_student()

    question = Question().get_current_question(cc_title, user).evaluate()
    cs_title = ClassSubject().get_class_subject_current_question(cc_title, user).evaluate()

    return render_template(
        'answer_question.html',
        cc=cc_title,
        cs=cs_title,
        q=question,
        username=user
    )


@app.route('/answer_question', methods=['GET', 'POST'])
def answer_question():
    check_if_student()

    if request.method == 'POST':
        cs = request.form['cs']
        cc = request.form['cc']
        right_answer = request.form['right_answer']
        alternative_answered = request.form['alternative_answered']

    if alternative_answered == right_answer:
        flash('Acertou miseravi')
    else:
        flash('Eroooouuuuu...', category='error')

    return render_template(
        'alert_question_answered.html',
        cs=cs,
        cc=cc,
        q=right_answer,
        alternative_answered=alternative_answered
    )


@app.route('/open_questions/<cs_title>/<cc_title>', methods=['GET', 'POST'])
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
        support_material = request.form['support_material']
        difficulty = request.form['difficulty']
        choice_a = request.form['choice_a']
        choice_b = request.form['choice_b']
        choice_c = request.form['choice_c']
        choice_d = request.form['choice_d']
        right_answer = request.form['right_answer']

        if len(title) < 1:
            flash('O título deve possuir pelo menos 1 caractere')
        elif len(body) < 1:
            flash('O enuciado deve possuir pelo menos 1 caractere')
        elif len(choice_a) < 1:
            flash('A alternativa A deve possuir pelo menos 1 caractere')
        elif not Question().create(cc, cs, title, body, support_material, difficulty, choice_a, choice_b, choice_c,
                                   choice_d, right_answer,
                                   session["username"]):
            flash('Erro ao cadastrar questão')
        else:
            flash('Questão criada com sucesso.')

    return redirect(request.referrer)


@app.route('/confirm_delete_question/<id>/<cc>/<cs>')
def confirm_delete_question(id, cc, cs):
    check_if_teacher()
    flash('Tem certeza que deseja excluir essa questão?')

    return render_template(
        'confirm_delete_question.html',
        id=id,
        cc=cc,
        cs=cs
    )


@app.route('/delete_question/<id>/<cc>/<cs>')
def delete_question(id, cc, cs):
    check_if_teacher()
    Question().delete(id)
    flash('Questão excluida com sucesso.')

    return redirect(url_for('open_questions', cs_title=cs, cc_title=cc))


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


# VERIFICA USUARIO #
def check_if_teacher():
    username = session.get('username')
    t = session.get('type')

    if not username and t != 'teacher':
        flash('Você não está logado como professor.')
        return redirect(url_for('login'))


def check_if_student():
    username = session.get('username')
    t = session.get('type')

    if not username and t != 'student':
        flash('Você não está logado como aluno.')
        return redirect(url_for('login'))
