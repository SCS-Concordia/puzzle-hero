from config import config
from sanic.response import json
import rest_service
from helpers import ok, error

def get_heartbeat(request=None):
    return json(ok('hello world'))

def get_slack_users(request=None, db_session=None):
    slack_users_response = rest_service.slack_users().json()
    if not slack_users_response['ok']:
        return json(error('Slack API error'), status=504)
    else:
        formatted_slack_users = []
        for slack_user in slack_users_response['members']:
            if not slack_user['deleted'] and slack_user['name'] not in config['blacklisted_slack_users']:
                formatted_slack_user = {
                    'username': slack_user['name'],
                    'realname': slack_user['profile']['real_name_normalized'],
                    'avatar': slack_user['profile']['image_192']
                }
                formatted_slack_users.append(formatted_slack_user)
        return json(ok(formatted_slack_users))

def post_verify_slack_email(request=None, db_session=None):
    slack_users_response = rest_service.slack_users().json()
    if not slack_users_response['ok']:
        return json(error('Slack API error'), status=504)
    slack_user_to_email = None
    for slack_user in slack_users_response['members']:
        if not slack_user['deleted'] and \
                slack_user['name'] not in config['blacklisted_slack_users'] and \
                request.json.get('username') == slack_user['name']:
            slack_user_to_email = slack_user
            break

    # if already_registered:
    #       if password is correct:
    #           log user in
    #       else:
    #           don't log user in, prompt to reset password
    # else:
    #      if password is not strong:
    #           return for stronger password
    #      else:
    #           create user, ask for email confirmation

    # TODO: Should write a user to db here as an attempted registration
    # - username: VARCHAR
    # - SALTED ENCRYPTED PASSWORD: VARCHAR?
    # - registered: FALSE
    # - last_attempted_registration: CURRENT DATE
    # - confirmation_code: VARCHAR (random string)

    # TODO: Make sure that the password is long enough
    # If so, return here, front-end should refuse registration

    return json(ok(request.json))

def authenticate_user(request=None, db_session=None):
    if "username" not in request or "password" not in request:
        return json(error("Malformed authenticate_user request"))

    succeeded, message = rest_service.authenticate_user(db_session, request)
    result = ok if succeeded else error
    return json(result(message))


def get_app_users(request=None, db_session=None):
    query_filter = {}
    if "username" in request:
        query_filter["username"] = request["username"]
    if "team" in request:
        query_filter["team_name"] = request["team"]

    users_response = rest_service.app_users(db_session, query_filter)
    users = [{
             'username': user.username,
             'name': user.name,
             'score': user.score,
             'team': user.team_name
             } for user in users_response]

    return json(ok(users))


def get_teams(request=None, db_session=None):
    query_filter = {}
    if "name" in request:
        query_filter["name"] = request["name"]

    teams_response = rest_service.teams(db_session, query_filter)
    teams = [{
             'name': team.name,
             'members': [user.username for user in team.members]
             } for team in teams_response]

    return json(ok(teams))


def add_user(request=None, db_session=None):
    data = {
        "username": request["username"],
        "password": request["password"]
    }
    slack_users = rest_service.slack_users().json()
    slack_users = [user for user in slack_users['members'] if user["name"] == request["username"]]

    if not slack_users or slack_users[0]['deleted'] or slack_users[0]['name'] in config['blacklisted_slack_users']:
        return json(error("No Slack user {}".format(request["username"])))

    data["name"] = slack_users[0]['profile']['real_name_normalized']

    succeeded, message = rest_service.add_user(db_session, data)
    result = ok if succeeded else error
    return json(result(message))


def modify_user(request=None, db_session=None):
    succeeded, message = rest_service.modify_user(db_session, request)
    result = ok if succeeded else error
    return json(result(message))


def add_team(request, db_session):
    if "name" not in request or "username" not in request:
        return json(error("Malformed request: {}".format(request)))

    succeeded, data = rest_service.add_team(db_session, request)
    result = ok if succeeded else error
    return json(result(data))


def join_team(request=None, db_session=None):
    if "name" not in request or "username" not in request:
        return json(error("Malformed request: {}".format(request)))

    succeeded, message = rest_service.join_team(db_session, request)
    result = ok if succeeded else error
    return json(result(message))


def add_challenge(request=None, db_session=None):
    pass

