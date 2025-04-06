from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty
from pygame import mixer
from mutagen.mp3 import MP3
from kivy.clock import Clock
import os


from jnius import autoclass  # Import Pyjnius for Android compatibility


class MediaPlayer(BoxLayout):
    songs = ListProperty()  # A property to store the list of song file paths

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        mixer.init()

        # Load songs from the directory
        self.songs = self.load_songs()
        if self.songs:
            self.update_song_list()

        self.playing = False
        self.is_paused = False
        self.current_index = 0
        self.timer = None

    def load_songs(self):
        songs = []
        try:
            # Access MediaStore's audio content
            Environment = autoclass('android.os.Environment')
            Context = autoclass('android.content.Context')
            Uri = autoclass('android.net.Uri')
            MediaStore = autoclass('android.provider.MediaStore')
            activity = autoclass('org.kivy.android.PythonActivity').mActivity

            # Create a content resolver to query audio files
            content_resolver = activity.getContentResolver()
            uri = MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
            projection = [MediaStore.Audio.Media.DATA]  # Retrieve file paths

            # Query all .mp3 files from device storage
            cursor = content_resolver.query(uri, projection, None, None, None)
            if cursor:
                while cursor.moveToNext():
                    file_path = cursor.getString(0)  # Get file path from the cursor
                    if file_path.endswith('.mp3'):  # Check for .mp3 files
                        songs.append(file_path)
                cursor.close()

        except Exception as e:
            print(f"Error accessing songs: {e}")

        return songs


    def update_song_list(self):
        # Populate the RecycleView with song names
        self.ids.song_list.data = [{'text': os.path.basename(song), 'on_press': lambda x=song: self.play_selected_song(x)} for song in self.songs]

    def play_selected_song(self, song_path):
        self.stop_timer()
        # Load and play the selected song
        self.current_index = self.songs.index(song_path)
        mixer.music.load(song_path)
        audio = MP3(song_path)
        self.ids.seekbar.max = audio.info.length
        self.ids.seekbar.value = 0
        self.ids.metadata_label.text = f"Playing: {os.path.basename(song_path)}"
        mixer.music.play()
        self.start_timer()
        self.playing = True
        self.is_paused = False
        self.ids.play_pause_button.text = "⏸ Pause"

    def play_pause_song(self):
        if self.playing:
            if self.is_paused:
                mixer.music.unpause()
                self.is_paused = False
                self.ids.play_pause_button.text = "⏸ Pause"
            else:
                mixer.music.pause()
                self.is_paused = True
                self.ids.play_pause_button.text = "⏯ Play"
        else:
            self.play_selected_song(self.songs[self.current_index])

    def next_song(self):
        self.current_index = (self.current_index + 1) % len(self.songs)
        self.play_selected_song(self.songs[self.current_index])

    def prev_song(self):
        self.current_index = (self.current_index - 1) % len(self.songs)
        self.play_selected_song(self.songs[self.current_index])

    def start_timer(self):
        self.timer = Clock.schedule_interval(self.update_seekbar_value, 0.2)

    def stop_timer(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None

    def update_seekbar_value(self, dt):
        if self.playing and not self.is_paused:
            self.ids.seekbar.value += 0.2
            if self.ids.seekbar.value > self.ids.seekbar.max:
                self.ids.seekbar.value = self.ids.seekbar.max
                self.next_song()

    def resume_at_seekbar(self, slider, touch):
        if slider.collide_point(touch.x, touch.y):
            if self.playing:
                seek_pos = slider.value
                mixer.music.stop()
                mixer.music.play(start=seek_pos)
                print(f"Resuming playback at {seek_pos} seconds")


class MediaPlayerApp(App):
    def build(self):
        return MediaPlayer()


if __name__ == "__main__":
    MediaPlayerApp().run()