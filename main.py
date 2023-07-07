
import re
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, make_response
import os
import yt_dlp
import bleach
from datetime import timedelta
import requests
from requests.exceptions import RequestException

app = Flask(__name__)

MAX_VIDEO_DURATION = 10  # Maximumi i lejuar i videos ne minuta per tu konvertuar

@app.route('/', methods=['POST', 'GET'])
def index():
    error_message = None
    if request.method == 'POST':
        # Handle form submission and conversion
        pass

    return render_template('index.html', error_message=error_message)


def check_internet_connection():
    try:
        requests.get("http://www.google.com", timeout=3)
        return True
    except RequestException:
        return False


@app.route('/convert', methods=['POST'])
def convert():
    conversion_type = 'mp3'
    output_dir = 'static/downloads/'
    video_url = request.form['video_url']
    sanitized_video_url = bleach.clean(video_url, tags=[], attributes={}, protocols=['http', 'https'])

    if not check_internet_connection():
        error_message = "No internet connection. Please check your internet connection and try again."
        return render_template('index.html', error_message=error_message)


    # Validate URL format using regular expression
    url_pattern = r'^(https?://)?(www\.)?youtu\.be/([\w-]+)$'
    match = re.match(url_pattern, sanitized_video_url)
    if not match or len(match.group(3)) != 11:
        return render_template('invalid_url.html')

    ydl_opts = {
        'outtmpl': os.path.join(output_dir, conversion_type, '%(id)s.%(ext)s'),
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }],
        'ffmpeg_location': r'C:\Users\User\Desktop\ffmpeg\bin'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_id = info['id']
            duration = timedelta(seconds=info['duration'])
            if duration > timedelta(minutes=MAX_VIDEO_DURATION):
                return render_template('invalid_duration.html', max_duration=MAX_VIDEO_DURATION)
            else:
                info = ydl.extract_info(video_url, download=True)
                video_title = info['title']
                file_path = os.path.join(output_dir, conversion_type, f'{video_id}.mp3')
                return redirect(url_for('download_file', file_path=file_path, video_title=video_title))
    except yt_dlp.utils.DownloadError:
        return render_template('invalid_url.html')

    except Exception as e:
        error_message = str(e)
        return render_template('index.html', error_message=error_message)


@app.route('/download', methods=['GET'])
def download_file():
    file_path = request.args.get('file_path')
    video_title = request.args.get('video_title')

    return render_template('download.html', file_path=file_path, video_title=video_title)


@app.route('/download/<path:file_path>', methods=['GET'])
def download(file_path):
    directory_path, file_name = os.path.split(file_path)
    video_title = request.args.get('video_title')
    modified_file_name = f'{video_title}.mp3'
    headers = {
        'Content-Disposition': f'attachment; filename="{modified_file_name}"'
    }
    response = make_response(send_from_directory(directory_path, file_name, as_attachment=True))
    response.headers = headers
    return response


if __name__ == '__main__':
    app.run(debug=True)
