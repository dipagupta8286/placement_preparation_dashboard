from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import psycopg2
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)

# Secret key for sessions
app.secret_key = "placement_dashboard_secret_key"


# =========================================================
# RESUME UPLOAD SETTINGS
# =========================================================

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="placement_dashboard",
        user="postgres",
        password="Dip@1812"
    )

    return conn


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

def create_tables():

    conn = get_db_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # STUDENTS TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.students (
            id SERIAL PRIMARY KEY,
            fullname VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(20),
            college VARCHAR(150),
            branch VARCHAR(100),
            semester VARCHAR(20),
            password VARCHAR(255) NOT NULL
        )
    """)

    # -----------------------------------------------------
    # COMPANIES TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.companies (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            company VARCHAR(100) NOT NULL,
            role VARCHAR(100) NOT NULL,
            status VARCHAR(50) NOT NULL
        )
    """)

    # -----------------------------------------------------
    # CODING PROBLEMS TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.coding_problems (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            problem VARCHAR(200) NOT NULL,
            platform VARCHAR(100) NOT NULL,
            difficulty VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL
        )
    """)

    # -----------------------------------------------------
    # REMINDERS TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.reminders (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            title VARCHAR(200) NOT NULL,
            reminder_date DATE NOT NULL,
            status VARCHAR(50) NOT NULL
        )
    """)

    # -----------------------------------------------------
    # ADMINS TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.admins (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    # Default admin account
    cursor.execute("""
        INSERT INTO admins (username, password)
        VALUES (%s, %s)
        ON CONFLICT (username) DO NOTHING
    """, ("admin", "admin123"))

    # -----------------------------------------------------
    # QUIZ SCORES TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.quiz_scores (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            quiz_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        ALTER TABLE public.quiz_scores
        ADD COLUMN IF NOT EXISTS subject VARCHAR(100)
    """)

    cursor.execute("""
        ALTER TABLE public.quiz_scores
        ADD COLUMN IF NOT EXISTS difficulty VARCHAR(20)
    """)
    
    #=========================================================
    #quiz_scores
    #=========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.quiz_questions (
            id SERIAL PRIMARY KEY,
            subject VARCHAR(100) NOT NULL,
            question TEXT NOT NULL,
            option_a VARCHAR(255) NOT NULL,
            option_b VARCHAR(255) NOT NULL,
            option_c VARCHAR(255) NOT NULL,
            option_d VARCHAR(255) NOT NULL,
            correct_answer VARCHAR(1) NOT NULL,
            difficulty VARCHAR(20) NOT NULL
        )
    """)
    
    conn.commit()

    cursor.close()
    conn.close()

