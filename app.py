from flask import Flask, request, redirect, make_response, render_template, g, session
import sqlite3
from datetime import datetime, timedelta
import random
import re
import requests
from bs4 import BeautifulSoup
from web_scrapper import backmarket,afbshop,ebay


app = Flask(__name__)
app.secret_key = "detoutesuiteduncompacteonpeutextraireunesuitequiconverge"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)


#
#------------- début blog ------------------
#


def insert_html(page, insertion, marker, keep_marker):
    index = page.find(marker)
    page = page[:index] + str(insertion) + (page[index + len(marker):] if not keep_marker else page[index:])
    return page


def add_sidebar(page, connection, req):
    sidebar = open("templates/sidebartemplate.html", "r", encoding="UTF-8").read()

    # Add login buttons to sidebar
    login_token = req.cookies.get("token")
    if login_token is None:
        name = None
    else:
        name = list(connection.execute(f"SELECT name FROM users WHERE token = {login_token}"))[0][0]

    if name is not None:
        buttons = f"""<div class='loggedinas'>
            <span>Logged in as<br><b>{name}</b></span>
            <a href='/logout'>Log out</a>
        </div>"""
    else:
        buttons = f"""<div class='loggedinas'>
                    <a href='/login'><b>Log in</b></a>
                    <a href='/signup'><b>Sign up</b></a>
                </div>"""

    sidebar = insert_html(sidebar, buttons, "<!-- loggedinas -->", False)

    # Actually insert sidebar into page
    page = insert_html(page, sidebar, "<!-- barre latérale gauche -->", False)

    return page


def make_post(post):
    post_html = open("templates/blog/posttemplate.html", "r", encoding="UTF-8").read()

    # Replace every comment from the template by the value from the database
    check_list = list(post.keys())
    ready = False
    while not ready:
        check = f"<!-- {check_list[0]} -->"
        index = post_html.find(check)
        if index == -1:
            check_list.pop(0)
        else:
            post_html = insert_html(post_html, post[check_list[0]], check, False)
        ready = not check_list

    # Add the star notation
    star_template = "<img src='/static/blog/assets/file.png' alt='star'>"
    stars_html = "".join(
        [insert_html(star_template, "star" if i + 1 <= post["grade"] else "empty_star", "file", False)
         for i in range(5)]
    )
    post_html = insert_html(post_html, stars_html, "<!-- star notation here -->", False)

    # Add the replies button if needed
    if post["repliescount"] >= 1:
        post_html = insert_html(post_html, "replies_button", "<!-- replies button class -->", False)
    else:
        post_html = insert_html(post_html, "hidden", "<!-- replies button class -->", False)

    return post_html


def make_reply(reply):
    reply_html = open("templates/blog/replytemplate.html", "r", encoding="UTF-8").read()

    # Replace every comment from the template by the value from the database
    check_list = list(reply.keys())
    ready = False
    while not ready:
        check = f"<!-- {check_list[0]} -->"
        index = reply_html.find(check)
        if index == -1:
            check_list.pop(0)
        else:
            reply_html = insert_html(reply_html, reply[check_list[0]], check, False)
        ready = not check_list

    return reply_html


