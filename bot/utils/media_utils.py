from moviepy.editor import VideoFileClip


def compress_video(input_file: str, new_file_path: str, target_resolution=(640, 360), fps=24):
    print(type(input_file), input_file)
    # Открываем видеофайл
    clip = VideoFileClip(input_file)
    output_file = f're-{input_file}'

    # Изменяем разрешение и частоту кадров
    compressed_clip = clip.resize(newsize=target_resolution).set_fps(fps)

    # Сохраняем видео в сжатом формате
    compressed_clip.write_videofile(new_file_path, codec='libx264', preset='ultrafast', audio_codec='aac')
    # compressed_clip.write_videofile(output_file, codec='libx264', preset='ultrafast', audio_codec='aac')
