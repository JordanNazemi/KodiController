import paramiko
from pytube import YouTube
import PySimpleGUI as sg

HOST_NAME = ""
USERNAME = ""
PASSWORD = ""

def download_youtube_video(url, save_path, file_name):
    try:
        yt = YouTube(url)
    except:
        print("Connection Error")  # to handle exception

    video = yt.streams.first()
    video.download(save_path, file_name)


def place_file(ssh_client, file_name, remote_location, local_location="."):
    ftp_client = ssh_client.open_sftp()
    ftp_client.put(f"{remote_location}/{file_name}", f"{local_location}/{file_name}")
    ftp_client.close()


def remove_file(ssh_client, remote_location, file_name):
    ftp_client = ssh_client.open_sftp()
    ftp_client.remove(f"{remote_location}/{file_name}")
    ftp_client.close()


def start_video(ssh_client, remote_location, file_name):
    ssh_client.exec_command(f"kodi-send -a 'PlayMedia(storage/{remote_location}/{file_name})'")


def play_video(ssh_client):
    ssh_client.exec_command(f"kodi-send -a 'PlayerControl(Play)'")


def rewind_video(ssh_client):
    ssh_client.exec_command(f"kodi-send -a 'PlayerControl(Rewind)'")


def forward_video(ssh_client):
    ssh_client.exec_command(f"kodi-send -a 'PlayerControl(Forward)'")


def exit_video(ssh_client):
    ssh_client.exec_command(f"kodi-send -a 'PlayerControl(Stop)'")


def build_ssh():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_client.connect(hostname=HOST_NAME, username=USERNAME, password=PASSWORD)
    return ssh_client


ssh_client = build_ssh()

# ftp_client=ssh_client.open_sftp()
# filesInRemoteArtifacts = ftp_client.listdir(path="videos")
# for file in filesInRemoteArtifacts:
#     print(file)
# ftp_client.close()


# TODO add youtube URL player and openVPN connection

ssh_connect = [
    [sg.Button("Connect SSH"), sg.Text('Not connected', key='-CONNECTION-')]
]

file_control = [
    [sg.Text('Video URL'), sg.InputText(key="-URL-")],
    [sg.Text("Video file"), sg.In(size=(25, 1), enable_events=True), sg.FileBrowse(key="-FILE-")],
    [sg.Button("Send")],
    [sg.Text('No video loaded', key='-LOADED-'), sg.Button("Delete loaded video")]
]

play_button = sg.ReadFormButton('Play', bind_return_key=True)
remote_control = [
    [play_button],
    [sg.Button("Forward")],
    [sg.Button("Rewind")]
]

layout = [

    [
        sg.Column(ssh_connect),
        sg.VSeperator(),
        sg.Column(file_control),
        sg.VSeperator(),
        sg.Column(remote_control),

    ]

]

window = sg.Window("Kodi Controller", layout=layout)

downloaded_video = []
ssh_client = ""
playing = False
winding = False
file_loaded = False
while True:
    event, values = window.read()

    if event == "Connect SSH":
        ssh_client = build_ssh()
        window['-CONNECTION-'].update('Connected')

    if event == "Send":
        file = values["-FILE-"]
        url = values["-URL-"]
        if file != "":
            file_name = file.rsplit('/', 1)[-1]
            file_location = file.rsplit('/', 1)[0] + "/"

            place_file(ssh_client, file_name, file_location, "videos")
            start_video(ssh_client, "videos", file_name)
            play_video(ssh_client)

        elif url != "":
            print(url)

        window['-LOADED-'].update(f"Video loaded")
        file_loaded = True

    if event == "Delete loaded video":
        exit_video(ssh_client)
        remove_file(ssh_client, "videos", file_name)
        window['-LOADED-'].update("No video loaded")
        file_loaded = False

    if event == "Forward":
        if not winding and playing:
            winding = True
            playing = False
            play_button.Update('Stop')
            forward_video(ssh_client)

    if event == "Rewind":
        if not winding and playing:
            winding = True
            playing = False
            play_button.Update('Stop')
            rewind_video(ssh_client)

    if event == "Play":
        play_video(ssh_client)

        if winding:
            winding = False

        if playing:
            play_button.Update('Play')
            playing = False
        else:
            play_button.Update("Pause")
            playing = True

    if event == sg.WIN_CLOSED:
        if file_loaded:
            exit_video(ssh_client)
            remove_file(ssh_client, "videos", file_name)
        break

window.close()
