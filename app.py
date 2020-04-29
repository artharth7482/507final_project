from flask import Flask, render_template, request
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
import random

app = Flask(__name__)

def get_player_overview(first_name,last_name):
    conn = sqlite3.connect('atp.sqlite')
    cur = conn.cursor()

    q = f'''
        SELECT PlayerImage,FirstName,LastName,Rank,Country,Age,Height,Weight,Plays,Gear1,GearImage1,Gear2,GearImage2,Gear3,GearImage3
        FROM Players
        WHERE FirstName = "{first_name}" AND LastName = "{last_name}"
    '''
    results = cur.execute(q).fetchone()
    conn.close()
    return results

def convert(tup):
    di={}
    for a, b in tup: 
        di[a]=b 
    return di 

def year_performance(year,first_name,last_name):
    conn = sqlite3.connect('atp.sqlite')
    cur = conn.cursor()
    additional_clause = f'''
        AND strftime('%Y', Matches.Date) = "{year}"
        GROUP BY Month
    '''
    q_winner = f'''
        SELECT strftime('%m', Matches.Date) as Month, COUNT(Matches.Id) as Win
        FROM Matches
        JOIN Players as P1
            ON Matches.Winner = P1.Id
        WHERE P1.FirstName = "{first_name}" AND P1.LastName = "{last_name}"{additional_clause}
    '''

    q_loser = f'''
        SELECT strftime('%m', Matches.Date) as Month, COUNT(Matches.Id) as Lose
        FROM Matches
        JOIN Players as P2
            ON Matches.Loser = P2.Id
        WHERE P2.FirstName = "{first_name}" AND P2.LastName = "{last_name}" {additional_clause}
    '''

    results_win = cur.execute(q_winner).fetchall()
    results_lose = cur.execute(q_loser).fetchall()
    conn.close()

    dic_win = convert(results_win)
    dic_lose = convert(results_lose)  

    for i in ['01','02','03','04','05','06','07','08','09','10','11','12']:
        if i not in dic_win:
            dic_win[i]=0
        else:
            dic_win[i]=int(dic_win[i])
        if i not in dic_lose:
            dic_lose[i]=0
        else:
            dic_lose[i]=int(dic_lose[i])

    dd = {} #combine two dictionaries with same keys
    for i in ['01','02','03','04','05','06','07','08','09','10','11','12']:
        dd[i]=dic_win[i],dic_lose[i]
    return dd

def h2h_calculator(player1_firstname,player1_lastname,player2_firstname,player2_lastname,surface,match_round,bestof):
    conn = sqlite3.connect('atp.sqlite')
    cur = conn.cursor()
    
    additional_surface_clause = ""
    additional_round_clause = ""
    additional_bestof_clause = ""

    if surface != "All":
        additional_surface_clause = f'''
            AND Matches.Surface = "{surface}"
        '''
    if match_round != "All":
        additional_round_clause = f'''
            AND Matches.Round = "{match_round}"
        '''
    if bestof != "All":
        additional_bestof_clause = f'''
            AND Matches.BestOf = "{bestof}"
        '''

    additional_clause = f'''
        {additional_surface_clause} {additional_round_clause} {additional_bestof_clause}
    '''

    q1_win = f'''
        SELECT COUNT(Matches.Id) AS P1Win, P1.PlayerImage, P1.FirstName, P1.LastName, P1.Rank, P1.Country
        FROM Matches
        JOIN Players AS P1
            ON Matches.Winner = P1.Id
        JOIN Players AS P2
            ON Matches.Loser = P2.Id
        WHERE P1.FirstName = "{player1_firstname}" AND P1.LastName = "{player1_lastname}" AND P2.FirstName = "{player2_firstname}" AND P2.LastName = "{player2_lastname}" {additional_clause}
    '''

    q2_win = f'''
        SELECT COUNT(Matches.Id) AS P2Win, P2.PlayerImage, P2.FirstName, P2.LastName, P2.Rank, P2.Country
        FROM Matches
        JOIN Players AS P2
            ON Matches.Winner = P2.Id
        JOIN Players AS P1
            ON Matches.Loser = P1.Id
        WHERE P1.FirstName = "{player1_firstname}" AND P1.LastName = "{player1_lastname}" AND P2.FirstName = "{player2_firstname}" AND P2.LastName = "{player2_lastname}" {additional_clause}
    '''

    player1_win = cur.execute(q1_win).fetchall()
    player2_win = cur.execute(q2_win).fetchall()
    conn.close()
    h2h_result_list = [player1_win,player2_win]
    return h2h_result_list