def insert_quiz_questions():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM quiz_questions")
    count = cursor.fetchone()[0]

    if count > 0:
        cursor.close()
        conn.close()
        return

    questions = [

        # ================= C PROGRAMMING =================

        ("C Programming", "Which symbol is used to end a statement in C?",
         ";", ":", ".", ",", "A", "Easy"),

        ("C Programming", "Which data type is used to store a single character?",
         "char", "string", "character", "text", "A", "Easy"),

        ("C Programming", "Which loop is guaranteed to execute at least once?",
         "for", "while", "do-while", "if", "C", "Medium"),

        ("C Programming", "What is the index of the first element of an array in C?",
         "0", "1", "-1", "2", "A", "Medium"),

        ("C Programming", "Which concept allows a function to call itself?",
         "Iteration", "Recursion", "Compilation", "Inheritance", "B", "Hard"),


        # ================= C++ =================

        ("C++", "Which feature allows the same function name with different parameters?",
         "Inheritance", "Polymorphism", "Function overloading", "Encapsulation", "C", "Easy"),

        ("C++", "Which keyword is used to create a class?",
         "class", "struct", "object", "define", "A", "Easy"),

        ("C++", "Which concept hides internal implementation details?",
         "Inheritance", "Encapsulation", "Recursion", "Compilation", "B", "Medium"),

        ("C++", "What is a constructor?",
         "A special member function", "A variable", "A loop", "A pointer", "A", "Medium"),

        ("C++", "Which feature allows a derived class to redefine a base class method?",
         "Overloading", "Overriding", "Binding", "Casting", "B", "Hard"),


        # ================= JAVA =================

        ("Java", "Which keyword is used to create an object?",
         "class", "new", "object", "create", "B", "Easy"),

        ("Java", "Which method is the entry point of a Java program?",
         "start()", "run()", "main()", "execute()", "C", "Easy"),

        ("Java", "Which concept allows one class to acquire properties of another?",
         "Encapsulation", "Inheritance", "Abstraction", "Compilation", "B", "Medium"),

        ("Java", "Which keyword prevents a class from being inherited?",
         "static", "private", "final", "protected", "C", "Medium"),

        ("Java", "Which mechanism handles runtime exceptions?",
         "try-catch", "if-else", "switch", "loop", "A", "Hard"),


        # ================= PYTHON =================

        ("Python", "Which symbol is used to create a comment in Python?",
         "#", "//", "/*", "--", "A", "Easy"),

        ("Python", "Which data type stores key-value pairs?",
         "List", "Tuple", "Dictionary", "Set", "C", "Easy"),

        ("Python", "Which keyword defines a function?",
         "function", "def", "fun", "define", "B", "Medium"),

        ("Python", "Which collection cannot be changed after creation?",
         "List", "Dictionary", "Tuple", "Set", "C", "Medium"),

        ("Python", "What is the average time complexity of dictionary lookup?",
         "O(1)", "O(n)", "O(log n)", "O(n²)", "A", "Hard"),


        # ================= JAVASCRIPT =================

        ("JavaScript", "Which keyword declares a block-scoped variable?",
         "var", "let", "define", "variable", "B", "Easy"),

        ("JavaScript", "Which symbol is used for strict equality?",
         "=", "==", "===", "!=", "C", "Easy"),

        ("JavaScript", "Which method adds an element to the end of an array?",
         "push()", "pop()", "shift()", "add()", "A", "Medium"),

        ("JavaScript", "What does DOM stand for?",
         "Document Object Model", "Data Object Model", "Document Oriented Method", "Digital Object Management", "A", "Medium"),

        ("JavaScript", "Which feature allows asynchronous code to be handled more easily?",
         "Promises", "Pointers", "Classes only", "Structs", "A", "Hard"),


        # ================= DBMS / SQL =================

        ("DBMS", "What does DBMS stand for?",
         "Database Management System", "Data Backup Management System", "Database Machine System", "Data Management Service", "A", "Easy"),

        ("DBMS", "Which SQL command is used to retrieve data?",
         "INSERT", "SELECT", "UPDATE", "DELETE", "B", "Easy"),

        ("DBMS", "Which key uniquely identifies a record?",
         "Foreign key", "Primary key", "Candidate key only", "Composite key only", "B", "Medium"),

        ("DBMS", "Which normal form removes partial dependency?",
         "1NF", "2NF", "3NF", "BCNF", "B", "Medium"),

        ("DBMS", "Which SQL clause is used to filter grouped results?",
         "WHERE", "ORDER BY", "HAVING", "GROUP BY", "C", "Hard"),


        # ================= OPERATING SYSTEM =================

        ("Operating Systems", "What is the main purpose of an operating system?",
         "Manage computer resources", "Create websites", "Design hardware", "Write programs automatically", "A", "Easy"),

        ("Operating Systems", "Which scheduling algorithm uses a time quantum?",
         "FCFS", "Round Robin", "SJF", "Priority", "B", "Easy"),

        ("Operating Systems", "What is a process?",
         "A program in execution", "A file", "A compiler", "A device", "A", "Medium"),

        ("Operating Systems", "Which condition is associated with deadlock?",
         "Circular wait", "Compilation", "Inheritance", "Recursion", "A", "Medium"),

        ("Operating Systems", "Which technique allows processes to share memory safely?",
         "Virtual memory", "Process synchronization", "Compilation", "Booting", "B", "Hard"),


        # ================= COMPUTER NETWORKS =================

        ("Computer Networks", "What does IP stand for?",
         "Internet Protocol", "Internal Process", "Internet Program", "Information Protocol", "A", "Easy"),

        ("Computer Networks", "Which device connects different networks?",
         "Switch", "Router", "Hub", "Repeater", "B", "Easy"),

        ("Computer Networks", "Which protocol is used to translate domain names into IP addresses?",
         "HTTP", "DNS", "FTP", "SMTP", "B", "Medium"),

        ("Computer Networks", "Which protocol provides reliable connection-oriented communication?",
         "UDP", "IP", "TCP", "ARP", "C", "Medium"),

        ("Computer Networks", "Which layer is responsible for end-to-end delivery in OSI?",
         "Network", "Transport", "Session", "Physical", "B", "Hard"),


        # ================= TOC =================

        ("TOC", "What does DFA stand for?",
         "Deterministic Finite Automaton", "Dynamic Finite Algorithm", "Data Flow Automaton", "Digital Finite Automaton", "A", "Easy"),

        ("TOC", "Which automaton recognizes regular languages?",
         "Finite Automaton", "Turing Machine only", "Compiler", "Stack", "A", "Easy"),

        ("TOC", "What is an NFA?",
         "Non-deterministic Finite Automaton", "Network Finite Algorithm", "Normal Finite Automaton", "Numeric Finite Automaton", "A", "Medium"),

        ("TOC", "Which machine has an unbounded tape?",
         "DFA", "NFA", "Turing Machine", "PDA", "C", "Medium"),

        ("TOC", "Which lemma is commonly used to prove that a language is not regular?",
         "Bayes Lemma", "Pumping Lemma", "Euclid Lemma", "Memory Lemma", "B", "Hard"),


        # ================= DAA =================

        ("DAA", "What does algorithm complexity measure?",
         "Resource requirements", "Program color", "Screen size", "Keyboard speed", "A", "Easy"),

        ("DAA", "What is the time complexity of binary search?",
         "O(n)", "O(log n)", "O(n²)", "O(1)", "B", "Easy"),

        ("DAA", "Which sorting algorithm uses divide and conquer?",
         "Bubble Sort", "Merge Sort", "Selection Sort", "Insertion Sort", "B", "Medium"),

        ("DAA", "What is the worst-case time complexity of quicksort?",
         "O(log n)", "O(n)", "O(n²)", "O(1)", "C", "Medium"),

        ("DAA", "Which technique solves problems by storing results of overlapping subproblems?",
         "Greedy", "Dynamic Programming", "Backtracking only", "Brute Force", "B", "Hard"),


        # ================= SOFTWARE ENGINEERING =================

        ("Software Engineering", "What is SDLC?",
         "Software Development Life Cycle", "System Design Logic Code", "Software Data Life Cycle", "System Development Language Code", "A", "Easy"),

        ("Software Engineering", "Which model follows a sequential development process?",
         "Waterfall", "Agile", "Spiral only", "Prototype only", "A", "Easy"),

        ("Software Engineering", "What is a software requirement?",
         "A needed system capability", "A programming language", "A database table", "A hardware device", "A", "Medium"),

        ("Software Engineering", "Which model emphasizes iterative development?",
         "Waterfall", "Agile", "Big Bang", "V-Model only", "B", "Medium"),

        ("Software Engineering", "Which activity identifies and manages project risks?",
         "Risk management", "Coding", "Compilation", "Debugging only", "A", "Hard"),


        # ================= SOFTWARE TESTING =================

        ("Software Testing", "What is software testing?",
         "Evaluating software for defects", "Writing only code", "Installing hardware", "Designing networks", "A", "Easy"),

        ("Software Testing", "Which testing checks individual units?",
         "System testing", "Unit testing", "Acceptance testing", "Regression testing", "B", "Easy"),

        ("Software Testing", "What is regression testing?",
         "Testing after changes to ensure existing functionality still works", "Testing only hardware", "Testing network speed", "Writing requirements", "A", "Medium"),

        ("Software Testing", "What is black-box testing?",
         "Testing without knowing internal implementation", "Testing source code only", "Testing hardware", "Testing databases only", "A", "Medium"),

        ("Software Testing", "Which testing verifies the complete integrated system?",
         "Unit testing", "System testing", "Component testing", "Syntax testing", "B", "Hard"),


        # ================= CYBERSECURITY =================

        ("Cybersecurity", "What does CIA stand for in information security?",
         "Confidentiality, Integrity, Availability", "Control, Internet, Access", "Code, Identity, Authentication", "Confidentiality, Internet, Authorization", "A", "Easy"),

        ("Cybersecurity", "What is phishing?",
         "A social engineering attack", "A sorting technique", "A database operation", "A network cable", "A", "Easy"),

        ("Cybersecurity", "What is encryption?",
         "Converting readable data into protected form", "Deleting data", "Compressing files only", "Creating hardware", "A", "Medium"),

        ("Cybersecurity", "What is multi-factor authentication?",
         "Using multiple verification factors", "Using multiple passwords only", "Using multiple computers", "Using multiple networks", "A", "Medium"),

        ("Cybersecurity", "Which attack attempts to make a service unavailable by overwhelming it?",
         "Phishing", "DDoS", "SQL query", "Sniffing only", "B", "Hard"),


        # ================= OOP =================

        ("OOP", "What does OOP stand for?",
         "Object-Oriented Programming", "Object Operating Process", "Open Object Programming", "Operational Object Process", "A", "Easy"),

        ("OOP", "Which concept hides data inside a class?",
         "Encapsulation", "Inheritance", "Polymorphism", "Compilation", "A", "Easy"),

        ("OOP", "Which concept allows one interface to have multiple implementations?",
         "Polymorphism", "Compilation", "Iteration", "Recursion", "A", "Medium"),

        ("OOP", "Which concept allows a class to derive properties from another class?",
         "Inheritance", "Encapsulation", "Abstraction", "Overloading", "A", "Medium"),

        ("OOP", "What is abstraction?",
         "Showing essential details while hiding unnecessary implementation", "Copying a class", "Deleting objects", "Creating loops", "A", "Hard"),


        # ================= DATA STRUCTURES =================

        ("Data Structures", "Which data structure follows LIFO?",
         "Queue", "Stack", "Array", "Tree", "B", "Easy"),

        ("Data Structures", "Which data structure follows FIFO?",
         "Stack", "Queue", "Tree", "Graph", "B", "Easy"),

        ("Data Structures", "Which data structure is commonly used for BFS?",
         "Stack", "Queue", "Heap only", "Array only", "B", "Medium"),

        ("Data Structures", "What is the average search complexity in a balanced binary search tree?",
         "O(1)", "O(log n)", "O(n²)", "O(n)", "B", "Medium"),

        ("Data Structures", "Which data structure is commonly used to implement priority queues?",
         "Heap", "Stack", "Queue only", "Linked List only", "A", "Hard")
    ]

    for q in questions:

        cursor.execute("""
            INSERT INTO quiz_questions
            (
                subject,
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_answer,
                difficulty
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, q)

    conn.commit()

    cursor.close()
    conn.close()
# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        college = request.form["college"]
        branch = request.form["branch"]
        semester = request.form["semester"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO students
                (
                    fullname,
                    email,
                    phone,
                    college,
                    branch,
                    semester,
                    password
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                fullname,
                email,
                phone,
                college,
                branch,
                semester,
                password
            ))

            conn.commit()

        except psycopg2.errors.UniqueViolation:

            conn.rollback()

            cursor.close()
            conn.close()

            return "Email already registered. Please use another email."

        cursor.close()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, fullname, email, password
            FROM students
            WHERE email = %s
        """, (email,))

        student = cursor.fetchone()

        cursor.close()
        conn.close()

        if student and student[3] == password:

            session["student_id"] = student[0]
            session["fullname"] = student[1]
            session["email"] = student[2]

            return redirect(url_for("dashboard"))

        return "Invalid email or password."

    return render_template("login.html")


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    student_id = session["student_id"]

    # =====================================================
    # TOTAL COMPANIES
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM companies
        WHERE student_id = %s
    """, (student_id,))

    total_companies = cursor.fetchone()[0]

    # =====================================================
    # TOTAL CODING PROBLEMS
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM coding_problems
        WHERE student_id = %s
    """, (student_id,))

    total_coding = cursor.fetchone()[0]

    # =====================================================
    # TOTAL REMINDERS
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM reminders
        WHERE student_id = %s
    """, (student_id,))

    total_reminders = cursor.fetchone()[0]

    # =====================================================
    # LATEST QUIZ
    # =====================================================

    cursor.execute("""
        SELECT score, total_questions
        FROM quiz_scores
        WHERE student_id = %s
        ORDER BY quiz_date DESC
        LIMIT 1
    """, (student_id,))

    quiz_result = cursor.fetchone()

    if quiz_result:

        latest_quiz_score = (
            f"{quiz_result[0]}/{quiz_result[1]}"
        )

    else:

        latest_quiz_score = "Not Attempted"

    # =====================================================
    # RECENT COMPANY
    # =====================================================

    cursor.execute("""
        SELECT company, role, status
        FROM companies
        WHERE student_id = %s
        ORDER BY id DESC
        LIMIT 1
    """, (student_id,))

    recent_company = cursor.fetchone()

    # =====================================================
    # RECENT CODING PROBLEM
    # =====================================================

    cursor.execute("""
        SELECT problem, platform, difficulty, status
        FROM coding_problems
        WHERE student_id = %s
        ORDER BY id DESC
        LIMIT 1
    """, (student_id,))

    recent_coding = cursor.fetchone()

    # =====================================================
    # UPCOMING REMINDER
    # =====================================================

    cursor.execute("""
        SELECT title, reminder_date, status
        FROM reminders
        WHERE student_id = %s
        ORDER BY reminder_date ASC
        LIMIT 1
    """, (student_id,))

    upcoming_reminder = cursor.fetchone()

    # =====================================================
    # LATEST QUIZ ACTIVITY
    # =====================================================

    cursor.execute("""
        SELECT score, total_questions, quiz_date
        FROM quiz_scores
        WHERE student_id = %s
        ORDER BY quiz_date DESC
        LIMIT 1
    """, (student_id,))

    recent_quiz = cursor.fetchone()

    # RESUME STATUS
    files = os.listdir(app.config["UPLOAD_FOLDER"])

    resume_uploaded = False

    for filename in files:
        if filename.startswith(str(student_id) + "_"):
            resume_uploaded = True
            break

    # =====================================================
    # OVERALL PROGRESS
    # =====================================================

    progress = 0

    if total_companies > 0:
        progress += 25

    if total_coding > 0:
        progress += 25

    if quiz_result:
        progress += 25

    if total_reminders > 0:
        progress += 25

    # =====================================================
    # CLOSE DATABASE
    # =====================================================

    cursor.close()
    conn.close()

    # =====================================================
    # SEND DATA TO DASHBOARD
    # =====================================================

    return render_template(
        "dashboard.html",

        total_companies=total_companies,

        total_coding=total_coding,

        total_reminders=total_reminders,

        latest_quiz_score=latest_quiz_score,

        progress=progress,

        recent_company=recent_company,

        recent_coding=recent_coding,

        upcoming_reminder=upcoming_reminder,

        recent_quiz=recent_quiz,
        
        resume_uploaded=resume_uploaded
    )

# =========================================================
# COMPANY TRACKER
# =========================================================

@app.route("/companies", methods=["GET", "POST"])
def companies():

    if "student_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # ADD COMPANY
    # -----------------------------------------------------

    if request.method == "POST":

        company = request.form["company"]
        role = request.form["role"]
        status = request.form["status"]

        cursor.execute("""
            INSERT INTO companies
            (
                student_id,
                company,
                role,
                status
            )
            VALUES (%s, %s, %s, %s)
        """, (
            session["student_id"],
            company,
            role,
            status
        ))

        conn.commit()

    # -----------------------------------------------------
    # GET COMPANIES
    # -----------------------------------------------------

    cursor.execute("""
        SELECT id, company, role, status
        FROM companies
        WHERE student_id = %s
        ORDER BY id DESC
    """, (session["student_id"],))

    company_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "companies.html",
        companies=company_list
    )


# =========================================================
# DELETE COMPANY
# =========================================================

@app.route("/delete-company/<int:company_id>", methods=["POST"])
def delete_company(company_id):

    if "student_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM companies
        WHERE id = %s
        AND student_id = %s
    """, (
        company_id,
        session["student_id"]
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("companies"))

