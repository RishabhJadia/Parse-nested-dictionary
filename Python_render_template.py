#pip install jinja2
from jinja2 import Template

def render_template(directory, file, **kwargs):
    filec = read_file(directory, file)
    try:
        template = Template(filec)
        result = template.render(**kwargs)
    except Exception as e:
        # Raise an exception with a descriptive error message
        raise ValueError(f"Failed to render Jinja2 template: {str(e)}")

    return result
 ----------------------------------------------------------
#TestCase
import unittest
from unittest.mock import patch, mock_open

class TestRenderTemplate(unittest.TestCase):
    @patch("builtins.open", mock_open(read_data="Hello, {{ name }}!"))
    @patch("jinja2.Template.render")
    def test_render_template_positive(self, mock_render):
        # Test rendering a template with valid input
        mock_render.return_value = "Hello, Alice!"
        kwargs = {"name": "Alice"}
        result = render_template("templates", "test.html", **kwargs)
        self.assertEqual(result, "Hello, Alice!")
        mock_render.assert_called_once_with(**kwargs)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_render_template_missing_file(self, mock_open):
        # Test rendering a missing template file
        with self.assertRaises(ValueError) as excinfo:
            kwargs = {"name": "Alice"}
            result = render_template("templates", "missing.html", **kwargs)
        self.assertIn("Failed to create Jinja2 template:", str(excinfo.exception))

    @patch("builtins.open", mock_open(read_data="Hello, {{ name }}!"))
    @patch("jinja2.Template.render", side_effect=Exception("Variable 'name' is not defined"))
    def test_render_template_missing_variable(self, mock_render):
        # Test rendering a template with a missing variable
        kwargs = {}
        with self.assertRaises(ValueError) as excinfo:
            result = render_template("templates", "test.html", **kwargs)
        self.assertIn("Failed to render Jinja2 template:", str(excinfo.exception))
        mock_render.assert_called_once_with(**kwargs)
 ---------------------------------------------------------

import unittest
from unittest.mock import patch
from jinja2 import Template

def read_file(directory, file):
    # Implement the read_file function as per your requirement
    pass

def render_template(directory, file, **kwargs):
    filec = read_file(directory, file)
    try:
        template = Template(filec)
    except ValueError as err:
        template = err
    return template.render(**kwargs)

class RenderTemplateTestCase(unittest.TestCase):
    def test_render_template(self):
        directory = "templates"
        file = "template.html"
        kwargs = {'name': 'John Doe', 'age': 30}

        # Mock the read_file function
        with patch("__main__.read_file") as mock_read_file:
            mock_read_file.return_value = "Hello, {{ name }}. You are {{ age }} years old."

            result = render_template(directory, file, **kwargs)

            self.assertEqual(result, "Hello, John Doe. You are 30 years old.")

    def test_render_template_invalid_file(self):
        directory = "templates"
        file = "invalid_template.html"
        kwargs = {'name': 'John Doe', 'age': 30}

        # Mock the read_file function to raise an exception
        with patch("__main__.read_file") as mock_read_file:
            mock_read_file.side_effect = FileNotFoundError

            result = render_template(directory, file, **kwargs)

            self.assertIsInstance(result, FileNotFoundError)

if __name__ == '__main__':
    unittest.main()

# Using this it is also possible to send in email via email.py file
