import yt_dlp
from pydub import AudioSegment
import os

def download():
    # Função para converter WebM para MP3 usando Pydub
    def convert_to_mp3(webm_file, mp3_file):
        audio = AudioSegment.from_file(webm_file)
        audio.export(mp3_file, format="mp3")
        print(f"Arquivo convertido para: {mp3_file}")

    # Baixar o áudio com o yt-dlp
    def download_audio(link):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',  # Nome do arquivo baseado no título
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': r'C:\Program Files\ffmpeg\bin',  # Caminho para o ffmpeg.exe
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            print("Áudio baixado com sucesso!")
        except Exception as e:
            print(f"Erro ao baixar o áudio: {e}")

    # Loop que continua até o usuário decidir parar
    while True:
        link = input("Digite o Link do Vídeo que Deseja Baixar ou 'sair' para encerrar: ")
        if link.lower() == "sair":
            print("Encerrando o processo de download.")
            break
        download_audio(link)

