from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import constants
import model
from model import Comment
from model import Document
from model import Sentence
from model import Tag
from model import Translation
from model import User
from model import PersonaUser

from flask import _app_ctx_stack

def get_session():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'db_session'):
        engine = create_engine(constants.THEDB, echo=False)
        Session = sessionmaker(bind=engine)
        top.db_session = Session()
    return top.db_session

def list_documents():
    """Returns a list of all the Document objects."""
    out = []
    session = get_session()
    for instance in session.query(Document).order_by(Document.id): 
        out.append(instance)
    return out

def list_tags():
    """Returns a list of all the Tag objects."""
    session = get_session()
    return session.query(Tag).order_by(Tag.text)

def documents_for_tagname(tagname):
    """Returns a list of all the Documents that pertain to a certain tag."""
    session = get_session()
    tag = session.query(Tag).filter_by(text=tagname).first() 
    if not tag: return []
    return tag.documents

def sentences_for_document(docid):
    """Returns a list of sentences for the given docid."""
    out = []
    session = get_session()
    for instance in session.query(Sentence).\
                            filter(Sentence.docid == docid).\
                            order_by(Sentence.id): 
        out.append(instance)
    return out

def translations_for_document(docid):
    """Returns a list of translations for the given docid."""
    out = []
    session = get_session()
    for instance in session.query(Translation).\
                    filter(Translation.docid == docid).\
                    order_by(Translation.sentenceid, Translation.id.desc()): 
        out.append(instance)
    return out

def translations_for_sentence(sentid):
    """Returns a list of translations for the given sentid."""
    out = []
    session = get_session()
    for instance in session.query(Translation).\
                    filter(Translation.sentenceid == sentid).\
                    order_by(Translation.id.desc()): 
        out.append(instance)
    return out

def comments_for_sentence(sentid):
    """Returns a list of comments for the given sentid."""
    out = []
    session = get_session()
    for instance in session.query(Comment).\
                    filter(Comment.sentenceid == sentid).\
                    order_by(Comment.id.desc()): 
        out.append(instance)
    return out

def things_for_sentence_with_user(sentid, klass):
    session = get_session()
    out = []
    for thing,user in session.query(klass,User).\
                         join(User).\
                         filter(klass.userid == User.id).\
                         filter(klass.sentenceid == sentid):
        out.append((thing,user))
    return out

def latest_translation_for_sentence(sentid):
    """Returns the latest translation for the given sentid."""
    out = []
    session = get_session()
    return session.query(Translation).\
                   filter(Translation.sentenceid == sentid).\
                   order_by(Translation.id.desc()).\
                   first()

def sentences_with_translations_for_document(docid):
    """Returns a list of translations for the given docid."""
    session = get_session()
    out = []
    for s,t in session.query(Sentence,Translation).\
                         outerjoin(Translation).\
                         filter(Sentence.docid == docid).\
                         order_by(Sentence.id, Translation.id.desc()):
        out.append((s,t))
    return out

def get_sentence(sentenceid):
    """Lookup a sentence by sentenceid. Return the model object."""
    session = get_session()
    sentence = session.query(Sentence).get(sentenceid)
    return sentence

def get_user(userid):
    """Lookup a user by userid. Return the model object."""
    session = get_session()
    user = session.query(User).get(userid)
    return user

def lookup_username(username):
    """Lookup a user by userid. Return the model object or None."""
    session = get_session()
    user = session.query(User).filter(User.username == username).first()
    return user

def save_thing(klass, userid, docid, sentenceid, text):
    """Save either a translation or a comment."""
    session = get_session()

    sentence = get_sentence(sentenceid)
    assert sentence.docid == docid
    user = get_user(userid)
    assert user

    item = klass(userid, text, docid, sentenceid)
    session.add(item)
    session.commit()

def save_translation(userid, docid, sentenceid, text):
    save_thing(Translation, userid, docid, sentenceid, text)

def save_comment(userid, docid, sentenceid, text):
    save_thing(Comment, userid, docid, sentenceid, text)

def save_document(title, tags, segments):
    """Given a document title, tags (as a list of strings), all the segments
    (also a list of strings), create a new document and tag it."""
    session = get_session()
    document = Document(title, "bob", "es")
    session.add(document)
    session.commit()
    docid = document.id

    sentences = []
    for (segmentid, s) in segments:
        sent = Sentence(s.strip(), docid)
        sentences.append(sent)
    session.add_all(sentences)
    session.commit()
    for tag in tags:
        tag_document(document, tag)

def lookup_user_by_email(email):
    """Lookup a User by email. Return the model object or None."""
    ## There should never be a PersonaUser that doesn't have an associated User
    ## object...
    session = get_session()
    pu = session.query(PersonaUser).filter(PersonaUser.email == email).first()
    if not pu:
        return None
    user = get_user(pu.userid)
    return user

def create_user_with_email(username, email):
    """Given a username and an email address, create the User and associated
    PersonaUser. Return the User."""

    session = get_session()
    user = lookup_username(username)
    assert user is None
    pu = session.query(PersonaUser).filter(PersonaUser.email == email).first()
    assert pu is None

    ## second one is the fullname, we can replace that later.
    user = User(username, username, "")
    session.add(user)
    session.commit()
    pu = PersonaUser(email, user.id)
    session.add(pu)
    session.commit()
    return user

def tag_document(document, tagname):
    """Given a document object, tag it with the named tag. Optionally create the
    tag if it doesn't exist yet.
    """
    session = get_session()
    tag = session.query(Tag).filter_by(text=tagname).first() 
    if not tag:
        tag = Tag(tagname)
        session.add(tag)
    document.tags.append(tag)
    session.commit()
