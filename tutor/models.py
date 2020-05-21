from py2neo import Graph, Node, Relationship, NodeMatcher
from datetime import datetime
import uuid

graph = Graph("http://localhost:7474", username="neo4j", password="neo4j1")
matcher = NodeMatcher(graph)


class Person:
    def __init__(self, username):
        self.username = username

    def find(self):
        user = matcher.match("Person", username=self.username).first()
        return user

    def register(self, name, password, p_type):
        if not self.find():
            user = Node("Person", name=name, username=self.username, password=password, type=p_type)
            graph.create(user)
            return True
        else:
            return False

    def confirm_passwords(self, password, confirm_password):

        if password == confirm_password:
            return True
        else:
            return False

    def verify_password(self, password):
        user = self.find()
        if user:
            if password == user['password']:
                return user
            else:
                return False
        else:
            return False

    def add_post(self, title, tags, text):
        user = self.find()
        post = Node(
            'Post',
            id=str(uuid.uuid4()),
            title=title,
            text=text,
            timestamp=timestamp(),
            date=date()
        )
        rel = Relationship(user, 'PUBLISHED', post)
        graph.create(rel)

        tags = [x.strip() for x in tags.lower().split(',')]
        for name in set(tags):
            tag = Node("Tag", name=name)
            # graph.merge(tag, "Tag", "name")

            rel = Relationship(tag, 'TAGGED', post)
            graph.create(rel)

    def like_post(self, post_id):
        user = self.find()
        post = matcher.match('Post', id=post_id).first()
        graph.merge(Relationship(user, 'LIKED', post))

    def get_recent_posts(self):
        query = '''
        MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
        WHERE user.username = $username
        RETURN post, COLLECT(tag.name) AS tags
        ORDER BY post.timestamp DESC LIMIT 5
        '''
        return graph.run(query, username=self.username)

    def get_similar_users(self):
        # Find three users who are most similar to the logged-in user
        # based on tags they've both blogged about.
        query = '''
        MATCH (you:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
              (they:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
        WHERE you.username = $username AND you <> they
        WITH they, COLLECT(DISTINCT tag.name) AS tags
        ORDER BY SIZE(tags) DESC LIMIT 3
        RETURN they.username AS similar_user, tags
        '''

        return graph.run(query, username=self.username)

    def get_commonality_of_user(self, other):
        # Find how many of the logged-in user's posts the other user
        # has liked and which tags they've both blogged about.
        query = '''
        MATCH (they:User {username: $they })
        MATCH (you:User {username: $you })
        OPTIONAL MATCH (they)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
                       (you)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
        RETURN SIZE((they)-[:LIKED]->(:Post)<-[:PUBLISHED]-(you)) AS likes,
               COLLECT(DISTINCT tag.name) AS tags
        '''

        return graph.run(query, they=other.username, you=self.username).next


class CourseClass:

    # Cria o nó "Answer" e faz as ligações necessárias para matricular o aluno a uma Disciplina
    def enrollment(self, title, user):
        username = Person(user).find()

        if self.find(title):
            question_answered = ""
            question = Question().get_random_question(title)
            a = Node("Answer", date=date(), question_answered=question_answered)
            graph.create(a)
            graph.merge(Relationship(username, 'HISTORIC', a))
            graph.merge(Relationship(a, 'BOND', question))
            return True
        else:
            return False

    def find(self, title):
        cc = matcher.match("CourseClass", title=title).first()
        return cc

    def create(self, title, username):
        if not self.find(title):
            user = Person(username).find()
            cc = Node("CourseClass", title=title)
            graph.create(cc)
            graph.merge(Relationship(cc, 'CREATED', user))
            return True
        else:
            return False

    def edit(self, title, cc, user):
        if not self.find(title):
            query = '''
                        MATCH (cc:CourseClass {title: $cc})<--(p:Person {username: $user})
                        SET cc.title = $title
                        RETURN cc
                        '''
            graph.run(query, title=title, cc=cc, user=user)
            return True
        else:
            return False

    def delete(self, title):
        if self.find(title):
            cc = matcher.match("CourseClass", title=title).first()
            graph.delete(cc)
            return True
        else:
            return False

    def get_student_course_classes(self, user):
        query = '''
                MATCH (p:Person {username: $user})-->()-->()-->()-->(cc:CourseClass)
                RETURN cc
                ORDER BY cc.title
                '''
        scc = list(graph.run(query, user=user))
        return scc

    def get_no_student_course_classes(self, user):
        query = '''
                MATCH (p:Person {username: $user})
                OPTIONAL MATCH (cc:CourseClass)
                WHERE NOT (p)-->()-->()-->()-->(cc)
                RETURN cc
                ORDER BY cc.title
                '''
        nscc = list(graph.run(query, user=user))
        return nscc

    def get_course_classes(self, user):
        query = '''
            MATCH (cc:CourseClass)<--(p:Person)
            WHERE p.username = $user
            RETURN cc
            ORDER BY cc.title
        '''
        cc = graph.run(query, user=user)
        return cc

    # método que verifica se a disciplina não tem nenhum relacionamento com outro assunto
    def find_single_course_class(self, cc):
        query = '''
                 MATCH (cc:CourseClass {title: $cc})
                 WHERE NOT (cc:CourseClass)<-->(:ClassSubject)
                 RETURN cc
                 '''
        cc = graph.run(query, cc=cc).evaluate()
        return cc


