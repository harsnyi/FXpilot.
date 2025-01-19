from flask import Blueprint, request, jsonify

def create_tickers_bp(handler):
    tickers_bp = Blueprint('settings', __name__)

    @tickers_bp.route('/list_options', methods=['GET'])
    def list_options():
        options = handler.get_options()
        return jsonify({"options": options}), 200

    @tickers_bp.route('/options/<option_name>', methods=['GET'])
    def get_option(option_name):
        option = handler.get_option(option_name)
        if option is None:
            return jsonify({"error": f"Option '{option_name}' not found"}), 404
        return jsonify({option_name: option}), 200

    @tickers_bp.route('/options/update/<option_name>', methods=['PUT'])
    def update_option(option_name):
        try:
            new_data = request.json
            if not new_data:
                return jsonify({"error": "No data provided"}), 400

            result = handler.update_option(option_name, new_data)

            if result["success"]:
                return jsonify({"message": result["message"]}), 200
            else:
                return jsonify({"error": "Validation errors", "details": result["errors"]}), 400

        except Exception as e:
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    @tickers_bp.route('/options/create', methods=['POST'])
    def create_option():
        try:
            new_data = request.json
            if not new_data:
                return jsonify({"error": "No data provided"}), 400
            name = new_data.get("name", None)
            if not name:
                return jsonify({"error": "Option name is required"}), 400
            result = handler.create_option(name, new_data)

            if result["success"]:
                return jsonify({"message": result["message"]}), 201
            else:
                return jsonify({"error": "Validation errors", "details": result["errors"]}), 400

        except Exception as e:
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    return tickers_bp
