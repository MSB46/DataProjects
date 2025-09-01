import os
from tkinter import messagebox
from tkinter.simpledialog import askstring
from tkinter.ttk import Progressbar

import pandas as pd
import requests
from tkinter import *
from pandastable import Table
from Recommendation import Recommendation
from idlelib.tooltip import Hovertip
import json

import spotipy
from spotipy.oauth2 import SpotifyOAuth

songs = {}

df = None
SELECTED_SONG_LIMIT = 10
client_id, client_sec = None, None

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    config = {"max_songs_preview": 10,
              "find_other_artists": 0,
              "cv_or_tdf": 0,
              "simplified": 1,
              "use_full": 0,
              "client_id": '',
              "client_sec": '',
              "same_decade": 1,
              }
    with open('config.json', 'w') as f:
        json.dump(config, f)
    with open('config.json', 'r') as f:
        config = json.load(f)
def add_item(*args):
    global df
    entry_text = entry_var.get()

    def handle_left_click_df(event):
        clicked_row = table.getSelectedRowData()
        new_id = clicked_row.index[0]
        new_name = clicked_row['name'].iloc[0]
        new_pa = clicked_row['primary_artist'].iloc[0]
        frame.destroy()
        if new_id in songs.values():
            messagebox.showerror(title="Song is already on the list",
                                 message="You already added that song to the list.")

        else:
            new_desc = f"{new_name} by {new_pa}"

            n_confirm = messagebox.askokcancel(title="Confirm", message=f"{new_desc}\n\nAdd this song to the list?")
            if n_confirm:
                songs[new_desc] = new_id
                listbox.insert(END, new_desc)

    def under_item_limit():
        if listbox.size() > SELECTED_SONG_LIMIT:
            messagebox.showerror(title="Limit exceeded",
                                 message=f"Limit is up to {SELECTED_SONG_LIMIT} songs per list.\n\nRemove a current song on the list by double clicking on it.")
            return False
        return True

    if entry_text:
        status_msg.config(text="Loading song selection...")
        status_msg.update_idletasks()
        if df is None:
            if config['use_full']:
                df = pd.read_csv("datasets/dataset_final.csv", low_memory=True)
            else:
                df = pd.read_csv("datasets/dataset_final_reduced.csv", low_memory=True)
            df.fillna("", inplace=True)
            df.index = df['id']
            df.drop('id', axis=1, inplace=True)

            df.sort_values(by=['primary_artist', 'release_date', 'name'], inplace=True)

        if under_item_limit():
            if int(radio_val.get()) == 1:
                messagebox.showinfo(title="Instruction",
                                    message="Find the song to be added and double click on its corresponding row number")
                frame = Toplevel(window.master)
                table = Table(frame, dataframe=df[
                    df['name'].str.contains(entry_text, case=False)][['release_date', 'name', 'primary_artist', 'secondary_artists']], showtoolbar=False, showstatusbar=True)
                table.show()
                table.rowheader.bind('<Double-Button-1>', handle_left_click_df)

            else:
                messagebox.showinfo(title="Instruction",
                                    message="Find the song to be added and double click on its corresponding row number")
                frame = Toplevel(window.master)
                table = Table(frame, dataframe=df[
                    (df['primary_artist'].str.contains(entry_text, case=False)) |
                    (df['secondary_artists'].str.contains(entry_text, case=False))][['release_date','name', 'primary_artist', 'secondary_artists']], showtoolbar=False, showstatusbar=True)
                table.show()
                table.rowheader.bind('<Double-Button-1>', handle_left_click_df)

    else:
        messagebox.showerror(title="Empty input", message="Please provide some input")

    # Clear the entry box for the next input
    # entry_var.set("")
    status_msg.config(text="Add another song?")


def remove_item(event):
    # Get the selected index
    selected_index = listbox.curselection()

    # Delete the selected item from the listbox
    if selected_index:
        confirmed = messagebox.askyesno(title="Confirm", message="Remove selected song from the list?")
        if confirmed:
            del songs[listbox.get(selected_index)]
            listbox.delete(selected_index)
            status_msg.config(text="Song removed. Add another?")


