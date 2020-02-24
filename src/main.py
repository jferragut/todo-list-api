"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os

from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from models import db,User,Todos

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/todos/user/<username>', methods=['POST', 'GET', 'PUT','DELETE'])
def handle_hello(username):
    # Case: GET REQUEST
    if request.method == "GET":
        # query a user by username and store it in the user var
        # user should only ever return one result because the username is unique
        # but we will return only the .first() instead of .all() anyway
        user = User.query.filter_by(username=username).first()

        # if user is not empty, meaning query returned something
        # we set the response_body to the serialized version
        if user is not None:
            response_body = user.serialize_todos()
            response_status_code = 200
        else:
            response_body = 'User was not found. Please check the username and try again.'
            response_status_code = 404

    # Case: POST REQUEST
    elif request.method == "POST":
        body = request.get_json() # Get body from request as JSON

        # Test to see if the client app sent a request with empty array in body
        if isinstance(body, list):
            user = User()               # user is an instance of the User model
            user.username = username    # set username to the username from the api path variable <username>

            # we dont need to set id because it is automatically generated
            # we also don't need to set todos because it is by nature a list. Comes from a 1 to n relationship to Todos() class

            db.session.add(user)        # add the new user via db.session
            db.session.commit()         # commit changes

            # next, we will define what the response should be and the status code
            # this will be returned at the end of our function so that we don't have to repeat the return
            response_body = {
                "result": "ok"
            }
            response_status_code = 200

    # Case: PUT REQUEST
    elif request.method == "PUT":
        body = request.get_json() # Get body from request as JSON
        if isinstance(body, list):
            # loop the list in body
            for todo in body:
                # make sure the todo we are looking at isn't empty
                if todo is not None:
                    try:
                        todo_item = Todos()                                     # instantiate a new Todo()
                        user = User.query.filter_by(username=username).first()  # query the user

                        # set label, done, and user_id field for the new todo
                        todo_item.label = todo['label']
                        todo_item.done = todo['done']
                        todo_item.user_id = user.id

                        db.session.add(todo_item)                               # add the current todo
                        db.session.commit()                                     # commit the change
                    except Exception as e:
                        return jsonify(f"An Error Occured: {e}")
                    
                # set response body and status code
                response_body = {
                    "result": "A list with %r todos was succesfully saved" % len(body)
                }
                response_status_code = 200

    # Case: DELETE REQUEST
    elif request.method == "DELETE":
        try:
            user = User.query.filter_by(username=username).first()  # get user by username
            todos = Todos.query.filter_by(user_id=user.id).all()    # get todos for given username

            # loop todos list
            for item in todos:
                db.session.delete(item) # delete each todo related to the current user from the list

            db.session.delete(user)     # delete the selected user
            db.session.commit()         # commit the changes
            
            # set the response body and status_code
            response_body = { 
                "result": "ok" 
            }
            response_status_code = 200
            
        except Exception as e:
            return jsonify(f"An Error Occured: {e}")


    return jsonify(response_body), response_status_code

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