class ClassSubject:

# método que retorna a quantidade de nós ClassSubject
    def find_node_count(self, cc, title):
        query = '''
                    MATCH (cc:CourseClass {title: $cc})<-->(cs:ClassSubject)
                    OPTIONAL MATCH (cs)<-->(cs {title: $title})
                    RETURN count(cs)
                '''
        count = graph.evaluate(query, cc=cc, title=title)
        return count

    def find_in_course(self, cc, title):
        query = '''
                   MATCH (cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass)
                   WHERE cc.title = $cc AND cs.title = $title
                   RETURN cs
                   ORDER BY cs.order
                   '''
        cc = graph.run(query, cc=cc, title=title)
        return cc

    def get_class_subject_current_question(self, cc_title, user):
        query = '''
                MATCH (p:Person)-->(a:Answer)-->()-->(cs:ClassSubject)-->(cc:CourseClass {title: $cc_title})
                WHERE a.question_answered = "" AND p.username = $user
                RETURN cs
               '''
        cs = graph.run(query, cc_title=cc_title, user=user)
        return cs

# Retorna o valor do campo 'initial' de um Assunto específco através do título da Disciplina e do título do Assunto
    def get_initial_value(self, title, cc):
        query = '''
                   MATCH (cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass)
                   WHERE cc.title = $cc AND cs.title = $title
                   RETURN cs.initial
                   '''
        return graph.evaluate(query, title=title, cc=cc)

# Retorna o valor do campo 'initial' de um Assunto específco através do título da Disciplina e do título do Assunto
    def get_initial_id(self, cc_title):
        query = '''
                   MATCH (cc:CourseClass {title: $cc})<-[:TAUGHT]-(cs:ClassSubject)
                   WHERE cs.initial = "True"
                   RETURN id(cs)
                   '''
        return graph.evaluate(query, cc=cc_title)

    def get_initial(self, title, cc):
        query = '''
                   MATCH (cc:CourseClass {title: $cc})<-->(cs:ClassSubject {title: $title})
                   WHERE NOT cs.initial = "True"
                   RETURN cs
                   '''
        cs = graph.evaluate(query, title=title, cc=cc)
        return cs

    def find_previous(self, title, cc):
        query = '''match (cc:CourseClass {title:$cc})<-[:TAUGHT]-(cs:ClassSubject {title:$title})-[:PREVIOUS]->(
        c:ClassSubject) return c.title '''
        return graph.evaluate(query, title=title, cc=cc)

    def find_next(self, title, cc):
        query = '''match (cc:CourseClass {title:$cc})<-[:TAUGHT]-(cs:ClassSubject {title:$title})-[:FORWARD]->(
        c:ClassSubject) return c.title '''
        return graph.evaluate(query, title=title, cc=cc)