def make_report(report, reptype):
    if reptype == "post":
        report_html = open("templates/blog/postreporttemplate.html", "r", encoding="UTF-8").read()
    else:
        report_html = open("templates/blog/replyreporttemplate.html", "r", encoding="UTF-8").read()

    # Replace every comment from the template by the value from the database
    check_list = list(report.keys())
    ready = False
    while not ready:
        check = f"<!-- {check_list[0]} -->"
        index = report_html.find(check)
        if index == -1:
            check_list.pop(0)
        else:
            report_html = insert_html(report_html, report[check_list[0]], check, False)
        ready = not check_list

    if reptype == "post":
        # Add the star notation
        star_template = "<img src='/static/blog/assets/file.png' alt='star'>"
        stars_html = "".join(
            [insert_html(star_template, "star" if i + 1 <= report["grade"] else "empty_star", "file", False)
             for i in range(5)]
        )
        report_html = insert_html(report_html, stars_html, "<!-- star notation here -->", False)

        # Add the replies button if needed
        if report["repliescount"] >= 1:
            report_html = insert_html(report_html, "replies_button", "<!-- replies button class -->", False)
        else:
            report_html = insert_html(report_html, "hidden", "<!-- replies button class -->", False)
    else:
        # Replace every comment from the template by the value from the database
        check_list = list(report.keys())
        ready = False
        while not ready:
            check = f"<!-- {check_list[0]} -->"
            index = report_html.find(check)
            if index == -1:
                check_list.pop(0)
            else:
                report_html = insert_html(report_html, report[check_list[0]], check, False)
            ready = not check_list

        # Add the replies button
        report_html = insert_html(report_html, "thread_button", "<!-- replies button class -->", False)

    return report_html


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        connection = sqlite3.connect("OPtimise.db")

        page = open("templates/login/signup.html", "r", encoding="UTF-8").read()

        # Add sidebar
        page = add_sidebar(page, connection, request)

        # Update error message
        args = dict(request.args)
        if "errmsg" in args.keys():
            page = insert_html(page, f"<h4 class='error'>{args['errmsg']}</h4>",
                               "<!-- errmsg -->", False)

        connection.close()
        return page
    else:
        connection = sqlite3.connect("OPtimise.db")

        form = dict(request.form)

        password_check = form["password1"] == form["password2"]
        fill_check = not any([not val for val in form.values()])
        len_check = not any([len(form["name"]) > 20, len(form["password1"]) > 50])
        name_check = re.compile(f"[a-zA-Z0-9_]{{{len(form['name'])}}}").match(form['name']) is not None

        if password_check and fill_check and len_check and name_check:
            try:
                user_id = random.randint(0, 99999999999)
                date = int(datetime.timestamp(datetime.now()))

                connection.execute(
                    f"INSERT INTO users "
                    f"VALUES ({user_id}, NULL, {date}, '{form['name']}', '{form['password1']}', NULL)"
                )
                connection.commit()
                connection.close()
                return redirect("/login")
            except:
                error_message = "Désolé, ce nom est déjà pris par un autre utilisateur !"
        elif not fill_check:
            error_message = "Veuillez remplir tous les champs."
        elif not password_check:
            error_message = "Vos mots de passe ne correspondent pas."
        elif not name_check:
            error_message = "Un nom ne peut contenir que les caractères a-z, A-Z, 0-9 et \"_\" !"
        else:
            error_message = "Les noms sont limités à 20 caractères et les mots de passe à 50 caractères."

        connection.close()
        return redirect(f"/signup?errmsg={error_message}")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        connection = sqlite3.connect("OPtimise.db")

        page = open("templates/login/login.html", "r", encoding="UTF-8").read()

        # Add sidebar
        page = add_sidebar(page, connection, request)

        # Update error message
        args = dict(request.args)
        if "errmsg" in args.keys():
            page = insert_html(page, f"<h4 class='error'>{args['errmsg']}</h4>",
                               "<!-- errmsg -->", False)

        connection.close()
        return page

    else:
        connection = sqlite3.connect("OPtimise.db")

        form = dict(request.form)

        error_message = None

        user = list(connection.execute(f"SELECT * FROM users WHERE name = '{form['name']}'"))

        fill_check = not any([not val for val in form.values()])
        if not user:
            error_message = f"Pas d'utilisateur connu sous le nom '{form['name']}'."
        elif not fill_check:
            error_message = "Veuillez remplir tous les champs."
        else:
            password_check = form["password"] == user[0][4]
            if not password_check:
                error_message = "Le nom d'utilisateur et le mot de passe ne correspondent pas."

        if error_message is not None:
            connection.close()
            return redirect(f"/login?errmsg={error_message}")
        else:
            resp = make_response(redirect("/menu"))

            token = random.randint(0, 10**15 - 1)

            connection.execute(f"UPDATE users SET token = {token} WHERE name = '{form['name']}'")
            resp.set_cookie(key="token", value=str(token))

            connection.commit()
            connection.close()
            return resp


@app.route("/logout", methods=["GET"])
def logout():
    resp = make_response(redirect("/menu"))

    resp.delete_cookie("token")

    return resp


