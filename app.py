from flask import Flask, request, jsonify
from flask_cors import CORS
from rq import Queue, get_current_job
from rq.job import Job
from worker import conn
from tasks import transcribe

app = Flask(__name__)
CORS(app)
q = Queue(connection=conn)

@app.route('/start_transcription', methods=['POST'])
def start_transcription():
    youtube_url = request.json['youtube_url']
    length = request.json['summary_sentences']
    keywords = request.json['keywords']
    kw_analysis_length = request.json['keyword_analysis_sentences']
    job = q.enqueue(transcribe, youtube_url, length, keywords, kw_analysis_length, job_timeout=600)
    return jsonify({'task_id': job.get_id()}), 202

@app.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    job = Job.fetch(task_id, connection=conn)

    if job.is_finished:
        return jsonify({
            'state': 'SUCCESS',
            'result': job.result,
            'status': job.meta.get('status', 'unknown')
        }), 200
    elif job.is_failed:
        return jsonify({'state': 'FAILED', 'result': None, 'status': job.meta.get('status', 'unknown')}), 500
    else:
        return jsonify({'state': 'PENDING', 'result': None, 'status': job.meta.get('status', 'unknown')}), 202

if __name__ == '__main__':
    app.run(debug=True)