# Retorna o nó de um Assunto através do título do Assunto e do título da Disciplina
    def find_single_class_subject(self, title, cc_title):
        query = '''
                 MATCH (cc:CourseClass {title: $cc})<-->(cs:ClassSubject {title: $title})
                 WHERE NOT (cs)<-->(:Question)
                 RETURN cs
                 '''
        cc = graph.evaluate(query, cc=cc_title, title=title)
        return cc

    def create(self, course_class, title, ps, ns, support_material):
        if not self.find_in_course(course_class, title).evaluate():

            cc = CourseClass().find(course_class)

            fscc = CourseClass().find_single_course_class(course_class)

            if fscc:
                cs = Node("ClassSubject", title=title, initial="True", support_material=support_material)
            else:
                cs = Node("ClassSubject", title=title, initial="False", support_material=support_material)

            graph.create(cs)

            graph.merge(Relationship(cs, 'TAUGHT', cc))

            if ps:
                previous_subject = self.find_in_course(course_class, ps).evaluate()
                graph.merge(Relationship(cs, 'PREVIOUS', previous_subject))

            if ns:
                next_subject = self.find_in_course(course_class, ns).evaluate()
                graph.merge(Relationship(cs, 'FORWARD', next_subject))

            return True
        else:
            return False

    def edit(self, st, title, cc, ps, ns, sm, cb):
        query = '''
                    MATCH (cc:CourseClass {title: $cc})
                    OPTIONAL MATCH (cs:ClassSubject {title:$title})
                    WHERE (cc)<-->(cs)
                    SET cs.title = $st, cs.support_material = $sm, cs.initial = $cb
                    '''

        if cb == "False" and cb != self.get_initial_value(title, cc) and \
                self.find_node_count(cc, title) > 1:
            cb = "True"
            graph.run(query, title=title, cc=cc, st=st, sm=sm, cb=cb)

        elif cb == "False" and self.find_node_count(cc, title) == 1:
            graph.run(query, title=title, cc=cc, st=st, sm=sm, cb=cb)

        elif cb == "True" and cb != self.get_initial_value(title, cc):
            self.set_class_subject_False(cc)
            graph.run(query, title=title, cc=cc, st=st, sm=sm, cb=cb)

        else:
            graph.run(query, title=title, cc=cc, st=st, sm=sm, cb=cb)

        if ps:
            self.delete_previous_course_class(cc, title)
            self.create_relationship_course_class_previous(cc, title, ps)

        if ns:
            self.delete_forward_course_class(cc, title)
            self.create_relationship_course_class_forward(cc, title, ns)

        if not ps:
            self.delete_previous_course_class(cc, title)

        if not ns:
            self.delete_forward_course_class(cc, title)

        return True

    def delete_previous_course_class(self, cc, title):
        query = '''
                MATCH (cs:ClassSubject {title: $title})-[:TAUGHT]->(cc:CourseClass {title: $cc})
                OPTIONAL MATCH (cs)-[r:PREVIOUS]->(ps:ClassSubject)
                DELETE r
                '''
        graph.run(query, cc=cc, title=title)

    def delete_forward_course_class(self, cc, title):
        query = '''
                MATCH (cs:ClassSubject {title: $title})-[:TAUGHT]->(cc:CourseClass {title: $cc})
                OPTIONAL MATCH (cs)-[r:FORWARD]->(ps:ClassSubject)
                DELETE r
                '''
        graph.run(query, cc=cc, title=title)

    def create_relationship_course_class_previous(self, cc, title, ps):
        query = '''
                MATCH (cc:CourseClass)<-->(cs:ClassSubject), (cc:CourseClass)<-->(cs1:ClassSubject)
                WHERE (cc.title = $cc) AND (cs.title = $title) AND (cs1.title = $ps)
                CREATE (cs)-[r:PREVIOUS]->(cs1)
                '''
        graph.run(query, cc=cc, title=title, ps=ps)

    def create_relationship_course_class_forward(self, cc, title, ns):
        query = '''
                MATCH (cc:CourseClass)<-->(cs:ClassSubject), (cc:CourseClass)<-->(cs1:ClassSubject)
                WHERE (cc.title = $cc) AND (cs.title = $title) AND (cs1.title = $ns)
                CREATE (cs)-[r:FORWARD]->(cs1)
                '''
        graph.run(query, cc=cc, title=title, ns=ns)

    def set_class_subject_False(self, cc):
        query = '''
                MATCH (cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass)
                WHERE cc.title = $cc AND cs.initial = "True"
                SET cs.initial = "False"
                '''
        graph.run(query, cc=cc)

    def get_class_subjects(self, title):
        query = '''
                MATCH (cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass)
                WHERE cc.title = $title
                RETURN cs
                '''

        cc = graph.run(query, title=title)
        return cc

    def get_class_subjects_and_course_class(self, title):
        query = '''
                MATCH (cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass)
                WHERE cc.title = $title
                RETURN cs, cc
                '''

        cc = graph.run(query, title=title)
        return cc

    # Retorna o id do Assunto initial da Disciplina
    def get_id_class_subjects(self, cc_title):
        query = '''
                MATCH (cc:CourseClass)<--(cs:ClassSubject {title: $title})
                RETURN id(cs)
                '''

        cs_id = graph.run(query, title=cc_title)
        return cs_id

    def get_class_subjects_with_previous_and_forward(self, title):
        query = '''
                 MATCH (cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass {title: $title})
                 OPTIONAL MATCH (cs)-[:FORWARD]->(ns:ClassSubject)
                 OPTIONAL MATCH (cs)-[:PREVIOUS]->(ps:ClassSubject)
                 RETURN cs,  ns.title as ns_title, ps.title as ps_title
                 ORDER BY cs.order
                '''

        cc = graph.run(query, title=title)
        return cc

    def delete(self, title, cc):

        if self.find_in_course(title, cc):
            query = '''
                       MATCH (cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass)
                       WHERE cc.title = $cc AND cs.title = $title
                       RETURN cs
                       '''
            cs = graph.evaluate(query, cc=cc, title=title)
            graph.delete(cs)
            return True
        else:
            return False