# =========================================================
# EDIT COMPANY STATUS
# =========================================================

@app.route("/edit-company/<int:company_id>", methods=["GET", "POST"])
def edit_company(company_id):

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        company = request.form["company"]
        role = request.form["role"]
        status = request.form["status"]

        cursor.execute("""
            UPDATE companies
            SET company = %s,
                role = %s,
                status = %s
            WHERE id = %s
            AND student_id = %s
        """, (
            company,
            role,
            status,
            company_id,
            session["student_id"]
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("companies"))

    cursor.execute("""
        SELECT id, company, role, status
        FROM companies
        WHERE id = %s
        AND student_id = %s
    """, (
        company_id,
        session["student_id"]
    ))

    company_data = cursor.fetchone()

    cursor.close()
    conn.close()

    if not company_data:
        return "Company not found."

    return render_template(
        "edit_company.html",
        company=company_data
    )

# =========================================================
# CODING TRACKER
# =========================================================

@app.route("/coding-tracker", methods=["GET", "POST"])
def coding_tracker():

    if "student_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # ADD CODING PROBLEM
    # -----------------------------------------------------

    if request.method == "POST":

        problem = request.form["problem"]
        platform = request.form["platform"]
        difficulty = request.form["difficulty"]
        status = request.form["status"]

        cursor.execute("""
            INSERT INTO coding_problems
            (
                student_id,
                problem,
                platform,
                difficulty,
                status
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            session["student_id"],
            problem,
            platform,
            difficulty,
            status
        ))

        conn.commit()

    # -----------------------------------------------------
    # GET CODING PROBLEMS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT id, problem, platform, difficulty, status
        FROM coding_problems
        WHERE student_id = %s
        ORDER BY id DESC
    """, (session["student_id"],))

    problems = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "coding_tracker.html",
        problems=problems
    )


