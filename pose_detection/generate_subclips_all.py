import os
from moviepy.editor import VideoFileClip

class generate_subclips():
    def __init__(self):
        self.start_times = [13.0, 1.5, 0.5, 0.5, 1.0, 0.5, 1.0, 6.5, 0, 0.5]
        self.min_time = 1000.0
        self.extracted_clips_array = []
        self.audioclip = None

    def edit_video_sink(self, videos_path):
        #                0  1  2  3  4  5   6  7  8  9  10
        # VIDEO SONG START TIME ARRAY
        # VIDEO ALIGNMENT -> SLICE START TIME

        for i in range(len(os.listdir(videos_path))):
            video_path = os.path.join(videos_path, sorted(os.listdir(videos_path))[i])
            clip = VideoFileClip(video_path)
            clip = clip.subclip(self.start_times[i], clip.duration)
            self.extracted_clips_array.append(clip)

            if self.min_time > clip.duration:
                self.audioclip = clip.audio
                self.min_time = clip.duration

        # print(len(extracted_clips_array))


    def make_subclips(self):
        for i in range(33):
            os.mkdir("subclips/" + str(i * 10))

        for video_idx in range(len(self.extracted_clips_array)):
            try:
                print("make subclip...")
                t = 0
                while t <= self.min_time + 10:
                    # 10 sec.
                    cur_t = t
                    next_t = min(t + 10, self.min_time)

                    clip = self.extracted_clips_array[video_idx].subclip(cur_t, next_t)
                    clip.write_videofile("subclips/" + str(t) + "/" + str(t) + " " + str(video_idx) + ".mp4")
                    t = next_t
            except IndexError:
                pass


    def get_extracted_clip_list(self):
        return self.extracted_clips_array

    def run(self):
        self.edit_video_sink("video/")
        self.make_subclips()

if __name__ == "__main__":
    k = generate_subclips()
    k.run()