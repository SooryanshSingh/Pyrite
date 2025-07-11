from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
import sys
from io import StringIO
import os
import markdown
from dotenv import load_dotenv

# Firebase Admin
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, firestore


load_dotenv()  # loads .env

firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
}

# Flask App
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")
app.debug = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

# Firebase Init
cred = credentials.Certificate("pyrite-7c9db-firebase-adminsdk-fbsvc-890f30ed61.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ------------------- Helpers -------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('signin'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------- Auth -------------------

@app.route("/session-login", methods=["POST"])
def session_login():
    data = request.get_json()
    id_token = data.get("idToken")
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        session['user'] = {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name", "")
        }
        return jsonify({"message": "Login successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for("homepage"))

@app.route("/signin")
def signin():
    return render_template("signin.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

# ------------------- Pages -------------------



@app.route("/")
def homepage():
    return render_template("homepage.html", firebase_config=firebase_config)



@app.route("/notebook/<notebook_id>/run/")
@login_required
def run_notebook(notebook_id):
    return render_template("code.html", notebook_id=notebook_id)


# ------------------- Notebooks -------------------



@app.route("/notebook/<notebook_id>")
@login_required
def open_notebook(notebook_id):
    return render_template("notebook.html", notebook_id=notebook_id)
@app.route("/notebook/create", methods=["POST"])


@login_required
def create_notebook():
    try:
        data = request.get_json()
        title = data.get("title", "Untitled")
        user_id = session['user']['uid']

        doc_ref = db.collection("notebooks").document()
        doc_ref.set({
            "title": title,
            "user_id": user_id
        })
        return jsonify({"notebook_id": doc_ref.id, "title": title}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/notebooks", methods=["GET"])
@login_required
def get_notebooks():
    try:
        user_id = session['user']['uid']
        notebooks = db.collection("notebooks").where("user_id", "==", user_id).stream()
        result = [{"notebook_id": doc.id, **doc.to_dict()} for doc in notebooks]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/notebook/<notebook_id>/delete", methods=["DELETE"])
@login_required
def delete_notebook(notebook_id):
    try:
        db.collection("notebooks").document(notebook_id).delete()
        return jsonify({"message": "Notebook deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------- Cells -------------------

@app.route("/notebook/<notebook_id>/add_cell/", methods=["POST"])
@login_required
def add_cell(notebook_id):
    try:
        cell_ref = db.collection("notebooks").document(notebook_id).collection("cells").document()
        cell_ref.set({"code": ""})
        return jsonify({"cell_id": cell_ref.id, "code": ""}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/notebook/<notebook_id>/cells/", methods=["GET"])
@login_required
def get_cells(notebook_id):
    try:
        docs = db.collection("notebooks").document(notebook_id).collection("cells").stream()
        cells = [{"cell_id": doc.id, **doc.to_dict()} for doc in docs]
        return jsonify(cells), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/notebook/<notebook_id>/cell/<cell_id>/run/", methods=["POST"])
@login_required
def run_cell_code(notebook_id, cell_id):
    try:
        data = request.get_json()
        code = data.get("code", "")

        db.collection("notebooks").document(notebook_id).collection("cells")\
            .document(cell_id).update({"code": code})

        compile(code, "<string>", "exec")
        old_stdout = sys.stdout
        new_output = sys.stdout = StringIO()
        exec(code, {})
        sys.stdout = old_stdout
        output = new_output.getvalue().strip()

        return jsonify({"output": output or "No output generated."})
    except IndentationError as e:
        return jsonify({"output": f"Indentation error: {str(e)}"}), 400
    except SyntaxError as e:
        return jsonify({"output": f"Syntax error: {str(e)}"}), 400
    except Exception as e:
        sys.stdout = old_stdout
        return jsonify({"output": f"Error: {str(e)}"}), 500

@app.route("/notebook/<notebook_id>/cell/<cell_id>/delete/", methods=["DELETE"])
@login_required
def delete_cell(notebook_id, cell_id):
    try:
        db.collection("notebooks").document(notebook_id).collection("cells").document(cell_id).delete()
        return jsonify({"message": "Cell deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------- Markdown (Markup) -------------------

@app.route("/notebook/<notebook_id>/add_mark", methods=["POST"])
@login_required
def add_mark(notebook_id):
    try:
        cell_ref = db.collection("notebooks").document(notebook_id).collection("markup").document()
        cell_ref.set({"code": ""})
        return jsonify({"cell_id": cell_ref.id, "code": ""}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/notebook/<notebook_id>/mark", methods=["GET"])
@login_required
def get_mark(notebook_id):
    try:
        docs = db.collection("notebooks").document(notebook_id).collection("markup").stream()
        result = [{"cell_id": doc.id, **doc.to_dict()} for doc in docs]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/notebook/<notebook_id>/markup/<cell_id>/run", methods=["POST"])
@login_required
def render_markdown(notebook_id, cell_id):
    try:
        data = request.get_json()
        code = data.get("code", "")
        db.collection("notebooks").document(notebook_id).collection("markup").document(cell_id).update({"code": code})
        html_output = markdown.markdown(code)
        return jsonify({"rendered_html": html_output}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/notebook/<notebook_id>/markup/<cell_id>/delete", methods=["DELETE"])
@login_required
def delete_markup(notebook_id, cell_id):
    try:
        db.collection("notebooks").document(notebook_id).collection("markup").document(cell_id).delete()
        return jsonify({"message": "Markup cell deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------- Start -------------------

if __name__ == "__main__":
    app.run(debug=True)
