import controller
import json
import pytest
import requests
import mocks
from rest_service import slack_users
from sanic.response import HTTPResponse

######### GET TESTS ###########

def test_get_heartbeat():
    assert isinstance(controller.get_heartbeat(), HTTPResponse)
    assert controller.get_heartbeat().status == 200
    data = json.loads(controller.get_heartbeat(None).body)
    assert data == {'data': 'hello world', 'ok': True}

def test_get_slack_users_slack_api_error(monkeypatch):
    class SlackUsersMock:
        def __init__(*args, **kwargs):
            return
        def json(self):
            return {
                'ok': False,
                'members': []
            }
    monkeypatch.setattr(requests, 'get', SlackUsersMock)
    assert isinstance(controller.get_slack_users(), HTTPResponse)
    assert controller.get_slack_users().status == 504
    data = json.loads(controller.get_slack_users().body)
    assert data == {'message': 'Slack API error', 'ok': False}

def test_get_app_users():
    mockUser = mocks.MockUser("testuser", "testpassword", "tester", 0, "sudoers")
    mockRequest = {"username": "testuser", "team": "sudoers"}

    result = controller.get_app_users(mockRequest, mocks.MockFilterProvider(mockUser))
    data = json.loads(result.body)
    assert data['ok']
    assert data['data'][0]['username'] == mockRequest["username"]

def test_get_teams():
    mockTeam = mocks.MockTeam("team1", [mocks.MockUser("testuser")])
    mockRequest = {"name": "team1"}

    result = controller.get_teams(mockRequest, mocks.MockFilterProvider(mockTeam))
    data = json.loads(result.body)
    assert data['ok']
    assert data['data'][0] is not None

def test_get_slack_users_no_users(monkeypatch):
    class SlackUsersMock:
        def __init__(*args, **kwargs):
            return
        def json(self):
            return {
                'ok': True,
                'members': []
            }
    monkeypatch.setattr(requests, 'get', SlackUsersMock)
    assert isinstance(controller.get_slack_users(), HTTPResponse)
    assert controller.get_slack_users().status == 200
    data = json.loads(controller.get_slack_users().body)
    assert data == {'data': [], 'ok': True}

def test_get_slack_users_filters_deleted_and_blacklisted(monkeypatch):
    class SlackUsersMock:
        def __init__(*args, **kwargs):
            return
        def json(self):
            return {
                'ok': True,
                'members': [
                    {
                        'deleted': True,
                        'name': 'snax',
                        'profile': {
                            'real_name_normalized': 'Hot Dog',
                            'image_192': 'https://fakeurl.coolbeans'
                        }
                    },
                    {
                        'deleted': False,
                        'name': 'testuser',
                        'profile': {
                            'real_name_normalized': 'Will BeFiltered',
                            'image_192': 'https://fakeurl.coolbeans'
                        }
                    },
                    {
                        'deleted': False,
                        'name': 'real_user',
                        'profile': {
                            'real_name_normalized': 'Bloop Bloop',
                            'image_192': 'https://fakeurl.coolbeans'
                        }
                    }
                ]
            }
    monkeypatch.setattr(requests, 'get', SlackUsersMock)
    assert isinstance(controller.get_slack_users(), HTTPResponse)
    assert controller.get_slack_users().status == 200
    data = json.loads(controller.get_slack_users().body)
    assert data == {
        'data': [{
            'username': 'real_user',
            'realname': 'Bloop Bloop',
            'avatar': 'https://fakeurl.coolbeans',

        }],
        'ok': True
    }

######## AUTH TESTS ###########

def test_authenticate_user():
    mockUser = mocks.MockUser("testuser", "testpassword")
    mockRequest = {"username": "testuser", "password": "testpassword"}
    mockWrongRequest = {"username": "testuser"}
    correct = controller.authenticate_user(mockRequest, mocks.MockFilterProvider(mockUser))
    incorrect = controller.authenticate_user(mockWrongRequest, mocks.MockFilterProvider(mockUser))
    data = json.loads(correct.body)
    assert data['ok']
    data = json.loads(incorrect.body)
    assert not data['ok']


######## ADD TESTS #############

def test_add_user(monkeypatch):
    class SlackUsersMock:
        def __init__(*args, **kwargs):
            return
        def json(self):
            return {
                'ok': True,
                'members': [
                    {
                        'deleted': False,
                        'name': 'snax',
                        'profile': {
                            'real_name_normalized': 'Hot Dog',
                            'image_192': 'https://fakeurl.coolbeans'
                        }
                    },
                    {
                        'deleted': False,
                        'name': 'fail',
                        'profile': {
                            'real_name_normalized': 'I should throw',
                            'image_192': 'https://fakeurl.coolbeans'
                        }
                    }
                ]
            }
    monkeypatch.setattr(requests, 'get', SlackUsersMock)
    response = controller.get_slack_users()
    assert isinstance(response, HTTPResponse)
    assert response.status == 200

    mockRequest = {"username": "four-o-four", "password": "no"}
    noSlackResult = json.loads(controller.add_user(mockRequest, None).body)
    assert noSlackResult["ok"] == False
    assert noSlackResult["message"] == "No Slack user four-o-four"

    mockRequest = {"username": "snax", "password": "no"}
    someSlackResult = json.loads(controller.add_user(mockRequest, mocks.MockAdderDatabase()).body)
    assert someSlackResult["ok"]
    assert someSlackResult["data"] == "Successfully added User snax"

    mockRequest = {"username": "fail", "password": "no"}
    failSlackResult = json.loads(controller.add_user(mockRequest, mocks.MockAdderDatabase()).body)
    assert failSlackResult["ok"] == False

###### MODIFY TESTS ########

def test_modify_user():
    result = controller.modify_user({"username": "snax", "name": "Hamburger", "changes": {}}, mocks.MockAdderDatabase())
    result = json.loads(result.body)
    assert result["ok"]

    result = controller.modify_user({"username": "fail", "name": "Hamburger", "changes": {}}, mocks.FaultyCommitDatabase())
    result = json.loads(result.body)
    assert result["ok"] == False

def test_add_challenge():
    controller.add_challenge(None, None)
