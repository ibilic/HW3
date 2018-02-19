## SI 364 - Winter 2018
## HW 3

####################
## Import statements
####################

from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms.validators import Required, Length
from flask_sqlalchemy import SQLAlchemy

############################
# Application configurations
############################
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string from si364'

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:si364@localhost/ibilichw3"
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

##################
### App setup ####
##################
db = SQLAlchemy(app) # For database use


#########################
#########################
######### Everything above this line is important/useful setup,
## not problem-solving.##
#########################
#########################

#########################
##### Set up Models #####
#########################
class Tweet(db.Model):
    __tablename__ = "tweets"
    id = db.Column(db.Integer,primary_key=True)
    text = db.Column(db.String(64), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __repr__(self):
        return '{} (ID: {})'.format(self.text, self.id)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer,primary_key=True)
    user_name = db.Column(db.String(64))
    display_name = db.Column(db.String(124))
    tweets = db.relationship('Tweet',backref='User')

    def __repr__(self):
        return '{} | ID: {}'.format(self.user_name, self.id)

########################
##### Set up Forms #####
########################

class TweetForm(FlaskForm):
    def validate_username(self,field):
        if field.data[0] == '@':
            raise ValidationError('Username cannot start with @ symbol')
    def validate_display_name(self, field):
        if len(field.data.split()) < 2:
            raise ValidationError('Display name must be two words')

    text = StringField("Tweet text (no more that 250 chars):", validators=[Required(),Length(1,280)])
    username = StringField("Twitter username (no @):",validators=[Required(),Length(1,64), validate_username])
    display_name = StringField("Display name (Enter 2 words): ",validators=[Required(), validate_display_name])
    submit = SubmitField()


###################################
##### Routes & view functions #####
###################################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#############
## Main route
#############

@app.route('/', methods=['GET', 'POST'])
def index():
    form = TweetForm()
    num_tweets = len(Tweet.query.all())
    if form.validate_on_submit():
        twt = form.text.data
        usr = form.username.data
        dis = form.display_name.data

        user = User.query.filter_by(user_name=usr).first()
        if not user:
            user = User(user_name=usr, display_name=dis)
            db.session.add(user)
            db.session.commit()

        if Tweet.query.filter_by(text=twt, user_id=user.id).first() != None:
            flash("Tweet by this user already exists")
            return redirect(url_for('see_all_tweets'))

        twt_obj = Tweet(text=twt,user_id=user.id)
        db.session.add(twt_obj)
        db.session.commit()
        flash("Tweet successfully added")
        return redirect(url_for('index'))
    # PROVIDED: If the form did NOT validate / was not submitted
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('index.html',form=form, num_tweets=num_tweets) # TODO 364: Add more arguments to the render_template invocation to send data to index.html

@app.route('/all_tweets')
def see_all_tweets():
    all_tweets = Tweet.query.all()
    tweet_things = [(tw.text, User.query.filter_by(id=tw.user_id).first().user_name) for tw in all_tweets]
    return render_template('all_tweets.html', all_tweets=tweet_things)


@app.route('/all_users')
def see_all_users():
    users = User.query.all()
    return render_template('all_users.html', users=users)

def countTwet(twet):  #sort by length
    return len(twet.text.replace(" ",""))

def twetText(twet):  #sort by alphabetical order
    return twet.text

@app.route('/longest_tweet')
def get_longest_tweet():
    all_tweets = Tweet.query.all()
    sortAlpha = sorted(all_tweets, key = twetText)
    sortNumLen = sorted(sortAlpha, key = countTwet, reverse=True)[0]

    user = User.query.filter_by(id=sortNumLen.user_id).first()
    disname = user.display_name

    tupInfo = (sortNumLen.text, user.user_name, disname)
    return render_template('longest_tweet.html',tupInfo=tupInfo)

if __name__ == '__main__':
    db.create_all() # Will create any defined models when you run the application
    app.run(use_reloader=True,debug=True) # The usual
