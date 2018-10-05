# -*- coding: utf-8 -*-
from flask import jsonify
from flask_restful import Resource, reqparse, abort

TODOS = {
    'todo1': {
        'task': 'build an API'
    },
    'todo2': {
        'task': '?????'
    },
    'todo3': {
        'task': 'profit!'
    },
    '42': {
        'task': 'Use Flasgger'
    }
}


def abort_if_todo_doesnt_exist(todo_id):
    if todo_id not in TODOS:
        abort(404, message="Todo {} doesn't exist".format(todo_id))


parser = reqparse.RequestParser()
parser.add_argument('task')


class Todo(Resource):
    """Shows a single To-do item and lets you delete a To-do item
    """

    def get(self, todo_id):
        """Returns a To-Do task
        This is an example
        ---
        tags:
          - To-Do list
        parameters:
          - in: path
            name: todo_id
            required: true
            description: The ID of the task, try 42!
            type: string
        responses:
          200:
            description: The task data
            schema:
              id: Task
              properties:
                task:
                  type: string
                  default: My Task
        """
        abort_if_todo_doesnt_exist(todo_id)
        return TODOS[todo_id]

    def delete(self, todo_id):
        """Deletes a To-Do task
        This is an example
        ---
        tags:
          - To-Do list
        parameters:
          - in: path
            name: todo_id
            required: true
            description: The ID of the task, try 42!
            type: string
        responses:
          204:
            description: Task deleted
        """
        abort_if_todo_doesnt_exist(todo_id)
        del TODOS[todo_id]
        return '', 204

    def put(self, todo_id):
        """Creates or update the To-Do task
        This is an example
        ---
        tags:
          - To-Do list
        parameters:
          - in: body
            name: body
            schema:
              $ref: '#/definitions/Task'
          - in: path
            name: todo_id
            required: true
            description: The ID of the task, try 42!
            type: string
        responses:
          201:
            description: The task has been updated
            schema:
              $ref: '#/definitions/Task'
        """
        args = parser.parse_args()
        task = {'task': args['task']}
        TODOS.update(todo_id=task)
        return task, 201


class TodoList(Resource):
    """TodoList
    Shows a list of all tasks to do, and lets you POST to add new tasks
    """

    def get(self):
        """Shows the To-do list
        This is an example
        ---
        tags:
          - To-Do list
        responses:
          200:
            description: The task data
            schema:
              id: Tasks
              properties:
                task_id:
                  type: object
                  schema:
                    $ref: '#/definitions/Task'
        """
        return TODOS

    def post(self):
        """Creates a new To-Do task
        This is an example
        ---
        tags:
          - To-Do list
        definitions:
          Task:
            task:
              type: string
              description: The name of the task
        parameters:
          - in: body
            name: body
            schema:
              $ref: '#/definitions/Task'
        responses:
          201:
            description: The task has been created
            schema:
              $ref: '#/definitions/Task'
        """
        args = parser.parse_args()
        todo_id = int(max(TODOS.keys()).lstrip('todo')) + 1
        todo_id = 'todo%i' % todo_id
        TODOS[todo_id] = {'task': args['task']}
        resp = jsonify(TODOS[todo_id])
        resp.status_code = 201
        return resp
