from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, UTC, timedelta

 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})

@api.route('/todos', methods=['GET'])
def get_todos():
    query = Todo.query

    # 处理 completed 参数
    if 'completed' in request.args:
        completed = request.args.get('completed').lower() == 'true'
        query = query.filter_by(completed=completed)

    # 处理 window 参数
    if 'window' in request.args:
        try:
            days = int(request.args.get('window'))
            if days < 0:
                raise ValueError()
            due_date = datetime.now(UTC) + timedelta(days=days)
            query = query.filter(Todo.deadline_at <= due_date)
        except ValueError:
            return jsonify({'error': 'Invalid window value'}), 400  # 确保返回 HTTP 响应

    todos = query.all()
    
    # 确保无论如何都返回 JSON 响应
    return jsonify([todo.to_dict() for todo in todos]), 200

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if todo is None:
       return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

ALLOWED_FIELDS = {'title', 'description', 'completed', 'deadline_at'}

@api.route('/todos', methods=['POST'])
def create_todo():
    if not request.json or 'title' not in request.json:
        return jsonify({'error': 'Title is required'}), 400

    extra_fields = set(request.json.keys()) - ALLOWED_FIELDS
    if extra_fields:
        return jsonify({'error': f'Unexpected fields: {extra_fields}'}), 400

    todo = Todo(
        title=request.json['title'],
        description=request.json.get('description'),
        completed=request.json.get('completed', False)
    )

    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json['deadline_at'])

    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 201



ALLOWED_FIELDS = {'title', 'description', 'completed', 'deadline_at'}

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404

    # 防止修改 ID
    if 'id' in request.json:
        return jsonify({'error': 'ID cannot be modified'}), 400

    # 检查是否有非法字段
    extra_fields = set(request.json.keys()) - ALLOWED_FIELDS
    if extra_fields:
        return jsonify({'error': f'Unexpected fields: {extra_fields}'}), 400

    # 只更新允许的字段
    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
    
    db.session.commit()
    return jsonify(todo.to_dict())


@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if todo is None:
       return jsonify({}), 200
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200
 