@app.route("/blog", methods=["GET", "POST"])
def blogroot():
    if request.method == "GET":
        connection = sqlite3.connect('OPtimise.db')

        posts = list(connection.execute("SELECT * FROM posts ORDER BY date DESC LIMIT 10"))
        columns = ["postid", "author", "date", "product", "firm", "grade", "content"]

        page = open("templates/blog/blog.html", "r", encoding="UTF-8").read()

        # Add sidebar
        page = add_sidebar(page, connection, request)

        # Update banhammer button's class
        login_token = request.cookies.get("token")
        if login_token is None:
            rights = None
        else:
            rights = list(connection.execute(f"SELECT rights FROM users WHERE token = {login_token}"))[0][0]
        if rights == "admin":
            page = insert_html(page, "banhammer", "<!-- banhammer button class -->", False)
        else:
            page = insert_html(page, "hidden", "<!-- banhammer button class -->", False)

        # Render system message
        if "sysmsg" in request.args:
            page = insert_html(page, f"<p class='sysmsg'>{request.args['sysmsg']}</p>",
                               "<!-- sysmsg -->", False)

        # Render posts
        for post in posts:
            post = {columns[i]: post[i] for i in range(len(post))}

            post["date"] = datetime.utcfromtimestamp(post["date"] + 60 * 60 * 1).strftime('%d/%m/%Y %H:%M:%S')
            post["author"] = list(connection.execute(f"SELECT name FROM users WHERE user_id = {post['author']}"))[0][0]
            post["repliescount"] = list(connection.execute(
                f"SELECT COUNT(*) FROM replies WHERE postid = {post['postid']}"))[0][0]

            page = insert_html(page, make_post(post), "<!-- posts here -->", True)

        connection.close()
        return page
    else:
        connection = sqlite3.connect('OPtimise.db')

        form = dict(request.form)
        action = form["action"]
        actionsplit = action.split("-")
        acttype = actionsplit[0]
        postid = actionsplit[1]
        if len(actionsplit) >= 3:
            replyid = actionsplit[2]
        else:
            replyid = None

        login_token = request.cookies.get("token")
        if login_token is None:
            rights = None
            user_id = None
        else:
            rights = list(connection.execute(f"SELECT rights FROM users WHERE token = {login_token}"))[0][0]
            user_id = list(connection.execute(f"SELECT user_id FROM users WHERE token = {login_token}"))[0][0]

        if user_id is None:
            connection.close()
            return redirect(f"/blog?sysmsg=Vous+devez+être+connecté+pour+effectuer+cette+action.")

        if acttype.startswith("reply_"):
            authorid = list(connection.execute(
                f"SELECT authorid FROM replies WHERE replyid = {replyid} AND postid = {postid}"))[0][0]
        else:
            authorid = list(connection.execute(f"SELECT authorid FROM posts WHERE postid = {postid}"))[0][0]
        user_id, authorid = int(user_id), int(authorid)

        if acttype == "reply":
            connection.close()
            return redirect(f"/blog/thread/{postid}#add_reply")
        elif acttype == "report":
            reportid = random.randint(0, 99999999999)
            connection.execute(f"INSERT INTO reports VALUES ({reportid}, {user_id}, {postid}, NULL)")
            connection.commit()
            connection.close()
            return redirect(f"/blog?sysmsg=Signalement+envoyé+avec+succès.+Merci+pour+le+coup+de+main+!")
        elif acttype == "delete":
            if user_id == authorid or rights == "admin":
                connection.execute(f"DELETE FROM posts WHERE postid = {postid}")
                connection.commit()
                connection.close()
                return redirect(f"/blog?sysmsg=Votre+post+a+été+supprimé+avec+succès+!")
            else:
                connection.close()
                return redirect(f"/blog?sysmsg=Vous+n'avez+pas+la+permission+de+supprimer+ce+post.")
        elif acttype == "reply_report":
            reportid = random.randint(0, 99999999999)
            connection.execute(f"INSERT INTO reports VALUES ({reportid}, {user_id}, {postid}, {replyid})")
            connection.commit()
            connection.close()
            return redirect(f"/blog/thread/{postid}"
                            f"?sysmsg=Signalement+envoyé+avec+succès.+Merci+pour+le+coup+de+main+!")
        elif acttype == "reply_delete":
            if user_id == authorid or rights == "admin":
                connection.execute(f"DELETE FROM replies WHERE replyid = {replyid}")
                connection.commit()
                connection.close()
                return redirect(f"/blog/thread/{postid}?sysmsg=Votre+commentaire+a+été+supprimé+avec+succès+!")
            else:
                connection.close()
                return redirect(f"/blog/thread/{postid}"
                                f"?sysmsg=Vous+n'avez+pas+la+permission+de+supprimer+ce+commentaire.")
        elif acttype == "report_ignore":
            if rights == "admin":
                connection.execute(f"DELETE FROM reports WHERE postid = {postid} AND replyid IS NULL")
                connection.commit()
                connection.close()
                return redirect(f"/blog/moderate")
            else:
                connection.close()
                return redirect(f"/blog")
        elif acttype == "report_delete":
            if rights == "admin":
                connection.execute(f"DELETE FROM posts WHERE postid = {postid}")
                connection.execute(f"DELETE FROM reports WHERE postid = {postid}")
                connection.commit()
                connection.close()
                return redirect(f"/blog/moderate")
            else:
                connection.close()
                return redirect(f"/blog")
        elif acttype == "report_reply_ignore":
            if rights == "admin":
                connection.execute(f"DELETE FROM reports WHERE replyid = {replyid}")
                connection.commit()
                connection.close()
                return redirect(f"/blog/moderate")
            else:
                connection.close()
                return redirect(f"/blog")
        elif acttype == "report_reply_delete":
            if rights == "admin":
                connection.execute(f"DELETE FROM replies WHERE replyid = {replyid}")
                connection.execute(f"DELETE FROM reports WHERE replyid = {replyid}")
                connection.commit()
                connection.close()
                return redirect(f"/blog/moderate")
            else:
                connection.close()
                return redirect(f"/blog")