# =========================================================
# DELETE CODING PROBLEM
# =========================================================

@app.route("/delete-coding/<int:problem_id>", methods=["POST"])
def delete_coding(problem_id):

    if "student_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM coding_problems
        WHERE id = %s
        AND student_id = %s
    """, (
        problem_id,
        session["student_id"]
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("coding_tracker"))

# =========================================================
# EDIT CODING PROBLEM
# =========================================================

@app.route("/edit-coding/<int:problem_id>", methods=["GET", "POST"])
def edit_coding(problem_id):

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        problem = request.form["problem"]
        platform = request.form["platform"]
        difficulty = request.form["difficulty"]
        status = request.form["status"]

        cursor.execute("""
            UPDATE coding_problems
            SET problem = %s,
                platform = %s,
                difficulty = %s,
                status = %s
            WHERE id = %s
            AND student_id = %s
        """, (
            problem,
            platform,
            difficulty,
            status,
            problem_id,
            session["student_id"]
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("coding_tracker"))

    cursor.execute("""
        SELECT id, problem, platform, difficulty, status
        FROM coding_problems
        WHERE id = %s
        AND student_id = %s
    """, (
        problem_id,
        session["student_id"]
    ))

    problem_data = cursor.fetchone()

    cursor.close()
    conn.close()

    if not problem_data:
        return "Coding problem not found."

    return render_template(
        "edit_coding.html",
        problem=problem_data
    )
# =========================================================
# APTITUDE QUIZ
# =========================================================

@app.route("/quiz", methods=["GET", "POST"])
def quiz():

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # GET SUBJECTS
    cursor.execute("""
        SELECT DISTINCT subject
        FROM quiz_questions
        ORDER BY subject
    """)

    subjects = [row[0] for row in cursor.fetchall()]

    # START QUIZ
    if request.method == "POST":

        subject = request.form["subject"]
        difficulty = request.form["difficulty"]

        if subject == "All":
            if difficulty == "All":
                cursor.execute("""
                    SELECT id, subject, question,
                           option_a, option_b,
                           option_c, option_d,
                           correct_answer
                    FROM quiz_questions
                    ORDER BY RANDOM()
                    LIMIT 10
                """)
            else:
                cursor.execute("""
                    SELECT id, subject, question,
                           option_a, option_b,
                           option_c, option_d,
                           correct_answer
                    FROM quiz_questions
                    WHERE difficulty = %s
                    ORDER BY RANDOM()
                    LIMIT 10
                """, (difficulty,))

        else:
            if difficulty == "All":
                cursor.execute("""
                    SELECT id, subject, question,
                           option_a, option_b,
                           option_c, option_d,
                           correct_answer
                    FROM quiz_questions
                    WHERE subject = %s
                    ORDER BY RANDOM()
                    LIMIT 5
                """, (subject,))
            else:
                cursor.execute("""
                    SELECT id, subject, question,
                           option_a, option_b,
                           option_c, option_d,
                           correct_answer
                    FROM quiz_questions
                    WHERE subject = %s
                    AND difficulty = %s
                    ORDER BY RANDOM()
                    LIMIT 5
                """, (subject, difficulty))

        questions = cursor.fetchall()

        cursor.close()
        conn.close()

        if not questions:
            return "No questions available for this selection."

        return render_template(
            "quiz.html",
            questions=questions,
            quiz_started=True,
            subject=subject,
            difficulty=difficulty
        )

    cursor.close()
    conn.close()

    return render_template(
        "quiz.html",
        subjects=subjects,
        quiz_started=False
    )

@app.route("/quiz-submit", methods=["POST"])
def quiz_submit():

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    score = 0
    total_questions = 0

    for key, answer in request.form.items():

        if key.startswith("q"):

            question_id = key[1:]

            cursor.execute("""
                SELECT correct_answer
                FROM quiz_questions
                WHERE id = %s
            """, (question_id,))

            result = cursor.fetchone()

            if result:

                total_questions += 1

                if answer == result[0]:
                    score += 1

    # SAVE RESULT
    subject = request.form.get("subject", "All")
    difficulty = request.form.get("difficulty", "All")

    cursor.execute("""
        INSERT INTO quiz_scores
        (student_id, score, total_questions, subject, difficulty)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        session["student_id"],
        score,
        total_questions,
        subject,
        difficulty
    ))
    conn.commit()

    cursor.close()
    conn.close()

    percentage = 0

    if total_questions > 0:
        percentage = round(
            (score / total_questions) * 100
        )

    return render_template(
        "quiz_result.html",
        score=score,
        total_questions=total_questions,
        percentage=percentage
    )

