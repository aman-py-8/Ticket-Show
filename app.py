from flask import Flask, render_template, request, redirect, Response, flash,  url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import LargeBinary, func
from datetime import datetime
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ticket.db'
db = SQLAlchemy(app)
app.app_context().push()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password
        
class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    v_name = db.Column(db.String(100), nullable=False)
    v_place = db.Column(db.Text, nullable=False)
    v_cap = db.Column(db.Integer, nullable=False, default='N/A')
    shows = db.relationship('Show', backref='venue', cascade='all, delete-orphan')

class Show(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    showprice = db.Column(db.Integer, nullable=False, default='N/A')
    date_added = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    ratings = db.Column(db.Integer)
    poster = db.Column(db.LargeBinary, nullable=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=True)
    tags = db.relationship('Tag', secondary='show_tags', backref='show')


    
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

class show_tags(db.Model):
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)

class bookings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    show_id = db.Column(db.Integer, nullable=True)
    num_seats = db.Column(db.Integer)
    showtime = db.Column(db.String(50), nullable=True)
    booking_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)



db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        
        
        if user:
            return redirect('/success')
        else:
            message = "Incorrect username or password or User not registered"
    return render_template('index.html', message = message)
    
@app.route('/success')
def success():
    all_shows = Show.query.all()
    return render_template('success.html', shows = all_shows)
    
@app.route('/search')
def search():
    query = request.args.get('search')
    results = Show.query.filter(Show.title.ilike(f'%{query}%')).all()
    return render_template('search_results.html', results=results)
    
@app.route('/showtitle/<int:id>')
def show_title(id):
    show = Show.query.get(id)
    if show:
        return Response(show.title, content_type='text')
    else:
        return "Show not found", 404

@app.route('/book/<int:show_id>', methods=['GET', 'POST'])
def book_ticket(show_id):
    show = Show.query.get_or_404(show_id)
    all_ven = Venue.query.all()
    max_seats = show.venue.v_cap
    booking = db.session.query(func.sum(bookings.num_seats)).filter_by(show_id=show_id).scalar()
    if booking:
        available_seats = show.venue.v_cap - booking
        if booking >= max_seats:
            all_shows = Show.query.all()
            message = "The Show You're Trying To Book Is Housefull"
            return render_template('success.html', message = message, shows = all_shows)
    else:
        available_seats = max_seats
    if request.method == 'POST':
        show_id = request.form.get('show_id')
        num_seat = request.form['num_tick']
        name = request.form['name']
        showtime = request.form['showtime']
        new_booking = bookings(show_id=show_id,num_seats=num_seat, name=name, showtime=showtime)
        db.session.add(new_booking)
        db.session.flush()
        new_tick_id = new_booking.id
        db.session.commit()
        show = Show.query.get(show_id)
        return render_template('Ticket.html', tick_id=new_tick_id, booking=new_booking,show=show)
    return render_template('book_ticket.html', show=show, venue=all_ven, available_seats=available_seats)

           
@app.route('/venue', methods=['GET', 'POST'])
    
def add_ven():

    if request.method == 'POST':
        venue_name = request.form['venue']
        venue_place = request.form['Place']
        venue_capacity = request.form['Capacity']
        new_venue = Venue(v_name=venue_name, v_place=venue_place, v_cap=venue_capacity)
        db.session.add(new_venue)
        db.session.commit()
        return redirect('/venue')
    else:
        all_venue = Venue.query.all()
        return render_template('venue.html', venues=all_venue)

@app.route('/venue/delete_ven/<int:id>')
def delete_ven(id):
    venue = Venue.query.get_or_404(id)
    db.session.delete(venue)
    db.session.commit()
    return redirect('/venue')
    
@app.route('/venue/edit_ven/<int:id>', methods=['GET', 'POST'])
def edit_ven(id):
    venue = Venue.query.get_or_404(id)
    if request.method == 'POST':
        venue.v_name = request.form['venue']
        venue.v_place = request.form['Place']
        venue.v_cap = request.form['Capacity']
        db.session.commit()
        return redirect('/venue')
    else:
        return render_template('edit_ven.html', venue=venue)

@app.route('/show', methods=['GET', 'POST'])
def add_show():

    if request.method == 'POST':
        show_name = request.form['show']
        s_price = request.form['price']
        rating = request.form['Rating']
        tag = request.form['movtag']
        venue_id = request.form['Venue_sel']
        image = request.files["image"]
        image_data = image.read() 

        new_show = Show(showprice=s_price, title=show_name, ratings=rating, venue_id = venue_id, poster=image_data)
        new_tag = Tag(name=tag)  
        image_data = image.read()    
        db.session.add(new_tag)
        db.session.add(new_show)
        db.session.flush()
        
        new_show_tag = show_tags(show_id=new_show.id, tag_id=new_tag.id)
        db.session.add(new_show_tag)
        db.session.commit()
        return redirect('/show')
    else:
        all_show = Show.query.all()
        all_venue = Venue.query.all()
        return render_template('show.html', shows=all_show, venues=all_venue)
        
@app.route('/showposter/<int:id>')
def show_poster(id):
    show = Show.query.get(id)
    if show:
        return Response(show.poster, content_type='image/jpeg')
    else:
        return "Show not found", 404

@app.route('/show/delete_show/<int:id>')
def delete_show(id):
    show = Show.query.get_or_404(id)
    db.session.delete(show)
    db.session.commit()
    return redirect('/show')
        
@app.route('/show/edit_show/<int:id>', methods=['GET', 'POST'])
def edit_show(id):
    show = Show.query.get_or_404(id)
    if request.method == 'POST':
        show.title = request.form['show']
        show.showprice = request.form['price']
        show.ratings = request.form['Rating']
        
        db.session.commit()
        return redirect('/show')
    else:
        return render_template('edit_show.html', show=show)


@app.route('/register', methods=['GET', 'POST'])
def Register():
    message = ""
    if request.method == 'POST':
        Username = request.form['username']
        Password = request.form['password']
        existing_user = User.query.filter_by(username=Username).first()
        if not existing_user:
            new_user = User(username=Username, password=Password)
            db.session.add(new_user)
            db.session.commit()
            return redirect('/')
        else:
            message="User already exist, Choose different username"
            
    return render_template('Register.html', message=message)
    
        
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    return render_template('adminlogin.html')
    
@app.route('/aflogin', methods=['GET', 'POST'])
def aflogin():
    return render_template('aflogin.html')
    
@app.route('/venue', methods=['GET', 'POST'])
def venue():
    return render_template('venue.html')
@app.route('/show', methods=['GET', 'POST'])
def show():
    return render_template('show.html')

if __name__ == "__main__":
    app.run(debug=True)