@app.route("/blog/thread/<int:postid>", methods=["GET", "POST"])
def thread(postid: int):
    if request.method == "GET":
        connection = sqlite3.connect("OPtimise.db")

        post = list(connection.execute(f"SELECT * FROM posts WHERE postid = {postid}"))[0]
        post_columns = ["postid", "author", "date", "product", "firm", "grade", "content"]
        replies = list(connection.execute(f"SELECT * FROM replies WHERE postid = {postid} ORDER BY date"))
        reply_columns = ["replyid", "postid", "author", "date", "content"]

        page = open("templates/blog/thread.html", "r", encoding="UTF-8").read()

        # Add sidebar
        page = add_sidebar(page, connection, request)

        # Update title
        page = insert_html(page, post[3], "<!-- product -->", False)
        page = insert_html(page, post[4], "<!-- firm -->", False)

        # Update optional system message
        if "sysmsg" in request.args:
            page = insert_html(page, f"<p class='sysmsg'>{request.args['sysmsg']}</p>",
                               "<!-- sysmsg -->", False)

        # Render post
        post = {post_columns[i]: post[i] for i in range(len(post))}

        post["date"] = datetime.utcfromtimestamp(post["date"] + 60 * 60 * 1).strftime('%d/%m/%Y %H:%M:%S')
        post["author"] = list(connection.execute(f"SELECT name FROM users WHERE user_id = {post['author']}"))[0][0]
        post["repliescount"] = 0

        page = insert_html(page, make_post(post), "<!-- post here -->", False)

        # Render replies
        for reply in replies:
            reply = {reply_columns[i]: reply[i] for i in range(len(reply))}

            reply["date"] = datetime.utcfromtimestamp(reply["date"] + 60 * 60 * 1).strftime('%d/%m/%Y %H:%M:%S')
            reply["author"] = list(connection.execute(
                f"SELECT name FROM users WHERE user_id = {reply['author']}"))[0][0]

            page = insert_html(page, make_reply(reply), "<!-- replies here -->", True)

        # Update form action
        page = insert_html(page, postid, "<!-- postid -->", False)

        connection.close()
        return page
    else:
        connection = sqlite3.connect("OPtimise.db")

        replyid = random.randint(0, 99999999999)
        login_token = request.cookies.get("token")
        authorid = list(connection.execute(f"SELECT user_id FROM users WHERE token = {login_token}"))[0][0]
        date = int(datetime.timestamp(datetime.now()))
        content = request.form["content"]

        connection.execute(f"INSERT INTO replies (replyid, postid, authorid, date, content) VALUES "
                           f"(?, ?, ?, ?, ?)", (replyid, postid, authorid, date, content))
        connection.commit()

        connection.close()
        return redirect(f"/blog/thread/{postid}")


@app.route("/blog/write", methods=["GET", "POST"])
def write():
    if request.method == "GET":
        connection = sqlite3.connect("OPtimise.db")

        page = open("templates/blog/blogwrite.html", "r", encoding="UTF-8").read()

        # Add sidebar
        page = add_sidebar(page, connection, request)

        connection.close()
        return page
    else:
        connection = sqlite3.connect("OPtimise.db")

        postid = random.randint(0, 99999999999)
        login_token = request.cookies.get("token")
        authorid = list(connection.execute(f"SELECT user_id FROM users WHERE token = {login_token}"))[0][0]
        date = int(datetime.timestamp(datetime.now()))
        product, firm, grade, content = (request.form["product"], request.form["firm"],
                                         request.form["grade"], request.form["content"])

        connection.execute(f"INSERT INTO posts (postid, authorid, date, product, firm, grade, content) VALUES "
                           f"(?, ?, ?, ?, ?, ?, ?)", (postid, authorid, date, product, firm, grade, content))
        connection.commit()

        connection.close()
        return redirect("/blog?sysmsg=Votre+post+a+bien+été+publié+!")


@app.route("/blog/moderate", methods=["GET"])
def moderate():
    connection = sqlite3.connect("OPtimise.db")

    login_token = request.cookies.get("token")
    user_id, rights = list(connection.execute(f"SELECT user_id, rights FROM users WHERE token = {login_token}"))[0]

    if not rights == "admin":
        return redirect("/blog?sysmsg=Vous+n'êtes+pas+un+administrateur.")

    if request.method == "GET":
        # Delete reports that are associated with a post/reply that doesn't exist anymore
        connection.execute("DELETE FROM reports WHERE postid NOT IN (SELECT p.postid FROM posts p)")
        connection.execute("DELETE FROM reports WHERE replyid NOT IN (SELECT r.replyid FROM replies r)")
        connection.commit()

        # Fetch a list of all reports
        # Requête SQL de la mort qui tue
        reports = list(connection.execute("""SELECT *
                                             FROM 
                                             (
                                             SELECT
                                             r.reportid, r.authorid AS reporterid, r.postid, r.replyid,
                                             p.authorid, p.date, p.product, p.firm, p.grade, p.content,
                                             u.name AS reporter,
                                             u2.name AS author
                                             FROM
                                             (((SELECT * FROM reports r WHERE r.replyid IS NULL) r
                                             JOIN posts p
                                             ON p.postid = r.postid)
                                             JOIN users u
                                             ON r.authorid = u.user_id)
                                             JOIN users u2
                                             ON p.authorid = u2.user_id
                                             )
                                             
                                             UNION
                                             
                                             SELECT 
                                             r.reportid, r.authorid AS reporterid, r.postid, r.replyid,
                                             ry.authorid, ry.date, NULL, NULL, NULL, ry.content,
                                             u.name AS reporter,
                                             u2.name AS author
                                             FROM
                                             (
                                             (((SELECT * FROM reports r WHERE r.replyid IS NOT NULL) r
                                             JOIN replies ry
                                             ON ry.replyid = r.replyid)
                                             JOIN users u
                                             ON r.authorid = u.user_id)
                                             JOIN users u2
                                             ON ry.authorid = u2.user_id
                                             )
                                             """))

        page = open("templates/blog/blogsec.html", "r", encoding="UTF-8").read()

        # Add sidebar
        page = add_sidebar(page, connection, request)

        # Update top message
        page = insert_html(page, "<p>Voici la liste des messages signalés par la communauté.</p>",
                           "<!-- msg -->", False)

        if not reports:
            page = insert_html(page, "<p>Il semblerait que vous ayez rétabli l'odre dans le royaume de "
                                     "l'obsolescence programmée !", "<!-- posts here -->", True)

        for report in reports:
            (reportid, reporterid, postid, replyid, authorid,
             date, product, firm, grade, content, reporter, author) = report

            reptype = "post" if replyid is None else "reply"
            columns = ["reportid", "reporterid", "postid", "replyid", "authorid", "date",
                       "product", "firm", "grade", "content", "reporter", "author"]

            if reptype == "post":
                report = {columns[i]: report[i] for i in range(len(report))}

                report["date"] = datetime.utcfromtimestamp(report["date"] + 60 * 60 * 1).strftime('%d/%m/%Y %H:%M:%S')
                report["repliescount"] = list(connection.execute(
                    f"SELECT COUNT(*) FROM replies WHERE postid = {report['postid']}"))[0][0]

                page = insert_html(page, make_report(report, reptype), "<!-- posts here -->", True)
            else:
                report = {columns[i]: report[i] for i in range(len(report))}

                report["date"] = datetime.utcfromtimestamp(report["date"] + 60 * 60 * 1).strftime('%d/%m/%Y %H:%M:%S')
                report["repliescount"] = list(connection.execute(
                    f"SELECT COUNT(*) FROM replies WHERE postid = {report['postid']}"))[0][0]

                page = insert_html(page, make_report(report, reptype), "<!-- posts here -->", True)

        connection.close()
        return page


