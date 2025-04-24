from flask import Flask, render_template,redirect,url_for,request,flash
from model import db,User,Subject,Chapter,Quiz,Question,Score
from flask_login import LoginManager,login_user,logout_user,login_required,current_user
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive Agg
import matplotlib.pyplot as plt
import io
import base64




app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///storage.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False #she stop warning
app.config['SECRET_KEY']= 'taaanu' 


db.init_app(app)


login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form['email']
        password=request.form['password']

        user= User.query.filter_by(email=email).first()

        if user and user.password == password:#before and checks the existence of user and then checks if password is correct
            login_user(user)
            flash('Login Successfull','success')
            
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        
        else:
            flash('Not a user (sign in) or incorrect email/password')
        
    return render_template('login.html')



@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        full_name=request.form['full_name']
        password=request.form['password']
        qualification=request.form['qualification']
        dob=request.form['dob']
        role=request.form['role']

        existing_user= User.query.filter_by(email=email).first()
        if existing_user:
            flash('Your email is already registered, kindly login','info')
            return redirect (url_for('login'))
        else:
            dob_date= datetime.strptime(dob,"%Y-%m-%d")
            new_user= User(username=username,email=email,password=password,full_name=full_name,qualification=qualification,dob=dob_date,role=role)
            db.session.add(new_user)
            db.session.commit()
            flash('you have been registered to our website successfully','success')
            return redirect(url_for('login'))
        
    return render_template('register.html')


@app.route('/user_dashboard',methods=['GET','POST'])
@login_required
def user_dashboard():
    if current_user.is_admin():
        flash('Admins cannot access the user dashboard')
        return redirect(url_for('admin_dashboard'))
    else:
        subjects= Subject.query.all()
        scores=Score.query.filter_by(user_id = current_user.id).all()
        return render_template('user_dashboard.html',User=current_user,subjects=subjects,scores=scores)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('you have been logged out!')
    return redirect(url_for('login'))






#ADMIN ROUTES 

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('you are not allowed to view this page','danger')
        return redirect(url_for('user_dashboard'))
    
    
    return render_template('admin_dashboard.html', admin=current_user)


@app.route('/admin_dashboard/subjects',methods=['GET','POST'])
@login_required
def manage_subjects():
    if not current_user.is_admin():
        flash('you are not allowed to visit this route','danger')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        subject_name= request.form['subject_name']
        description= request.form['description']

        new_subject=Subject(subject_name=subject_name,description=description)
        db.session.add(new_subject)
        db.session.commit()

        flash('Subject added to the database','success')
        return redirect(url_for('manage_subjects'))
    
    subjects= Subject.query.all()
    return render_template('manage_subjects.html',subjects=subjects)


@app.route('/admin_dashboard/subjects/delete <int:subject_id>')
@login_required
def delete_subject(subject_id):
    if not current_user.is_admin():
        flash('You are not allowed to access this page','danger')
        return redirect(url_for('student_dashboard'))
    
    else:
        subject = Subject.query.get(subject_id)
        if subject:
            # First delete all scores related to quizzes in this subject's chapters
            for chapter in subject.chapters:
                for quiz in chapter.quizzes:
                    Score.query.filter_by(quiz_id=quiz.id).delete()
                    Question.query.filter_by(quiz_id=quiz.id).delete()
                    db.session.delete(quiz)
            
            # Then delete all chapters
            Chapter.query.filter_by(subject_id=subject.id).delete()
            
            # Finally delete the subject
            db.session.delete(subject)
            db.session.commit()
            flash('Subject and all related data deleted successfully','success')
            
        return redirect(url_for('manage_subjects'))
    
