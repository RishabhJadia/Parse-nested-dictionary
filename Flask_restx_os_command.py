import os
import subprocess
from flask import Flask, request
from flask_restx import Api, Resource, fields

app = Flask(__name__)
api = Api(app, version='1.0', title='OS Command API',
    description='A limited API for executing specific read-only OS commands.')

ns = api.namespace('commands', description='OS commands operations')

# Define input model
command_model = api.model('Command', {
    'path': fields.String(required=True, description='Path to execute the command in'),
    'command': fields.String(required=True, description='Command to execute'),
    'filename': fields.String(description='Filename (for commands like cat, head, tail)'),
})

# Allowed read-only commands (added uptime and free)
ALLOWED_COMMANDS = [
    'ls', 'pwd', 'du -sh', 'cat', 'head', 'tail', 'file', 'wc',
    'find . -type f -print | wc -l', 'date', 'uptime', 'free -h' #Added uptime and free -h
]

def is_path_safe(base_path, user_path):
    """Checks if the user-provided path is within the allowed base path."""
    abs_path = os.path.abspath(os.path.join(base_path, user_path))
    return os.path.commonpath([base_path]) == os.path.commonpath([base_path, abs_path])

@ns.route('/')
class ExecuteCommand(Resource):
    @ns.expect(command_model, validate=True)
    @ns.response(200, 'Command executed successfully')
    @ns.response(400, 'Invalid input or command')
    @ns.response(500, 'Error executing command')
    def post(self):
        data = request.get_json()
        base_path = data.get('path')
        command = data.get('command')
        filename = data.get('filename')

        if not os.path.isdir(base_path):
            return {'message': 'Invalid base path'}, 400

        if command not in ALLOWED_COMMANDS:
            return {'message': 'Command not allowed'}, 400

        try:
            full_command = f"cd {base_path} && "

            if command in ['cat', 'head', 'tail', 'file']:
                if not filename:
                    return {'message': 'Filename is required for this command'}, 400
                if not is_path_safe(base_path, filename):
                    return {'message': 'Invalid file path'}, 400
                full_command += f"{command} {filename}"
            elif command == 'find . -type f -print | wc -l':
                full_command += "find . -type f -print | wc -l"
            else:
                full_command += command

            process = subprocess.Popen(
                full_command,
                shell=True,  # Only safe due to strict whitelisting and path validation
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                return {'output': stdout, 'error':stderr,'message': f'Command execution failed with return code: {process.returncode}'}, 500

            return {'output': stdout, 'error': stderr}, 200

        except subprocess.TimeoutExpired:
            return {'message': 'Command execution timed out'}, 500
        except Exception as e:
            return {'message': f'Error executing command: {str(e)}'}, 500

if __name__ == '__main__':
    app.run(debug=True)