@app.route("/blog/search", methods=["GET", "POST"])
def search_post():
    if request.method == "GET":
        connection = sqlite3.connect("OPtimise.db")

        args = dict(request.args)
        q = args["q"]
        qs = q.replace("'", "''")

        # Fetch posts
        posts = list(connection.execute(
            f"SELECT * FROM posts "
            f"WHERE product LIKE '%{qs}%' "
            f"OR firm LIKE '%{qs}%' "
            f"OR content LIKE '%{qs}%'"
        ))
        columns = ["postid", "author", "date", "product", "firm", "grade", "content"]

        page = open("templates/blog/blogsec.html", "r", encoding="UTF-8").read()

        # Add sidebar
        page = add_sidebar(page, connection, request)

        # Update top message
        page = insert_html(page, f"<p>{len(posts)} résultats sont associés à la recherche '{q}'.</p>",
                           "<!-- msg -->", False)

        # Render posts
        for post in posts:
            post = {columns[i]: post[i] for i in range(len(post))}

            post["date"] = datetime.utcfromtimestamp(post["date"] + 60 * 60 * 1).strftime('%d/%m/%Y %H:%M:%S')
            post["author"] = list(connection.execute(f"SELECT name FROM users WHERE user_id = {post['author']}"))[0][0]
            post["repliescount"] = list(connection.execute(
                f"SELECT COUNT(*) FROM replies WHERE postid = {post['postid']}"))[0][0]

            page = insert_html(page, make_post(post), "<!-- posts here -->", True)

        connection.close()
        return page

    else:
        form = dict(request.form)

        return redirect(f"/blog/search?q={form['search_query']}")


#
#------------- fin blog ------------------
#

#
#------------- début classement ------------------
#
databasecl = sqlite3.connect('OPtimise.db', check_same_thread=False)
cursorcl = databasecl.cursor()

def fullsortbygradeENT(notes,entreprises,produits):
    #tri a bulles sur les notes
    for k in range (len(notes)):
        for j in range (len(notes)-k-1):
            if notes[j] < notes[j+1]:
                #afin que les notes, les entreprises et le produits conservent le même indice les 3 sont changés en même temps
                notes[j],notes[j+1] = notes[j+1],notes[j]
                entreprises[j],entreprises[j+1] = entreprises[j+1],entreprises[j]
                produits[j],produits[j+1] = produits[j+1],produits[j]
    return notes, entreprises, produits

@app.route('/classement/entreprise')
def displayE():
    connection = sqlite3.connect("OPtimise.db")
    login_token = request.cookies.get("token")
    if login_token is None:
        name = None
    else:
        name = list(connection.execute(f"SELECT name FROM users WHERE token = {login_token}"))[0][0]
    connection.close()
    #récuperation de la liste des entreprises
    entreprises = cursorcl.execute("SELECT DISTINCT firm FROM posts").fetchall()
    #création d'une liste auxiliaire pour les entreprises afin qu'elles soient exploitables (car par defaut sous forme de tuple)
    entreprisesaux = []
    for k in entreprises:
        entreprisesaux.append(k[0])
    #récuperation de la liste des produits proposés par chaque entreprise
    produitsAUT = []
    for k in entreprises:
        produitsAUT.append(cursorcl.execute("SELECT firm,postid FROM posts WHERE firm = \"{}\"".format(k[0])).fetchall())
    #création d'une liste auxiliaire exploitable pour les produits
    produits = []
    for k in entreprisesaux:
        prodaux1 = (cursorcl.execute("SELECT DISTINCT product FROM posts WHERE firm = \"{}\"".format(k)).fetchall())
        prodaux2 = []
        for j in prodaux1:
            prodaux2.append(j[0])
        produits.append(prodaux2)
    #récuperation des notes moyennes de chaque entreprises
    notes = []
    for k in range(len(entreprises)):
        for j in produitsAUT[k]:
            dataaux = cursorcl.execute("SELECT grade FROM posts WHERE postid = {} and firm = \"{}\"".format(j[1],entreprisesaux[k])).fetchall()
        gradeaux = 0
        for j in dataaux:
            gradeaux += j[0]
        greadeaux = gradeaux/len(dataaux)
        notes.append(gradeaux)
    #tri des entreprises et de leurs produits par rapport aux notes
    notes, entreprisesaux, produits = fullsortbygradeENT(notes,entreprisesaux,produits)
    #création d'une liste d'entiers qui représente le nombre de produits proposés par chaque E (utilisé pour le template HTML)
    len2 = []
    for k in produits:
        len2.append(len(k))
    #affichage de la page a partir du template
    return render_template("classement/classementENT.html",entreprisesaux = entreprisesaux,produits = produits,notes = notes,len1 = len(entreprisesaux),len2 = len2,name=name)


