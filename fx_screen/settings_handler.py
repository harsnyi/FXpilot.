
import yaml
import os

class ScreeningOptionsHandler:
    def __init__(self, OPTIONS_PATH, SCHEMA_PATH):
        self.OPTIONS_PATH = OPTIONS_PATH
        self.options = {}
        
        with open(SCHEMA_PATH, 'r') as f:
            try:
                self.schema = yaml.safe_load(f)
            except yaml.YAMLError:
                print("Error in reading schema file.")
                self.schema = {}

        if os.path.exists(OPTIONS_PATH):
            for file in os.listdir(OPTIONS_PATH):
                if file.endswith('.yaml'):
                    with open(f"{OPTIONS_PATH}/{file}", 'r') as f:
                        try:
                            data = yaml.safe_load(f) or {}
                            name = data.get('name', file)
                            self.options[name] = data
                        except yaml.YAMLError:
                            print(f"Warning: Corrupted YAML file {file}. Skipping.")
                        except Exception as e:
                            print(f"Error in reading: {e}")


        elif not os.path.exists(OPTIONS_PATH):
            os.makedirs(OPTIONS_PATH)


    def get_options(self):
        return self.options


    def get_option(self, option_name):
        return self.options.get(option_name, None)


    def validate_setting(self, setting_name, setting_value, schema):
        if schema["type"] == "string":
            if not isinstance(setting_value, str):
                return f"{setting_name} must be a string."
        elif schema["type"] == "list":
            if not isinstance(setting_value, list):
                return f"{setting_name} must be a list."
            if "allowed_values" in schema:
                for item in setting_value:
                    if item not in schema["allowed_values"]:
                        return f"{item} in {setting_name} is not allowed."
        elif schema["type"] == "integer":
            if not isinstance(setting_value, int):
                return f"{setting_name} must be an integer."
        return None


    def validate(self, data):
        errors = []
        for key, definition in self.schema.items():
            if key in data:
                error = self.validate_setting(key, data[key], definition)
                if error:
                    errors.append(error)
            elif definition.get("required", False):
                errors.append(f"{key} is required.")
        return errors


    def update_option(self, option_name, new_data):
        errors = self.validate(new_data)
        if errors:
            return {"success": False, "errors": errors}

        option_file = os.path.join(self.OPTIONS_PATH, f"{option_name}.yaml")
        try:
            with open(option_file, 'w') as f:
                yaml.safe_dump(new_data, f, default_flow_style=False)

            self.options[option_name] = new_data
            return {"success": True, "message": f"Option '{option_name}' updated successfully"}
        except Exception as e:
            return {"success": False, "errors": [f"Failed to update option: {e}"]}


    def create_option(self, option_name, new_data):
        errors = self.validate(new_data)
        if errors:
            return {"success": False, "errors": errors}

        if option_name in self.options:
            return {"success": False, "errors": [f"Option '{option_name}' already exists."]}

        option_file = os.path.join(self.OPTIONS_PATH, f"{option_name}.yaml")
        try:
            with open(option_file, 'w') as f:
                yaml.safe_dump(new_data, f, default_flow_style=False)

            self.options[option_name] = new_data
            return {"success": True, "message": f"Option '{option_name}' created successfully"}
        except Exception as e:
            return {"success": False, "errors": [f"Failed to create option: {e}"]}