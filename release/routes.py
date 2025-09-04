from flask import jsonify, request, send_from_directory

import analysis
import log_parser


def register_routes(app):
    @app.route('/')
    def serve_index():
        return send_from_directory('static', 'index.html')

    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_from_directory('static', filename)

    @app.route('/api/LogList', methods=['GET'])
    def get_log_list_api():
        if not log_parser.log_list:
            log_parser.log_list = log_parser.get_log_list()
        log_parser.log_list.reverse()
        return jsonify({'list': log_parser.log_list})

    @app.route('/api/analyse', methods=['GET'])
    def analyse_log():
        date = request.args.get('date', 'all')
        if date == 'all':
            return analysis.analyse_all_logs()
        else:
            return analysis.analyse_single_log(date)

    @app.route('/api/item-trend', methods=['GET'])
    def item_trend():
        item_name = request.args.get('item', '')
        if item_name:
            return analysis.analyse_item_history(item_name)
        return jsonify({})

    @app.route('/api/duration-trend', methods=['GET'])
    def duration_trend():
        return analysis.analyse_duration_history()

    @app.route('/api/total-items-trend', methods=['GET'])
    def item_history():
        return analysis.analyse_all_items()
