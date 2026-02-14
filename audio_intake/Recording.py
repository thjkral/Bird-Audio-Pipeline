"""
Class to store recording info
"""
from tinytag import TinyTag
from datetime import datetime, timedelta
import hashlib
import os

class Recording:
    def __init__(self, old_file_path, filename):
        self.old_file_path = old_file_path
        self.filename = filename
        self._parse_filename_to_metadata()
        self._get_audio_metadata()
        self.stop_time = self._calculate_stop_time()
        self.rec_id = self._generate_hashed_id()

    def _get_audio_metadata(self):
        '''
        Sets metadata fields of the audio using the tinytag module. This information is used to monitor quality.
        '''
        try:
            tag = TinyTag.get(self.old_file_path)
            self.duration = tag.duration
            self.filesize = tag.filesize
            self.samplerate = tag.samplerate
            self.channels = tag.channels
            self.bitdepth = tag.bitdepth
        except Exception as e:
            print(f"Error extracting metadata: {e}")

    def _parse_filename_to_metadata(self):
        '''
        The filename of each recording contains the name of the microphone, the time when the recording was started, and
        the date. This function parses the filename and assigns them to metadata fields.
        '''
        filename_extention_removed = self.filename.replace('.wav', '')
        file_metadata = filename_extention_removed.split('_')

        self.mic_id = file_metadata[0]
        self.rec_date = datetime.strptime(file_metadata[1], '%Y%m%d').date()
        self.start_time = datetime.strptime(file_metadata[2], '%H%M%S').time()

    def _calculate_stop_time(self):
        '''
        Adds the duration of the recording to the start time. This can later be used to validate recordings.
        '''
        dt = datetime.combine(self.rec_date, self.start_time)
        stop_time = dt + timedelta(seconds=self.duration)
        return stop_time.time()

    def _generate_hashed_id(self):
        hashtext = self.filename + str(self.rec_date) + str(self.start_time) + self.mic_id
        return hashlib.md5(hashtext.encode("utf-8")).hexdigest()

    def set_new_filepath(self, save_location):
        year = str(self.rec_date.year)
        month = str(self.rec_date.month)

        self.new_file_path = os.path.join(save_location, year, month, self.filename)

    def __str__(self):
        return f'Recording details:\n' \
               f'ID= {self.rec_id}\n' \
               f'filepath= {self.old_file_path}\n' \
               f'filename= {self.filename}\n' \
               f'mic_id= {self.mic_id}\n' \
               f'date= {self.rec_date}\n' \
               f'start_time= {self.start_time}\n' \
               f'stop_time = {self.stop_time}\n' \
               f'duration (sec)= {self.duration}\n' \
               f'size (bytes)= {self.filesize}\n' \
               f'samplerate= {self.samplerate}\n' \
               f'channels= {self.channels}\n' \
               f'bitdepth= {self.bitdepth}'