# =========================================================
# QUIZ HISTORY
# =========================================================

@app.route("/quiz-history")
def quiz_history():

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT score,
               total_questions,
               quiz_date,
               subject,
               difficulty
        FROM quiz_scores
        WHERE student_id = %s
        ORDER BY quiz_date DESC
    """, (session["student_id"],))

    history = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "quiz_history.html",
        history=history
    )

# =========================================================
# RESUME
# =========================================================

@app.route("/resume", methods=["GET", "POST"])
def resume():

    if "student_id" not in session:
        return redirect(url_for("login"))

    message = ""

    if request.method == "POST":

        if "resume" not in request.files:
            message = "No file selected."

        else:
            file = request.files["resume"]

            if file.filename == "":
                message = "No file selected."

            elif not allowed_file(file.filename):
                message = "Invalid file type. Only PDF, DOC and DOCX are allowed."

            else:
                filename = secure_filename(file.filename)

                student_id = session["student_id"]

                # Add student ID to filename
                filename = str(student_id) + "_" + filename

                file.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        filename
                    )
                )

                message = "Resume uploaded successfully."

    return render_template(
        "resume.html",
        message=message
    )
@app.route("/download-resume")
def download_resume():

    if "student_id" not in session:
        return redirect(url_for("login"))

    student_id = str(session["student_id"])

    upload_folder = app.config["UPLOAD_FOLDER"]

    files = os.listdir(upload_folder)

    for filename in files:

        if filename.startswith(student_id + "_"):

            file_path = os.path.join(upload_folder, filename)

            return send_from_directory(
                upload_folder,
                filename,
                as_attachment=True
            )

    return "Resume not found."
    # -----------------------------------------------------
    # ADD REMINDER
    # -----------------------------------------------------

    if request.method == "POST":

        title = request.form["title"]
        reminder_date = request.form["reminder_date"]
        status = request.form["status"]

        cursor.execute("""
            INSERT INTO reminders
            (
                student_id,
                title,
                reminder_date,
                status
            )
            VALUES (%s, %s, %s, %s)
        """, (
            session["student_id"],
            title,
            reminder_date,
            status
        ))

        conn.commit()

    # -----------------------------------------------------
    # GET REMINDERS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            title,
            reminder_date,
            status
        FROM reminders
        WHERE student_id = %s
        ORDER BY reminder_date ASC
    """, (session["student_id"],))

    reminder_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "reminders.html",
        reminders=reminder_list
    )

