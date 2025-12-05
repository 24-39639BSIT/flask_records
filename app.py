from flask import Flask, render_template, redirect, url_for, flash, g
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
import sqlite3
from datetime import datetime
import click

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-change-in-production'
app.config['DATABASE'] = 'records.db'


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    """
    Close database connection when request ends.
    teardown_appcontext: runs after each request, even if error occurred.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """
    Initialize database schema.
    Creates tables if they don't exist.
    """
    db = get_db()
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    db.commit()

@app.cli.command('init-db')
def init_db_command():
    """Initialize the database (run: flask init-db)"""
    init_db()
    print('Database initialized.')

class RecordForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 140)])
    content = TextAreaField('Content', validators=[Length(max=2000)])
    submit = SubmitField('Save Record')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/records')
def list_records():
    db = get_db()
    # Execute SQL query
    records = db.execute(
        'SELECT id, title, content, created_at FROM records ORDER BY created_at DESC'
    ).fetchall()
    return render_template('records_list.html', records=records)

@app.route('/records/new', methods=['GET', 'POST'])
def create_record():
    form = RecordForm()
    
    if form.validate_on_submit():
        db = get_db()
        db.execute(
            'INSERT INTO records (title, content) VALUES (?, ?)',
            (form.title.data, form.content.data)
        )
        db.commit()
        
        flash('Record created successfully!', 'success')
        return redirect(url_for('list_records'))
    
    return render_template('form.html', form=form, action='Create')

@app.route('/records/<int:id>')
def view_record(id):
    """View single record"""
    db = get_db()
    record = db.execute(
        'SELECT id, title, content, created_at FROM records WHERE id = ?',
        (id,)
    ).fetchone()
    
    if record is None:
        flash('Record not found.', 'error')
        return redirect(url_for('list_records'))
    
    return render_template('record_detail.html', record=record)

@app.route('/records/<int:id>/edit', methods=['GET', 'POST'])
def edit_record(id):
    """Edit existing record"""
    db = get_db()
    record = db.execute(
        'SELECT id, title, content FROM records WHERE id = ?',
        (id,)
    ).fetchone()
    
    if record is None:
        flash('Record not found.', 'error')
        return redirect(url_for('list_records'))
    
    form = RecordForm()
    
    if form.validate_on_submit():
        db.execute(
            'UPDATE records SET title = ?, content = ? WHERE id = ?',
            (form.title.data, form.content.data, id)
        )
        db.commit()
        
        flash('Record updated successfully!', 'success')
        return redirect(url_for('view_record', id=id))
    
    if not form.is_submitted():
        form.title.data = record['title']
        form.content.data = record['content']
    
    return render_template('form.html', form=form, action='Edit', record_id=id)

@app.route('/records/<int:id>/delete', methods=['POST'])
def delete_record(id):
    """Delete record (POST only for security)"""
    db = get_db()
    db.execute('DELETE FROM records WHERE id = ?', (id,))
    db.commit()
    
    flash('Record deleted successfully!', 'success')
    return redirect(url_for('list_records'))

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)