def make_recommendation():
    if songs:
        status_msg.config(text="Beginning search.")
        status_msg.update_idletasks()
        rec = Recommendation(df=df, ids=songs.values(), status=status_msg, progress=progressbar)
        # cv = 0, tfidf = 1
        result = rec.recommend(max_songs=config['max_songs_preview'], find_other_artists=config['find_other_artists'], use_tfidf=config['cv_or_tdf'],
                               simple=config['simplified'])
        frame = Toplevel(window)
        frame.attributes('-topmost', False)
        frame.update()
        table = Table(parent=frame, dataframe=result, showtoolbar=True, showstatusbar=True)

        # cid, csec = os.environ['CID'], os.environ['CS']
        cid, csec = config['client_id'], config['client_secret']
        table.show()

        if cid and csec:
            pl_confirmation = messagebox.askyesno(title="Confirm", message="Add the picked songs to a playlist?",
                                                  parent=table)
            if pl_confirmation:
                pl_name = askstring(title='Playlist Name', prompt='Enter a name for this playlist.',
                                    initialvalue="My Newest Playlist")

                # Replace client_id and client_secret values with your own
                auth_manager = SpotifyOAuth(client_id=cid,
                                            client_secret=csec,
                                            redirect_uri="http://example.com",
                                            scope="playlist-modify-private",
                                            show_dialog=True,
                                            cache_path="token.txt", )

                sp = spotipy.Spotify(auth_manager=auth_manager)
                token = auth_manager.get_access_token(as_dict=False)
                uid = sp.me()['id']

                URI = []
                artist_list = []
                song_list = []
                for i, r in result.iterrows():
                    artist = r['primary_artist']
                    artist_list.append(artist)
                    song = r['name']
                    song_list.append(song)
                    query = f"artist:{artist} track:{song}"
                    # query_id = f"artist:{artist} track:{song}"
                    try:
                        result = sp.search(q=query, type="track", limit=1)
                        # if not result:

                        # print(result)
                        URI.append(result['tracks']['items'][0]['uri'])
                    except (TypeError, IndexError) as e:
                        print(f"{r['id']}:{e}")
                        continue
                artist_list = list(set(artist_list))
                song_list = list(set(song_list))
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
                c_json_data = {
                    'name': pl_name,
                    'description': f'Songs recommended based on songs like {song_list} and artists like {artist_list}',
                    'public': False,
                }

                create_r = requests.post(f'https://api.spotify.com/v1/users/{uid}/playlists', headers=headers,
                                         json=c_json_data)
                # create_r.raise_for_status()
                playlist_content = create_r.json()
                pl_id = playlist_content['id']

                status_msg.config(text="Adding songs")
                status_msg.update_idletasks()
                # # Adding songs to the playlist
                a_json_data = {
                    'uris': URI,
                }

                add_songs_r = requests.post(url=f"https://api.spotify.com/v1/playlists/{pl_id}/tracks", headers=headers,
                                            json=a_json_data)
                # add_songs_r.raise_for_status()

                messagebox.showinfo(title="Success", message="Playlist created! Enjoy!", parent=table)
                status_msg.config(text="Playlist created!")

            else:
                status_msg.config(text="Cancelled. Try something else?")


def open_credits():
    credits_window = Toplevel(window.master)
    credits_window.title("Settings")
    credits_window.config()

    label_creds1 = Label(credits_window, text="Developed by Michael Saulon B")
    label_creds1.pack(pady=5, padx=5)

    label_creds2 = Label(credits_window, text="github.com/MSB46")
    label_creds2.pack(pady=5, padx=5)