@app.route('/classement/produit')
def displayP():
    connection = sqlite3.connect("OPtimise.db")
    login_token = request.cookies.get("token")
    if login_token is None:
        name = None
    else:
        name = list(connection.execute(f"SELECT name FROM users WHERE token = {login_token}"))[0][0]
    connection.close()
    dataaux = cursorcl.execute("SELECT DISTINCT product,firm FROM posts").fetchall()
    entreprises = []
    produits = []
    for k in dataaux:
        produits.append(k[0])
        entreprises.append(k[1])
    notes =[]
    for k in produits:
        noteraw = cursorcl.execute("SELECT grade FROM posts WHERE product = \"{}\"".format(str(k))).fetchall()
        gradeaux = 0
        for j in noteraw:
            gradeaux += j[0]
        greadeaux = gradeaux/len(dataaux)
        notes.append(gradeaux)
    #tri des entreprises et de leurs produits par rapport aux notes
    notes, entreprises, produits = fullsortbygradeENT(notes,entreprises,produits)
    
    #boucle sur les produits pour avoir les notes 1 par 1 puis somme avec boucle
    return render_template("classement/classementPROD.html",entreprises = entreprises,produits = produits,notes = notes,len1 = len(produits),name=name)

#
#------------- fin classement ------------------
#

#
#------------- début quiz ------------------
#
# Ouvre une connection vers la bd.
def get_db(): 
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("quiz_db.db")
    return db

# Ferme la connection à la bd.
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()



# Page d'introduction du site.
@app.route("/quiz/", methods=("GET", "POST"))
def quiz() :
    connection = sqlite3.connect("OPtimise.db")
    login_token = request.cookies.get("token")
    if login_token is None:
        name = None
    else:
        name = list(connection.execute(f"SELECT name FROM users WHERE token = {login_token}"))[0][0]
    connection.close()
    # Initialise la session
    session["inserted"] = False
    session["question_max"] = 0
    session["question_n"] = 0
    session["question_justes"] = 0
    session["question_ids"] = []

    # Affichage en cas de session expirée sur une autre page.
    if session.get("failed") :
        session["failed"] = False
        return "<script type=\"text/javascript\"> window.alert(\"Session couldn't be started or expired !\"); </script>" + render_template("quiz/quiz.html",name=name)

    # Si POST, récupère le nombre de questions.
    if request.method == 'POST' :
        session["question_max"] = int(request.form.get('question_max'))

        # Récupère la liste des questions.
        c = get_db().cursor()
        c.execute("SELECT id_question FROM questions")
        res = c.fetchall()
        close_connection(None)

        # Mélange la liste des id_questions.
        questions = []
        random.shuffle(res)
        for i in range(0, min(session["question_max"], len(res))) :
            questions.append(res[i][0])
        session["question_ids"] = questions

    # Rend la page.
        return redirect("/quiz/question")
    return render_template("quiz/quiz.html",name=name)
    


# Page de questions du quiz.
@app.route("/quiz/question", methods=("GET", "POST"))
def question() :
    connection = sqlite3.connect("OPtimise.db")
    login_token = request.cookies.get("token")
    if login_token is None:
        name = None
    else:
        name = list(connection.execute(f"SELECT name FROM users WHERE token = {login_token}"))[0][0]
    connection.close()
    # Redirection en cas de session expirée.
    if session.get("question_max") == None or session.get("question_max") == 0  :
        session["failed"] = True
        return redirect("/quiz")

    # Récupère la question.
    c = get_db().cursor()
    c.execute("SELECT * FROM `questions` WHERE `id_question` = " + str(session["question_ids"][0]))
    question = c.fetchall()[0]
    c.execute("SELECT `nom_theme`, `color` FROM `themes` WHERE `id_theme` = " + str(question[6]))
    theme = c.fetchall()[0]
    close_connection(None)

    # Récupère les réponses.
    if request.method == "POST" :
        check1 = (request.form.get("check1") != None)
        check2 = (request.form.get("check2") != None)
        check3 = (request.form.get("check3") != None)

        # Vérifie la validité de la réponse.
        if check1 and question[5] == 0 : session["question_justes"] += 1
        if check2 and question[5] == 1 : session["question_justes"] += 1
        if check3 and question[5] == 2 : session["question_justes"] += 1

        # Passe à la question suivante.
        session["question_ids"].pop(0)
        session["question_n"] += 1

        # Passe à la fin du quiz.
        if len(session["question_ids"]) == 0 :
            return redirect("/quiz/resultat")
        return redirect("/quiz/question")

    # Affiche la page.
    elif request.method == "GET" :
        return render_template("quiz/quiz_question.html", session=session, question=question, theme=theme,name=name)