@app.route('/admin_dashboard/subjects/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    if not current_user.is_admin():
        flash("You are not allowed")
        return redirect(url_for('user_dashboard'))
    else:
        subject = Subject.query.get_or_404(subject_id)

        if request.method == 'POST':
            subject.subject_name = request.form['subject_name']
            subject.description = request.form['description']

            db.session.commit()
            flash('Subject updated')
            return redirect(url_for('manage_subjects'))
        
        return render_template('edit_subject.html', subject=subject)

@app.route('/admin_dashboard/chapters', methods=['GET','POST'])
@login_required
def manage_chapters():
    if not current_user.is_admin():
        flash('You are not allowed to access this page','danger')
        return redirect(url_for('student_dashboard'))
    
    else:
        subjects= Subject.query.all()

        if request.method=='POST':
            name=request.form['name']
            description=request.form['description']
            subject_id=request.form['subject_id']

            new_chapter=Chapter(name=name,description=description,subject_id=subject_id)
            db.session.add(new_chapter)
            db.session.commit()


            flash('Chapter Added','success')
            return redirect(url_for('manage_chapters'))
        
        chapters=Chapter.query.all()
        return render_template('manage_chapters.html',chapters=chapters, subjects=subjects)



@app.route('/admin_dashboard/chapters/edit<int:chapter_id>',methods=['GET','POST'])
@login_required
def edit_chapter(chapter_id):
    if not current_user.is_admin():
        flash("You are not allowed")
        return redirect(url_for('user_dashboard'))
    else:
        chapter= Chapter.query.get_or_404(chapter_id)
        subjects= Subject.query.all()

        if request.method=='POST':
            chapter.name=request.form['name']
            chapter.description=request.form['description']
            chapter.subject_id=request.form['subject_id']

            db.session.commit()
            flash('chapter updated')
            return redirect(url_for('manage_chapters'))
        
        return render_template('edit_chapter.html',chapter=chapter,subjects=subjects)


@app.route('/admin_dashboard/chapters/delete<int:chapter_id>',methods=['GET','POST'])
@login_required
def delete_chapter(chapter_id):
    if not current_user.is_admin():
        flash("Unauthorized action!", "danger")
        return redirect(url_for('user_dashboard'))
    else:
        chapter= Chapter.query.get(chapter_id)
        if chapter:
            for quiz in chapter.quizzes:
                Score.query.filter_by(quiz_id=quiz.id).delete()
                Question.query.filter_by(quiz_id=quiz.id).delete()
                db.session.delete(quiz)
            
            db.session.delete(chapter)
            db.session.commit()

            flash('chapter deleted')
        
        return redirect(url_for('manage_chapters'))

@app.route('/admin_dashboard/quizzes',methods=['GET','POST'])
@login_required
def manage_quizzes():
    if not current_user.is_admin():
        flash("You are not authorised to visit this route",'danger')
        return redirect(url_for('user_dashboard'))
    
    else:
        chapters=Chapter.query.all()
        
        if request.method=='POST':
            name= request.form['name']
            quiz_date=request.form['quiz_date']
            time_duration= request.form['time_duration']
            remarks=request.form['remarks']
            chapter_id=request.form['chapter_id']


            quiz_date=datetime.strptime(quiz_date, "%Y-%m-%d").date()
            new_quiz= Quiz(name=name,quiz_date=quiz_date,time_duration=time_duration,remarks=remarks,chapter_id=chapter_id)
            db.session.add(new_quiz)
            db.session.commit()


            flash(' New Quiz Created','success')
            return redirect(url_for('manage_quizzes'))
        
        quizzes=Quiz.query.all()
        return render_template('manage_quizzes.html', quizzes=quizzes,chapters=chapters)
    

@app.route('/admin_dashboard/quizzes/delete/<int:quiz_id>',methods=['GET','POST'])
@login_required
def delete_quiz(quiz_id):
    if not current_user.is_admin():
        flash('You cant crawl on this route','danger')
        return redirect(url_for('user_dashboard'))
    
    else:
        quiz=Quiz.query.get(quiz_id)
        if quiz:
            # First delete all scores related to this quiz
            Score.query.filter_by(quiz_id=quiz.id).delete()
            
            # Then delete all questions
            Question.query.filter_by(quiz_id=quiz.id).delete()

            # Finally delete the quiz
            db.session.delete(quiz)
            db.session.commit()

            flash('Quiz Deleted','success')
        
        return redirect(url_for('manage_quizzes'))

@app.route('/admin_dashboard/quizzes/edit/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    if not current_user.is_admin():
        flash("You are not authorized to visit this route", 'danger')
        return redirect(url_for('user_dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    chapters = Chapter.query.all()
    
    if request.method == 'POST':
        quiz.name = request.form['name']
        quiz.time_duration = request.form['time_duration']
        quiz.remarks = request.form['remarks']
        quiz.chapter_id = request.form['chapter_id']
        
        if request.form['quiz_date']:
            quiz.quiz_date = datetime.strptime(request.form['quiz_date'], "%Y-%m-%d").date()
        
        db.session.commit()
        flash('Quiz updated successfully', 'success')
        return redirect(url_for('manage_quizzes'))
    
    return render_template('edit_quiz.html', quiz=quiz, chapters=chapters)

@app.route('/admin_dashboard/questions/<int:quiz_id>',methods=['GET','POST'])
@login_required
def manage_questions(quiz_id):
    if not current_user.is_admin():
        flash("You are not authorized to visit this route",'danger')
        return redirect(url_for('user_dashboard'))
    
    else:
        quiz=Quiz.query.get_or_404(quiz_id)

        if request.method=='POST':
            quiz_question= request.form['quiz_question']
            option1=request.form['option1']
            option2=request.form['option2']
            option3=request.form['option3']
            option4=request.form['option4']
            correct_choice=request.form['correct_choice']
            
            # Convert option names to integer values and force integer type
            correct_choice_map = {'option1': 1, 'option2': 2, 'option3': 3, 'option4': 4}
            correct_choice_int = int(correct_choice_map.get(correct_choice, 1))  # Force integer type
            
            # Debug print
            print(f"Saving question with correct choice: {correct_choice_int}, type: {type(correct_choice_int)}")

            new_question=Question(quiz_id=quiz_id,quiz_question=quiz_question,option1=option1,option2=option2,option3=option3,option4=option4,correct_choice=correct_choice_int)

            db.session.add(new_question)
            db.session.commit()

            flash('question added','success')
            return redirect(url_for('manage_questions',quiz_id=quiz_id))
        
        questions=Question.query.filter_by(quiz_id=quiz_id).all()
        return render_template('manage_questions.html',quiz=quiz,questions=questions)
    
@app.route('/admin_dashboard/questions/delete<int:question_id>/<int:quiz_id>',methods=['GET','POST'])
@login_required
def delete_question(question_id,quiz_id):
    if not current_user.is_admin():
        flash("You are not authorized to visit this route",'danger')
        return redirect(url_for('user_dashboard'))
    
    else:
        question=Question.query.get_or_404(question_id)
        if question:
            db.session.delete(question)
            db.session.commit()
            
            flash('Question Deleted','success')
            
        return redirect (url_for('manage_questions',quiz_id=quiz_id))




#END OF ADMIN ROUTES


#USER ROUTES

@app.route('/subject/<int:subject_id>')
@login_required
def view_chapters(subject_id):
    subject=Subject.query.get_or_404(subject_id)
    chapters= Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('view_chapters.html',subject=subject,chapters=chapters)


@app.route('/chapter/<int:chapter_id>')
@login_required
def view_quizzes(chapter_id):
    chapter= Chapter.query.get_or_404(chapter_id)
    quizzes=Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template('view_quizzes.html',chapter=chapter,quizzes=quizzes)

@app.route('/admin_summary')
@login_required
def admin_summary():
    if not current_user.is_admin():
        flash('You are not authorized to view this page', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        # Calculate overall stats
        total_quizzes = Quiz.query.count()
        total_attempts = Score.query.count()
        total_users = User.query.count()
        active_users = db.session.query(Score.user_id).distinct().count()
        
        # Calculate participation rate and overall accuracy
        participation_rate = round((active_users / total_users) * 100, 1) if total_users > 0 else 0
        
        # Overall accuracy calculation
        total_questions_answered = 0
        total_correct_answers = 0
        
        quiz_scores = db.session.query(Score.total_score, Quiz.id).join(Quiz).all()
        for score, quiz_id in quiz_scores:
            question_count = Question.query.filter_by(quiz_id=quiz_id).count()
            total_questions_answered += question_count
            total_correct_answers += score
        
        overall_accuracy = round((total_correct_answers / total_questions_answered) * 100, 1) if total_questions_answered > 0 else 0
        
        # Create overall stats dictionary
        overall_stats = {
            'total_quizzes': total_quizzes,
            'total_attempts': total_attempts,
            'total_users': total_users,
            'active_users': active_users,
            'participation_rate': participation_rate,
            'overall_accuracy': overall_accuracy
        }
        
        # Generate quiz data for table
        quiz_data = []
        quizzes = Quiz.query.all()
        
        for quiz in quizzes:
            question_count = Question.query.filter_by(quiz_id=quiz.id).count()
            scores = Score.query.filter_by(quiz_id=quiz.id).all()
            attempts = len(scores)
            
            if attempts > 0:
                avg_score = sum(score.total_score for score in scores) / attempts
                avg_percentage = (avg_score / question_count) * 100 if question_count > 0 else 0
            else:
                avg_score = 0
                avg_percentage = 0
            
            quiz_data.append({
                'id': quiz.id,
                'name': quiz.name,
                'subject': quiz.chapter.subject.subject_name,
                'chapter': quiz.chapter.name,
                'question_count': question_count,
                'attempts': attempts,
                'avg_score': round(avg_score, 1),
                'avg_percentage': round(avg_percentage, 1)
            })
        
        # Generate participation chart
        plt.figure(figsize=(10, 5))
        quiz_names = [q['name'] for q in quiz_data]
        attempts = [q['attempts'] for q in quiz_data]
        
        plt.bar(quiz_names, attempts, color='#550737')
        plt.title('Quiz Participation')
        plt.xlabel('Quizzes')
        plt.ylabel('Number of Attempts')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        participation_bytes = io.BytesIO()
        plt.savefig(participation_bytes, format='png', bbox_inches='tight')
        participation_bytes.seek(0)
        participation_chart = base64.b64encode(participation_bytes.getvalue()).decode()
        plt.close()
        
        # Generate performance chart
        plt.figure(figsize=(10, 5))
        avg_percentages = [q['avg_percentage'] for q in quiz_data]
        
        plt.bar(quiz_names, avg_percentages, color='#671949')
        plt.title('Quiz Performance')
        plt.xlabel('Quizzes')
        plt.ylabel('Average Score (%)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        performance_bytes = io.BytesIO()
        plt.savefig(performance_bytes, format='png', bbox_inches='tight')
        performance_bytes.seek(0)
        performance_chart = base64.b64encode(performance_bytes.getvalue()).decode()
        plt.close()
        
        # Generate accuracy pie chart
        plt.figure(figsize=(8, 8))
        labels = ['Correct', 'Incorrect']
        sizes = [overall_accuracy, 100 - overall_accuracy]
        colors = ['#8A3C6C', '#BC6E9E']
        
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title('Overall Answer Accuracy')
        
        accuracy_bytes = io.BytesIO()
        plt.savefig(accuracy_bytes, format='png', bbox_inches='tight')
        accuracy_bytes.seek(0)
        accuracy_chart = base64.b64encode(accuracy_bytes.getvalue()).decode()
        plt.close()

        return render_template(
            'admin_summary.html',
            overall_stats=overall_stats,
            quiz_data=quiz_data,
            participation_chart=participation_chart,
            performance_chart=performance_chart,
            accuracy_chart=accuracy_chart
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error generating summary: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/quiz/<int:quiz_id>',methods=['GET','POST'])
@login_required
def take_quiz(quiz_id):
    quiz=Quiz.query.get_or_404(quiz_id)
    questions=Question.query.filter_by(quiz_id=quiz_id).all()

    if request.method== 'POST':
        score=0
        for question in questions:
            selected_option= request.form.get(f'question_{question.id}')
            
            # Make sure we're comparing integers
            if selected_option and int(selected_option) == int(question.correct_choice):
                score+=1
        
        new_score= Score(quiz_id=quiz_id,user_id=current_user.id,total_score=score)
        db.session.add(new_score)
        db.session.commit()

        flash(f'You scored {score}/{len(questions)}!','info')
        return redirect(url_for('user_dashboard'))
    
    return render_template('take_quiz.html',quiz=quiz,questions=questions)

@app.route('/admin/search')
@login_required
def admin_search():
    if not current_user.is_admin():
        flash('You are not allowed to access this page', 'danger')
        return redirect(url_for('user_dashboard'))
    
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('admin_dashboard'))
    
    # Search for users
    users = User.query.filter(
        (User.username.contains(query)) | 
        (User.email.contains(query)) | 
        (User.full_name.contains(query))
    ).all()
    
    # Search for subjects
    subjects = Subject.query.filter(
        (Subject.subject_name.contains(query)) | 
        (Subject.description.contains(query))
    ).all()
    
    # Search for quizzes
    quizzes = Quiz.query.filter(
        (Quiz.name.contains(query)) | 
        (Quiz.remarks.contains(query))
    ).all()
    
    # Search for questions
    questions = Question.query.filter(
        Question.quiz_question.contains(query)
    ).all()
    
    return render_template(
        'admin_search_results.html',
        query=query,
        users=users,
        subjects=subjects,
        quizzes=quizzes,
        questions=questions
    )

@app.route('/user/search')
@login_required
def user_search():
    if current_user.is_admin():
        flash('Admins should use the admin search', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('user_dashboard'))
    
    # Search for subjects
    subjects = Subject.query.filter(
        (Subject.subject_name.contains(query)) | 
        (Subject.description.contains(query))
    ).all()
    
    # Search for quizzes
    quizzes = Quiz.query.filter(
        (Quiz.name.contains(query)) | 
        (Quiz.remarks.contains(query))
    ).all()
    
    return render_template(
        'user_search_results.html',
        query=query,
        subjects=subjects,
        quizzes=quizzes
    )

@app.route('/summary')
@login_required
def summary():
    if current_user.is_admin():
        flash('Admins cannot view personal summaries')
        return redirect(url_for('admin_dashboard'))
    
    try:
        # Check if user has any scores at all
        user_scores = Score.query.filter_by(user_id=current_user.id).all()
        if not user_scores:
            flash('You haven\'t taken any quizzes yet. Complete some quizzes to see your summary!', 'info')
            return redirect(url_for('user_dashboard'))
        
        # Get user's scores grouped by subject
        subject_scores = (
            db.session.query(
                Subject.subject_name,
                db.func.count(Score.id).label('attempts'),
                db.func.avg(Score.total_score).label('average_score')
            )
            .join(Chapter, Subject.id == Chapter.subject_id)
            .join(Quiz, Chapter.id == Quiz.chapter_id)
            .join(Score, Quiz.id == Score.quiz_id)
            .filter(Score.user_id == current_user.id)
            .group_by(Subject.subject_name)
            .all()
        )

        if not subject_scores:
            flash('No quiz attempts found. Take some quizzes to see your summary!', 'info')
            return redirect(url_for('user_dashboard'))

        # Prepare data for plotting
        subjects = [score[0] for score in subject_scores]
        attempts = [score[1] for score in subject_scores]
        averages = [round(float(score[2]), 2) for score in subject_scores]

        # Create bar chart
        plt.figure(figsize=(10, 5))
        plt.bar(subjects, averages, color='#2A1A5E')
        plt.title('Average Scores by Subject')
        plt.xlabel('Subjects')
        plt.ylabel('Average Score')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save bar chart to bytes
        bar_bytes = io.BytesIO()
        plt.savefig(bar_bytes, format='png', bbox_inches='tight', transparent=True)
        bar_bytes.seek(0)
        bar_chart = base64.b64encode(bar_bytes.getvalue()).decode()
        plt.close()     

        # Create pie chart for attempts distribution
        plt.figure(figsize=(8, 8))
        colors = ['#550737', '#671949', '#8A3C6C', '#BC6E9E', '#2A1A5E', '#7E6EB3']
        plt.pie(attempts, labels=subjects, autopct='%1.1f%%', colors=colors)
        plt.title('Quiz Attempts Distribution')
        plt.tight_layout()

        # Save pie chart to bytes
        pie_bytes = io.BytesIO()
        plt.savefig(pie_bytes, format='png', bbox_inches='tight', transparent=True)
        pie_bytes.seek(0)
        pie_chart = base64.b64encode(pie_bytes.getvalue()).decode()
        plt.close()
        
        # Generate detailed quiz data
        quiz_data = []
        for score in user_scores:
            quiz = Quiz.query.get(score.quiz_id)
            question_count = Question.query.filter_by(quiz_id=quiz.id).count()
            percentage = (score.total_score / question_count) * 100 if question_count > 0 else 0
            
            quiz_data.append({
                'quiz_name': quiz.name,
                'subject': quiz.chapter.subject.subject_name,
                'chapter': quiz.chapter.name,
                'score': score.total_score,
                'max_score': question_count,
                'percentage': round(percentage, 1),
                'date': score.timestamp.strftime("%Y-%m-%d %H:%M")
            })
        
        # Calculate overall stats
        total_quizzes = len(user_scores)
        total_questions = sum(q['max_score'] for q in quiz_data)
        total_correct = sum(q['score'] for q in quiz_data)
        accuracy = round((total_correct / total_questions) * 100, 1) if total_questions > 0 else 0
        
        overall_stats = {
            'total_quizzes': total_quizzes,
            'total_questions': total_questions,
            'total_correct': total_correct,
            'accuracy': accuracy
        }

        return render_template(
            'user_summary.html',  # Changed from 'summary.html' to 'user_summary.html'
            bar_chart=bar_chart,  # Changed variable name from bar_graph to bar_chart
            pie_chart=pie_chart,  # Changed variable name from pie_graph to pie_chart
            quiz_data=quiz_data,
            overall_stats=overall_stats
        )

    except Exception as e:
        import traceback
        traceback.print_exc()  # Print the full traceback
        flash(f'Error generating summary: {str(e)}', 'danger')
        return redirect(url_for('user_dashboard'))



with app.app_context():

    db.create_all()

    # new_sub= Subject(id=1,subject_name='maths',description='maths quiz is here')
    # db.session.add(new_sub)
    # db.session.commit()



if __name__=='__main__':
    app.run(debug=True)