class Question:

    # Retorna uma questão através do id (NÃO ESTA SENDO USADO)
    def find(self, id):
        question = matcher.match("Question", id=id).first()
        return question

    # Cria uma questão
    def create(self, cc, class_subject, title, body, support_material, difficulty, choice_a, choice_b, choice_c,
               choice_d, right_answer, user):
        cs = ClassSubject().find_in_course(cc, class_subject).evaluate()

        question = Node(
            "Question",
            id=str(uuid.uuid1()),
            title=title,
            body=body,
            support_material=support_material,
            difficulty=difficulty,
            choice_a=choice_a,
            choice_b=choice_b,
            choice_c=choice_c,
            choice_d=choice_d,
            right_answer=right_answer
        )
        graph.create(question)

        u = Person(user).find()

        graph.merge(Relationship(question, 'ASKED', cs))

        # graph.merge(Relationship(u, 'CREATED', question))
        return True

    # Edita uma questão através do id
    def edit(self, question_id, title, body, support_material, difficulty, choice_a, choice_b, choice_c,
             choice_d, right_answer):
        query = '''
                MATCH (q:Question {id: $question_id})
                SET q.title = $title, q.body = $body, q.support_material = $support_material, q.difficulty = 
                $difficulty, q.choice_a = $choice_a, q.choice_b = $choice_b, q.choice_c = $choice_c, q.choice_d =
                $choice_d, q.right_answer = $right_answer
                '''
        graph.run(query, question_id=question_id, title=title, body=body, support_material=support_material,
                  difficulty=difficulty, choice_a=choice_a, choice_b=choice_b, choice_c=choice_c, choice_d=choice_d,
                  right_answer=right_answer)
        return True

    # Retorna uma questão atráves do título da Disciplina e do título do Assunto
    def get_questions(self, cs_title, cc_title):
        query = '''
            MATCH (q:Question)-[:ASKED]->(cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass)
            WHERE cs.title = $cs_title and cc.title = $cc_title
            RETURN q
            ORDER BY q.title
            '''
        question = graph.run(query, cs_title=cs_title, cc_title=cc_title)
        return question

    # Retorna uma questão através do id
    def get_question(self, question_id):
        query = '''
            MATCH (q:Question {id: $question_id})
            RETURN q
            '''
        question = graph.run(query, question_id=question_id)
        return question

    # Retorna uma questão aleatória de um Assunto específico
    def get_random_question(self, cc_title):
        cs_id_initial = ClassSubject().get_initial_id(cc_title)

        query = '''
                MATCH (cs:ClassSubject)<-[:ASKED]-(q:Question)
                WHERE id(cs) = $cs_id
                WITH q, rand() as rand
                ORDER BY rand LIMIT 1
                RETURN id(q)
            '''
        id = graph.run(query, cs_id=cs_id_initial).evaluate()
        return matcher.get(id)

    # TO DO
    def get_second_random_question(self, cs_title):
        query = '''
                MATCH (cs:ClassSubject)<-[:ASKED]-(q:Question)
                WHERE id(cs) = $cs_id
                WITH q, rand() as rand
                ORDER BY rand LIMIT 1
                RETURN id(q)
            '''
        id = graph.run(query, cs_title=cs_title).evaluate()
        return matcher.get(id)


    # Retorna a questão atual, não respondida, de uma Disciplina
    def get_current_question(self, cc_title, user):

        query = '''
                MATCH (p:Person)-->(a:Answer)-->(q:Question)-->()-->(cc:CourseClass {title: $cc_title})
                WHERE a.question_answered = "" AND p.username = $user
                RETURN q
            '''
        question = graph.run(query, cc_title=cc_title, user=user)
        return question

    # Exclui uma questão
    def delete(self, id):
        if self.find(id):
            question = matcher.match("Question", id=id).first()
            graph.delete(question)
            return True
        else:
            return False


class Answer:
    def set_answer_question(self, alternative_answered, user):
        query = '''
            MATCH (p:Person {username:$user})-->(a:Answer)
            WHERE a.question_answered = ''
            SET a.question_answered = $alternative_answered
        '''
        graph.run(query, user=user, alternative_answered=alternative_answered)
        return True


# Funcões legadas
def get_todays_recent_posts():
    query = '''
        MATCH (user:Person)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
        WHERE post.date = $today
        RETURN user.username AS username, post, COLLECT(tag.name) AS tags
        ORDER BY post.timestamp DESC LIMIT 5
        '''

    return graph.run(query, today=date())


def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()


def date():
    return datetime.now().strftime('%Y-%m-%d')