# Page de resultats du quiz.
@app.route("/quiz/resultat")
def resultat() :
    connection = sqlite3.connect("OPtimise.db")
    login_token = request.cookies.get("token")
    if login_token is None:
        name = None
    else:
        name = list(connection.execute(f"SELECT name FROM users WHERE token = {login_token}"))[0][0]
    connection.close()
    # Redirection en cas de session expirée.
    if session.get("question_max") == None or session.get("question_max") == 0  :
        session["failed"] = True
        return redirect("/quiz")
    
    # Insère la réponse dans la base de donnée.
    if (session.get("inserted") == False) :
        c = get_db()
        c.execute("INSERT INTO resultats (note) VALUES (" + str(session["question_justes"]/session["question_max"]) + ")")
        c.commit()
        session["inserted"] = True

    # Récupère les scores.
    c = get_db().cursor()
    nb_res = c.execute("SELECT COUNT(*) AS n FROM `resultats`").fetchone()[0]
    nb_worse = c.execute(
        "SELECT COUNT(*) AS n FROM `resultats` WHERE `note` < " + 
        str(session["question_justes"]/session["question_max"])
    ).fetchone()[0]
    close_connection(None)

    # Affiche les résultats.
    score = int(session["question_justes"]/session["question_max"]*100)
    mieux = int(nb_worse/nb_res*100)
    return render_template("quiz/quiz_resultat.html", score=score, mieux=mieux, name=name)
#
#------------- fin quiz ------------------
#

#
#------------- début marketplace ------------------
#