def open_settings_window():
    # Create a new window for settings
    settings_window = Toplevel(window.master)
    settings_window.title("Settings")
    settings_window.config()

    label_songs = Label(settings_window, text="Songs to recommend:")
    label_songs.grid(row=1, column=1, pady=5, padx=5)
    text_num_songs = StringVar()
    text_num_songs.set(config['max_songs_preview'])
    entry_num_songs = Entry(settings_window, textvariable=text_num_songs)
    entry_num_songs.grid(row=1, column=2, columnspan=2, padx=5)
    tip_num = Hovertip(entry_num_songs, 'Maximum number of songs to include in a recommendation')

    check_artists = StringVar(settings_window, value=config['find_other_artists'])
    check1 = Checkbutton(settings_window, text="Find different artists", variable=check_artists, onvalue=1, offvalue=0)
    check1.grid(row=2, column=1, columnspan=1)
    tip1 = Hovertip(check1, 'Exclude artists of the songs added to the input from all recommendations\nLeave unchecked in unsure')

    check_tfidf = StringVar(settings_window, value=config['cv_or_tdf'])
    check2 = Checkbutton(settings_window, text="Activate TF_IDF", variable=check_tfidf, onvalue=1, offvalue=0)
    check2.grid(row=2, column=2, columnspan=1)
    tip2 = Hovertip(check2, "Recommendation adds greater weight towards the words used in categorical details instead of the frequency.\nLeave unchecked if unsure")

    check_simple = StringVar(settings_window, value=config['simplified'])
    check3 = Checkbutton(settings_window, text="Simplified df format", variable=check_simple, onvalue=1, offvalue=0)
    check3.grid(row=3, column=1, columnspan=1)
    tip3 = Hovertip(check3, 'Previews only the name, artists, and genres of recommended songs.\n\nLeave checked if unsure')

    check_use_full = StringVar(settings_window, value=config['use_full'])
    check4 = Checkbutton(settings_window, text="Use full dataframe", variable=check_use_full, onvalue=1, offvalue=0)
    check4.grid(row=3, column=2, columnspan=1)
    tip4 = Hovertip(check4, 'Allow an larger selection of songs to choose from, including songs without a recorded genre. May also lead to slower performance.\nLeave unchecked if unsure')

    check_same_decade = StringVar(settings_window, value=config['same_decade'])
    check5 = Checkbutton(settings_window, text="Recommend within decade", variable=check_same_decade, onvalue=1, offvalue=0)
    check5.grid(row=4, column=1, columnspan=2)
    tip5 = Hovertip(check5,'Only include songs released in the same decades as provided songs.')

    label_cid = Label(settings_window, text="Client ID:")
    label_cid.grid(row=5, column=1, pady=5, padx=5)
    text_cid = StringVar()
    text_cid.set(config['client_id'])
    entry_cid = Entry(settings_window, textvariable=text_cid)
    entry_cid.grid(row=5, column=2, columnspan=2, padx=5)
    tip_cid = Hovertip(entry_num_songs, 'Client ID of application used for adding songs to Spotify account')

    label_csec = Label(settings_window, text="Client Secret:")
    label_csec.grid(row=6, column=1, pady=5, padx=5)
    text_csec = StringVar()
    text_csec.set(config['client_sec'])
    entry_csec = Entry(settings_window, textvariable=text_csec)
    entry_csec.grid(row=6, column=2, columnspan=2, padx=5)
    tip_csec = Hovertip(entry_num_songs, 'Client Secret ID of application used for adding songs to Spotify account')

    def on_closing():
        global df
        try:
            config['max_songs_preview'] = int(entry_num_songs.get())
        except ValueError:
            pass
        try:
            config['client_id'] = entry_cid.get()
        except ValueError:
            pass
        try:
            config['client_secret'] = entry_csec.get()
        except ValueError:
            pass

        config['find_other_artists'] = int(check_artists.get())
        config['cv_or_tdf'] = int(check_tfidf.get())
        config['simplified'] = int(check_simple.get())
        config['use_full'] = int(check_use_full.get())
        config['same_decade'] = int(check_same_decade.get())

        # write it back to the file
        with open('config.json', 'w') as f:
            json.dump(config, f)

        if config['use_full']:
            df = pd.read_csv("datasets/dataset_ultimate.csv", low_memory=True)
        else:
            df = pd.read_csv("datasets/dataset_ultimate_reduced.csv", low_memory=True)

        df.fillna("", inplace=True)
        df.index = df['id']
        df.drop('id', axis=1, inplace=True)

        settings_window.destroy()
        # print(max_songs_preview, find_other_artists, cv_or_tdf)

    settings_window.protocol("WM_DELETE_WINDOW", on_closing)


window = Tk()
window.title("Song picker")
window.config(padx=80, pady=50)

radio_val = StringVar(window, 1)
# here is a Dictionary to create multiple buttons
options = {"Song": 1,
           "Artist": 2}

# Status message
status_msg = Label(window, text="Welcome!")
status_msg.grid(row=1, column=2, columnspan=len(options))

# Progress Bar
progressbar = Progressbar()
progressbar.grid(row=2, column=2, pady=4, columnspan=len(options))

# We will use a Loop just to create multiple
# Radiobuttons instaed of creating each button separately
for (txt, val) in options.items():
    Radiobutton(window, text=txt, variable=radio_val, value=val).grid(row=3, column=val + 1, padx=5, pady=5)

entry_var = StringVar()
entry = Entry(window, textvariable=entry_var)
entry.grid(row=4, column=2, columnspan=len(options), pady=5)

# Create a button
button = Button(window, text="Search", command=lambda: add_item())
button.grid(row=5, column=2, columnspan=len(options), pady=5)

# Create a listbox
listbox = Listbox(window)
listbox.grid(row=6, column=2, columnspan=len(options) + 1, pady=10)

# Create a button
button_r = Button(window, text="Recommend songs", command=make_recommendation)
button_r.grid(row=7, columnspan=len(options), column=2)

listbox.bind("<Double-Button-1>", remove_item)

# Create a menu
menu_bar = Menu(window)
window.config(menu=menu_bar)

# Create a "Settings" menu
settings_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Edit", menu=settings_menu)
settings_menu.add_command(label="Settings", command=open_settings_window)

about_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="About", menu=about_menu)
about_menu.add_command(label="Credits", command=open_credits)

window.bind("<Return>", add_item)
window.mainloop()