def random_player_overview(number):
    conn = sqlite3.connect('atp.sqlite')
    cur = conn.cursor()

    q = f'''
        SELECT PlayerImage,FirstName,LastName,Rank,Country,Age,Height,Weight,Plays,Gear1,GearImage1,Gear2,GearImage2,Gear3,GearImage3
        FROM Players
        WHERE Players.Id = "{number}"
    '''
    q_us = f'''
        SELECT Matches.Round
        FROM Matches
        JOIN Players
            ON Matches.Winner = Players.Id
        WHERE Players.Id = "{number}" AND Matches.Tournament = "US Open"
    '''
    q_fr = f'''
        SELECT Matches.Round
        FROM Matches
        JOIN Players
            ON Matches.Winner = Players.Id
        WHERE Players.Id = "{number}" AND Matches.Tournament = "French Open"
    '''
    q_uk = f'''
        SELECT Matches.Round
        FROM Matches
        JOIN Players
            ON Matches.Winner = Players.Id
        WHERE Players.Id = "{number}" AND Matches.Tournament = "Wimbledon"
    '''
    q_au = f'''
        SELECT Matches.Round
        FROM Matches
        JOIN Players
            ON Matches.Winner = Players.Id
        WHERE Players.Id = "{number}" AND Matches.Tournament = "Australian Open"
    '''

    results_player = cur.execute(q).fetchone()
    results_us = cur.execute(q_us).fetchall()
    results_fr = cur.execute(q_fr).fetchall()
    results_uk = cur.execute(q_uk).fetchall()
    results_au = cur.execute(q_au).fetchall()
    conn.close()
    results = [results_player,results_au,results_fr,results_uk,results_us]
    return results

def convert(tup):
    di={}
    for a, b in tup: 
        di[a]=b 
    return di

def higher_round(list):
    result = "Haven't won any game :("
    for i in list:
        if "The Final" in i:
            result = "The Final"
        elif "Semifinals" in i:
            result = "Semifinals"
        elif "Quarterfinals" in i:
            result = "Quarterfinals"
        elif "4th Round" in i:
            result = "4th Round"
        elif "3rd Round" in i:
            result = "3rd Round"
        elif "2nd Round" in i:
            result = "2nd Round"
        elif "1st Round" in i:
            result = "1st Round"
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/player')
def player():
    return render_template('player.html')

@app.route('/player_result', methods=['POST'])
def search_player():
    player_name = request.form['name']
    overview = get_player_overview(player_name.split(' ')[0],player_name.split(' ')[1])
    return render_template('player_result.html', result=overview)

@app.route('/player_result2', methods=['POST'])
def plot():
    player_name = request.form['name']
    search_year = request.form['year']
    first_name = player_name.split(' ')[0]
    last_name = player_name.split(' ')[1]

    results = year_performance(search_year,first_name,last_name)
    x_vals = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    y_vals_win = []
    y_vals_lose = []
    for key in results:
        y_vals_win.append(results[key][0])
        y_vals_lose.append(results[key][1])
    
    bars_data = [
    go.Bar(name='Win', x=x_vals, y=y_vals_win),
    go.Bar(name='Lose', x=x_vals, y=y_vals_lose)
    ]

    fig = go.Figure(data=bars_data).update_layout(barmode='group', xaxis_tickangle=-45)

    div = fig.to_html(full_html=False)
    return render_template("player_result2.html", plot_div=div, year=search_year, first_name=first_name,last_name=last_name)

@app.route('/h2h')
def h2h():
    return render_template('h2h.html')

@app.route('/h2h_result', methods=['POST'])
def search_h2h():
    player1_name = request.form['name1']
    player2_name = request.form['name2']
    surface = request.form['surface']
    match_round = request.form['round']
    best_of = request.form['best']
    player1_firstname = player1_name.split(" ")[0]
    player1_lastname = player1_name.split(" ")[1]
    player2_firstname = player2_name.split(" ")[0]
    player2_lastname = player2_name.split(" ")[1]
    results = h2h_calculator(player1_firstname,player1_lastname,player2_firstname,player2_lastname,surface,match_round,best_of)
    p1_win = results[0][0][0]
    p1_image = results[0][0][1]
    p1_fname = results[0][0][2]
    p1_lname = results[0][0][3]
    p1_rank = results[0][0][4]
    p1_country = results[0][0][5]
    p2_win = results[1][0][0]
    p2_image = results[1][0][1]
    p2_fname = results[1][0][2]
    p2_lname = results[1][0][3]
    p2_rank = results[1][0][4]
    p2_country = results[1][0][5]
    return render_template('h2h_result.html', p1_win = p1_win,
    p1_image = p1_image,p1_fname = p1_fname, p1_lname = p1_lname, p1_rank = p1_rank, p1_country = p1_country, p2_win = p2_win, p2_image = p2_image, p2_fname = p2_fname, p2_lname = p2_lname, p2_rank = p2_rank, p2_country = p2_country)

@app.route('/random')
def random_player():
    number = random.randint(1,1291)
    results = random_player_overview(number)
    player = results[0]
    results_au = higher_round(results[1])
    results_fr = higher_round(results[2])
    results_uk = higher_round(results[3])
    results_us = higher_round(results[4])
    return render_template('random.html',player=player,results_au=results_au,results_fr=results_fr,results_uk=results_uk,results_us=results_us)

if __name__ == '__main__':
    app.run(debug=True)