@app.route('/marketplace')
def shopping():
    
    content=f"""<!DOCTYPE html><html lang='fr-fr'>
    <head>
        <meta charset="UTF-8" /> <!--l'encodage-->
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="stylesheet" type='text/css' href='static/marketplace/style.css')"><!--pour lier la page css-->
        <title> OPtimise </title> <!--le titre de l'onglet -->
    </head>
    <body>
    <div id="content">
            <header>
                <img src='static/marketplace/logo.png' alt="Logo de votre site" id="logo" />
                <h1>OPtimise, Tout sur l'Obsolescence Programmée !</h1>
            </header>
            <main>
    
                <nav> <!--barre latérale gauche-->"""
    login_token = request.cookies.get("token")
    connection = sqlite3.connect("OPtimise.db")
    if login_token is None:
        name = None
    else:
        name = list(connection.execute(f"SELECT name FROM users WHERE token = {login_token}"))[0][0]

    if name is not None:
        buttons = f"""<div class='loggedinas'>
            <span>Logged in as<br><b>{name}</b></span>
            <a href='/logout'>Log out</a>
        </div>"""
    else:
        buttons = f"""<div class='loggedinas'>
                    <a href='/login'><b>Log in</b></a>
                    <a href='/signup'><b>Sign up</b></a>
                </div>"""
    content += buttons
    connection.close()
    content += f"""
                    <ul>
                        <li><a href="/quiz">Quiz</a></li>
                        <li><a href="/classement/entreprise">Classements</a></li>
                        <li><a href="/blog">Blog</a></li>
                        <li><a href="/marketplace">Shopping</a></li>
                        <li><a href="/menu">Autre ressources</a></li>
                    </ul>
                </nav>
    <p> Besoin d'un appareil reconditionné ? Cherchez parmis une multitude de produits</p>
    
    <form action ='/marketplace' method='get'><input class='input' type="text" id='search' name='search' placeholder="Rechercher un produit...">
    </form><br>

    """

    s=request.args.get('search')
    page=request.args.get('page',default='1')
    
    if (s!='' and s!=None):
    
        backmarket_infos,nb_pages_backmarket=backmarket(s,page)
        afbshop_infos,nb_pages_afbshop=afbshop(s,page)
        ebay_infos,nb_pages_ebay=ebay(s,page)

        nb_pages=max(nb_pages_afbshop,nb_pages_backmarket,nb_pages_ebay)
        if (backmarket_infos!=[] or afbshop_infos!=[] or ebay_infos!=[]):
            i=0
            content+="<div class='grid-container'>"
            
            while (i<max(len(backmarket_infos),len(afbshop_infos),len(ebay_infos))):
            
                for j in range(0,2):
                    if (2*i+j)<len(backmarket_infos):
                        elt=backmarket_infos[2*i+j]
                        if elt[4]=='-1':
                            content+="<a class='grid-item' href="+elt[1]+"><br><img src='/static/marketplace/Back_Market.png' height='40' width='132'><br>"+elt[0]+"<br><br><img class='center-image-with-border' src="+elt[2]+" height='200' width='200'><br><br>Garantie"+elt[3]+"<br>À partir de :<div style='font-weight:bold; font-size:20px'>"+elt[5]+"</div></a>"
                        else:    
                            content+="<a class='grid-item' href="+elt[1]+"><br><img src='/static/marketplace/Back_Market.png' height='40' width='132'><br>"+elt[0]+"<br><br><img class='center-image-with-border' src="+elt[2]+" height='200' width='200'><br><br>Garantie"+elt[3]+"<br>Nombres d'étoiles "+elt[4]+"<br>À partir de :<div style='font-weight:bold; font-size:20px'>"+elt[5]+"</div></a>"
                    
                    
                if i<len(afbshop_infos):
                    elt=afbshop_infos[i]
                    if elt[3]!=None:
                        content+="<a class='grid-item' href="+elt[1]+"><br><img src='/static/marketplace/afb.png' height='40' width='132'><br>"+elt[0]+"<br><br><img class='center-image-with-border' src="+elt[2]+" height='200' width='200'><br><br>État : "+elt[3]+"<br>À partir de :<div style='font-weight:bold; font-size=30px'>"+elt[4]+"€</div></a>"
                    else:    
                        content+="<a class='grid-item' href="+elt[1]+"><br><img src='/static/marketplace/afb.png' height='40' width='132'><br>"+elt[0]+"<br><br><img class='center-image-with-border' src="+elt[2]+" height='200' width='200'><br><br>À partir de :<div style='font-weight:bold; font-size=30px'>"+elt[4]+"€</div></a>"
                        
                
                for j in range(0,4):
                    if (4*i+j)<len(ebay_infos):
                        elt=ebay_infos[4*i+j]
                        content+="<a class='grid-item' href="+elt[1]+"><br><img src='/static/marketplace/EBay.png' height='40' width='132'><br>"+elt[0]+"<br><br><img class='center-image-with-border' src="+elt[2]+" height='200' width='200'><br><br>"
                        for sub in elt[3]:
                            content+=sub+"<br>"
                        for infos in elt[4]:
                            prix=infos.split('EUR')
                            if len(prix)==2:
                                content+="<div style='font-weight:bold; font-size:20px'>"+prix[0]+'€</div><br>'
                            else:
                                content+=infos+'<br>'
                        content+='</a>'
                        
                i+=1

            content+="</div>"

            if nb_pages!=1:
                content+=f"""<div style='text-align:center;'>"""
                if page=='1':
                    content+=f"""<a class='current_page' href="/marketplace?search={s}&page=1">1 </a>
                    """
                else:
                    content+=f"""<a class='page' href="/marketplace?search={s}&page={str(int(page)-1)}"> < </a><a class='page' href="/marketplace?search={s}&page=1">1 </a>
                    """
                if int(page)>=4:
                    content+="..."
                for pages in range(int(page)-2,int(page)+3):
                    if (pages>1 and pages<nb_pages):
                        if pages==int(page):
                            content+=f"""<a class='current_page' href="/marketplace?search={s}&page={pages}">{pages} </a>"""
                        else:
                            content+=f"""<a class='page' href="/marketplace?search={s}&page={pages}">{pages} </a>"""
                if int(page)<=nb_pages-2:
                    content+="..."
                
                if page==str(nb_pages):
                    content+=f"""<a class='current_page' href="/marketplace?search={s}&page={nb_pages}">{nb_pages}</a></div>"""
                else:
                    content+=f"""<a class='page' href="/marketplace?search={s}&page={nb_pages}">{nb_pages}</a><a class='page' href="/marketplace?search={s}&page={str(int(page)+1)}"> > </a></div>"""
        else:
            content+="""<p>Désolé il s'emblerait que nous n'ayons pas trouvé ce que vous recherchez</p>
                        <p>À la place voici une photo mignone de chaton :</p>
                        <br><img class='center-image-with-border' src='static/marketplace/_light-23113-chat-pelote-de-laine.jpg' alt='Image de chat' height='400' width='453'><br>"""

    else:
        content+="""<p>OPtimise propose une sélection de produit issus des sites de Backmarket, ebay, et AfBshop.<br>
                    Lorsque cous cliquez sur un produit vous êtes redirigé vers la page produit du site en question.</p> """
    content+="""<footer> 
        <div class="bottom-bar">
            <ul>
                <li><a href="contact.html">Contact</a></li>
                <li><a href="aide.html">Aide</a></li>
                <li><a href="dons.html">Dons</a></li>
                <li><a href="vieprivee.html">Vie privée</a></li>
            </ul>
        </div>
                <p>&copy; 2023  Tous droits réservés.  </p>
            </footer>
        </body>"""
    return content


#
#------------- fin marketplace ------------------
#

#
#------------- début menu ------------------
#
@app.route('/menu')
def displaymenu():
    connection = sqlite3.connect("OPtimise.db")
    login_token = request.cookies.get("token")
    if login_token is None:
        name = None
    else:
        name = list(connection.execute(f"SELECT name FROM users WHERE token = {login_token}"))[0][0]
    connection.close()
    return render_template("menu/menu.html", name = name)



@app.route('/')
def welcome():
    connection = sqlite3.connect("OPtimise.db")
    login_token = request.cookies.get("token")
    if login_token is None:
        name = None
    else:
        name = list(connection.execute(f"SELECT name FROM users WHERE token = {login_token}"))[0][0]
    connection.close()
    return render_template("menu/menu.html", name = name)
#
#------------- fin menu ------------------
#