@app.route("/reminders", methods=["GET", "POST"])
def reminders():

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        title = request.form["title"]
        reminder_date = request.form["reminder_date"]
        status = request.form["status"]

        cursor.execute("""
            INSERT INTO reminders
            (student_id, title, reminder_date, status)
            VALUES (%s, %s, %s, %s)
        """, (
            session["student_id"],
            title,
            reminder_date,
            status
        ))

        conn.commit()

    cursor.execute("""
        SELECT id, title, reminder_date, status
        FROM reminders
        WHERE student_id = %s
        ORDER BY reminder_date ASC
    """, (session["student_id"],))

    reminder_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "reminders.html",
        reminders=reminder_list
    )

# =========================================================
# DELETE REMINDER
# =========================================================

@app.route("/delete-reminder/<int:reminder_id>", methods=["POST"])
def delete_reminder(reminder_id):

    if "student_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM reminders
        WHERE id = %s
        AND student_id = %s
    """, (
        reminder_id,
        session["student_id"]
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("reminders"))
#==========================================================
#EDIT_REMINDER
#=========================================================
@app.route("/edit-reminder/<int:reminder_id>", methods=["GET", "POST"])
def edit_reminder(reminder_id):

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        title = request.form["title"]
        reminder_date = request.form["reminder_date"]
        status = request.form["status"]

        cursor.execute("""
            UPDATE reminders
            SET title = %s,
                reminder_date = %s,
                status = %s
            WHERE id = %s
            AND student_id = %s
        """, (
            title,
            reminder_date,
            status,
            reminder_id,
            session["student_id"]
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("reminders"))

    cursor.execute("""
        SELECT id, title, reminder_date, status
        FROM reminders
        WHERE id = %s
        AND student_id = %s
    """, (
        reminder_id,
        session["student_id"]
    ))

    reminder_data = cursor.fetchone()

    cursor.close()
    conn.close()

    if not reminder_data:
        return "Reminder not found."

    return render_template(
        "edit_reminder.html",
        reminder=reminder_data
    )

# =========================================================
# PROFILE
# =========================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    student_id = session["student_id"]

    if request.method == "POST":

        fullname = request.form["fullname"]
        phone = request.form["phone"]
        college = request.form["college"]
        branch = request.form["branch"]
        semester = request.form["semester"]

        cursor.execute("""
            UPDATE students
            SET fullname = %s,
                phone = %s,
                college = %s,
                branch = %s,
                semester = %s
            WHERE id = %s
        """, (
            fullname,
            phone,
            college,
            branch,
            semester,
            student_id
        ))

        conn.commit()

    cursor.execute("""
        SELECT id, fullname, email, phone, college, branch, semester
        FROM students
        WHERE id = %s
    """, (student_id,))

    student = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "profile.html",
        student=student
    )

# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                username,
                password
            FROM admins
            WHERE username = %s
        """, (username,))

        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin and admin[2] == password:

            session["admin_id"] = admin[0]
            session["admin_username"] = admin[1]

            return redirect(
                url_for("admin_dashboard")
            )

        return "Invalid admin username or password."

    return render_template("admin_login.html")


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # ---------------- STUDENT DATA ----------------

    cursor.execute("""
        SELECT id, fullname, email, phone, college, branch, semester
        FROM students
        ORDER BY id DESC
    """)
    student_list = cursor.fetchall()

    # ---------------- GENERAL STATISTICS ----------------

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM companies")
    total_companies = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM coding_problems")
    total_coding = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reminders")
    total_reminders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM quiz_scores")
    total_quizzes = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(ROUND(AVG(score), 2), 0)
        FROM quiz_scores
    """)
    average_quiz_score = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(MAX(score), 0)
        FROM quiz_scores
    """)
    highest_quiz_score = cursor.fetchone()[0]

    # ---------------- CODING STATISTICS ----------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM coding_problems
        WHERE LOWER(status) = 'solved'
    """)
    solved_coding = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM coding_problems
        WHERE LOWER(status) = 'pending'
    """)
    pending_coding = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM coding_problems
        WHERE LOWER(difficulty) = 'easy'
    """)
    easy_coding = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM coding_problems
        WHERE LOWER(difficulty) = 'medium'
    """)
    medium_coding = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM coding_problems
        WHERE LOWER(difficulty) = 'hard'
    """)
    hard_coding = cursor.fetchone()[0]

    # ---------------- TOP CODING STUDENTS ----------------

    cursor.execute("""
        SELECT
            students.fullname,
            COUNT(coding_problems.id) AS solved_count
        FROM students
        JOIN coding_problems
        ON students.id = coding_problems.student_id
        WHERE LOWER(coding_problems.status) = 'solved'
        GROUP BY students.id, students.fullname
        ORDER BY solved_count DESC
        LIMIT 5
    """)
    top_coding_students = cursor.fetchall()

    # ---------------- PLATFORM USAGE ----------------

    cursor.execute("""
        SELECT platform, COUNT(*)
        FROM coding_problems
        GROUP BY platform
        ORDER BY COUNT(*) DESC
    """)
    platform_usage = cursor.fetchall()

    # ---------------- RECENT CODING ACTIVITY ----------------

    cursor.execute("""
        SELECT
            students.fullname,
            coding_problems.problem,
            coding_problems.platform,
            coding_problems.difficulty,
            coding_problems.status
        FROM coding_problems
        JOIN students
        ON students.id = coding_problems.student_id
        ORDER BY coding_problems.id DESC
        LIMIT 5
    """)
    recent_coding_activity = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin.html",

        # General statistics
        students=student_list,
        total_students=total_students,
        total_companies=total_companies,
        total_coding=total_coding,
        total_reminders=total_reminders,
        total_quizzes=total_quizzes,
        average_quiz_score=average_quiz_score,
        highest_quiz_score=highest_quiz_score,

        # Coding statistics
        solved_coding=solved_coding,
        pending_coding=pending_coding,
        easy_coding=easy_coding,
        medium_coding=medium_coding,
        hard_coding=hard_coding,

        # Coding details
        top_coding_students=top_coding_students,
        platform_usage=platform_usage,
        recent_coding_activity=recent_coding_activity
    )

# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# CREATE TABLES AND START APPLICATION
# =========================================================

create_tables()
insert_quiz_questions()

@app.route("/analytics")
def analytics():

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    student_id = session["student_id"]

    # Overall quiz statistics
    cursor.execute("""
        SELECT
            COUNT(*),
            COALESCE(ROUND(AVG(score), 2), 0),
            COALESCE(MAX(score), 0)
        FROM quiz_scores
        WHERE student_id = %s
    """, (student_id,))

    overall = cursor.fetchone()

    # Subject-wise performance
    cursor.execute("""
        SELECT
            subject,
            COUNT(*) AS attempts,
            ROUND(
                AVG(
                    CASE
                        WHEN total_questions > 0
                        THEN (score::decimal / total_questions) * 100
                        ELSE 0
                    END
                ), 2
            ) AS percentage
        FROM quiz_scores
        WHERE student_id = %s
        AND subject IS NOT NULL
        GROUP BY subject
        ORDER BY percentage DESC
    """, (student_id,))

    subject_performance = cursor.fetchall()
    # Find subjects that need more practice
    weak_subjects = [
        subject for subject in subject_performance
        if subject[2] < 60
    ]

    cursor.close()
    conn.close()

    return render_template(
        "analytics.html",
        overall=overall,
        subject_performance=subject_performance,
        weak_subjects=weak_subjects
    )

if __name__ == "__main__":

    app.run(debug=True)