from flask import Flask, request

from data import get_user_cards, get_users, get_user, get_transitive_reports, get_direct_reports

app = Flask(__name__)

page = """<html><head>
<style>
a {{
  text-decoration: none;
}}

a:hover {{
  text-decoration: underline;
}}

.sql {{
  font-family: monospace;
  background-color: #EEE;
  border: 2px solid #888;
  padding: 15px;
  margin-top: 5px;
}}

.oso-fragment {{
  color: blue;
}}

.code {{
  font-family: monospace;
}}
</style>
</head><body>{}</body></html>""".format

@app.route("/users")
def html_users():
    past = request.args.get("past")
    users_data = get_users(past)
    if not users_data['users']:
        return page("<h3>Users</h3><em>No results</em>")
    users_list = ''.join(
        f"""<li><a href="/users/{user['user_id']}/cards">{user['name']}</li>"""
        for user in users_data['users']
    )
    return page(f"""
    <h3>Users</h3>
    <ul>{users_list}</ul>
    <a href="/users?past={users_data['past']}">Next Page</a>
    """)


@app.route("/users/<user_id>/cards")
def html_user_cards(user_id):
    past = request.args.get("past")
    user = get_user(user_id)

    if user is None:
        return page(f"""
        <a href="/users">&lt; Users</a>
        <br />
        <h3><em>User not found</em></h3>
        """)

    reports = get_transitive_reports(user_id)
    direct_reports = get_direct_reports(user_id)
    cards_data = get_user_cards(user_id, past)

    cards_list = ''.join(f"<li>{card['card_id']} (owner: <a href='/users/{card['owner_id']}/cards'>{card['owner']}</a>)</li>" for card in cards_data['cards']) or "No results"
    next_page_button = f"""<a href="/users/{user_id}/cards?past={cards_data['past']}">Next Page</a>""" if cards_data['past'] else ""
    manager_line = f"""<li>Manager: <a href="/users/{user['manager_id']}/cards">{user['manager_name']}</a></li>""" if user['manager_id'] else ""

    sql_html = (
        cards_data['sql']
        .replace(cards_data['oso_fragment'], f"<span class='oso-fragment'>{cards_data['oso_fragment']}</span>")
        .replace("\n", "<br />")
    )

    query_time = f"{cards_data['query_time'] * 1000:.2f}"

    return page(f"""
    <a href="/users">&lt; Users</a>
    <h1>{user['name']}</h1>
    <ul>
        <li>{len(reports)} transitive reports</li>
        <li>{len(direct_reports)} direct reports</li>
        {manager_line}
    </ul>
    <div>
        <h3>Cards ({cards_data['total_cards']} total)</h3>
        <ul>{cards_list}</ul>
        {next_page_button}
    </div>
    <hr>
    <div>
        <h3>Cards Query</h3>
        <p>
        This is the full Postgres query to fetch cards this user is allowed to view.
        The section in blue is the authorization filter returned by <span class="code">oso.list_local</span>.
        </p>
        Query ran in {query_time}ms
        <div class="sql">{sql_html}</div>
    </div>
    """)
