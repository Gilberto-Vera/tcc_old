from py2neo import Graph, Node, Relationship, NodeMatcher
from datetime import datetime
import uuid

graph = Graph("http://localhost:7474", username="neo4j", password="neo4j1")
matcher = NodeMatcher(graph)


class Person:
    def __init__(self, username):
        self.username = username

    def find(self):
        user = matcher.match("Person", username__exact=self.username).first()
        return user

    def register(self, name, password, type):
        if not self.find():
            user = Node("Person", name=name, username=self.username, password=password, type=type)
            graph.create(user)
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
            #graph.merge(tag, "Tag", "name")

            rel = Relationship(tag, 'TAGGED', post)
            graph.create(rel)

    def like_post(self, post_id):
        user = self.find()
        post = matcher.match('Post', id__exact=post_id).first()
        graph.merge(Relationship(user, 'LIKED', post))

    def get_recent_posts(self):
        query = '''
        MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
        WHERE user.username = {username}
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
        WHERE you.username = {username} AND you <> they
        WITH they, COLLECT(DISTINCT tag.name) AS tags
        ORDER BY SIZE(tags) DESC LIMIT 3
        RETURN they.username AS similar_user, tags
        '''

        return graph.run(query, username=self.username)

    def get_commonality_of_user(self, other):
        # Find how many of the logged-in user's posts the other user
        # has liked and which tags they've both blogged about.
        query = '''
        MATCH (they:User {username: {they} })
        MATCH (you:User {username: {you} })
        OPTIONAL MATCH (they)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
                       (you)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
        RETURN SIZE((they)-[:LIKED]->(:Post)<-[:PUBLISHED]-(you)) AS likes,
               COLLECT(DISTINCT tag.name) AS tags
        '''

        return graph.run(query, they=other.username, you=self.username).next


class CourseClass:
    def find(self, title):
        cc = matcher.match("CourseClass", title__exact=title).first()
        return cc

    def create(self, title):
        if not self.find(title):
            cc = Node("CourseClass", title=title)
            graph.create(cc)
            return True
        else:
            return False

    def edit(self, title, cc):
        query = '''
                    MATCH (cc:CourseClass {title: {cc}})
                    SET cc.title = {title}
                    RETURN cc
                    '''
        graph.run(query, title=title, cc=cc)
        return True

    def delete(self, title):
        if self.find(title):
            cc = matcher.match("CourseClass", title__exact=title).first()
            graph.delete(cc)
            return True
        else:
            return False

    def get_course_classes(self):
        cc = matcher.match("CourseClass").order_by("_.title")
        return cc

    # método que verifica se a disciplina não tem nenhum relacionamento com outro assunto
    def find_single_course_class(self, cc):
        query = '''
                 match (cc:CourseClass {title: {cc}})
                 where not (cc:CourseClass)<-->(:ClassSubject)
                 return cc
                 '''
        cc = graph.evaluate(query, cc=cc)
        return cc


class ClassSubject:
    def find_in_course(self, cc, title):
        query = '''
                   MATCH (cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass)
                   WHERE cc.title = {cc} AND cs.title = {title}
                   RETURN cs
                   ORDER BY cs.order
                   '''
        cc = graph.run(query, cc=cc, title=title)
        return cc

    def find_inicial(self, title, cc):
        query = '''
                   MATCH (cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass)
                   WHERE cc.title = {cc} AND cs.title = {title}
                   RETURN cs.inicial
                   '''
        return graph.evaluate(query, title=title, cc=cc)

    def find_previous(self, title, cc):
        query = '''
                match (cc:CourseClass {title:{cc}})<-[:TAUGHT]-(cs:ClassSubject {title:{title}})-[:PREVIOUS]->(c:ClassSubject)
                return c.title
                '''
        return graph.evaluate(query, title=title, cc=cc)

    def find_next(self, title, cc):
        query = '''
                match (cc:CourseClass {title:{cc}})<-[:TAUGHT]-(cs:ClassSubject {title:{title}})-[:FORWARD]->(c:ClassSubject)
                return c.title
                '''
        return graph.evaluate(query, title=title, cc=cc)

    def create(self, course_class, title, ps, ns, support_material):
        if not self.find_in_course(course_class, title).evaluate():

            cc = CourseClass().find(course_class)

            fscc = CourseClass().find_single_course_class(course_class)

            if fscc:
                cs = Node("ClassSubject", title=title, inicial=True, support_material=support_material)
            else:
                cs = Node("ClassSubject", title=title, inicial=False, support_material=support_material)

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

    def get_class_subjects(self, title):
        query = '''
                MATCH (cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass)
                WHERE cc.title = {title}
                RETURN cs, cc
                '''

        cc = graph.run(query, title=title)
        return cc

    def get_class_subjects_with_previous_and_forward(self, title):
        query = '''
                 MATCH (cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass {title: {title}})
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
                       WHERE cc.title = {cc} AND cs.title = {title}
                       RETURN cs
                       '''
            cs = graph.evaluate(query, cc=cc, title=title)
            graph.delete(cs)
            return True
        else:
            return False


class Question:
    def find(self, id):
        question = matcher.match("Question", id__exact=id).first()
        return question

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

        graph.merge(Relationship(u, 'CREATED', question))
        return True

    def get_questions(self, cs_title, cc_title):
        query = '''
            MATCH (q:Question)-[:ASKED]->(cs:ClassSubject)-[:TAUGHT]->(cc:CourseClass)
            WHERE cs.title = {cs_title} and cc.title = {cc_title}
            RETURN q
            ORDER BY q.title
            '''
        question = graph.run(query, cs_title=cs_title, cc_title=cc_title)
        return question

    def delete(self, id):
        if self.find(id):
            question = matcher.match("Question", id__exact=id).first()
            graph.delete(question)
            return True
        else:
            return False

def get_todays_recent_posts():
    query = '''
    MATCH (user:Person)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
    WHERE post.date = {today}
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
