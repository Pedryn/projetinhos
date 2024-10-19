import yt_dlp

def download():
    # Loop que continua até o usuário decidir parar
    while True:
        link = input("Digite o Link do Vídeo que Deseja Baixar ou 'sair' para encerrar: ")
        if link.lower() == 'sair':
            print("Encerrando o processo de download.")
            break

        # Configurações de download
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
        }

        # Baixa o vídeo
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Baixando:", link)
                ydl.download([link])
            print("Download Concluído!")
        except Exception as e:
            print(f"Erro ao baixar o vídeo: {e}")

