"""
GUI for photo identification training.
Can be adapted to any set of photographs.
The only requirement is that each photo's filename starts with the id followed
by an underscore. Score tracking and visualisation system included.

How to:
-------
Double-click on photoID.py file. The parameter setting windows opens:
- Fill in at least the photo folder list and the number of questions.
- Previous results file (.csv), path to save results and figure are optionnal.

Classes
-------
Quizz

Functions
---------
photo_quizz
explore_folder
load_results
"""

import os
import random

import tkinter as tk
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import tkfilebrowser as tkf
from PIL import Image, ImageOps, ImageTk

tesf = ['C:/Users/benti/Desktop/2024 Osaka/Fieldwork Awaji/Kaigaishi_pics',
        'C:/Users/benti/Desktop/2024 Osaka/Fieldwork Awaji/Awaji/Photos'
        ]
test = Quizz(folders=tesf, n=3)
test.choose_photos(exclude=['ToBeSorted'])
test.start_quizz()

class Quizz:
    """
    Photo identification training.
    
    Atttributes:
    ------------
        GUI attributes:
    - window (tk.Tk): main window where quizz runs.
    - top_frame (tk.Frame): Top frame of quizz window.
    - mid_frame (tk.Frame): Mid frame of quizz window.
    - bot_frame (tk.Frame): Bottom frame of quizz window.
        Quizz information
    - folders (list of path like): folders containing the photographs.
    - resources (dict): list of available pictures per individual
    - id_list (list of str): list of individuals in the pictures
    - n (int): Number of questions in the quizz.
        Quizz progress
    - score (pd.DataFrame): table storing the quizz results.
    - q_no (int): Index of question number.
    - res (matplotlib.Figure, matplotlib.Axes): Figure showing  quizz results.
    
    Methods:
    --------
    __init__: Creates instance
    choose_photos: Finds and sorts photos within the provided folders
    build_score: Creates or checks the data frame for score tracking
    start_quizz: launches quizz
    next_question: ends question and assess whether to display another one or
        to end the quizz
    end_quizz: ends the quizz
    show_results: Builds figure to show quizz results and optionally displays
        the figure
    save_results: Saves result figures and/or score table.
    select_folders: utility to access file explorer on button click
    select_scores: utility to access file explorer on button click
    """
    
    def __init__(self, folders=None, n=None, score=None):
        """
        Initialise quizz instance from photo folder and parent window.
        Parametrisation of the quizz via command line or GUI.
        Arguments
        ---------
        - folders (list of path like): where the photos are stored
        - n (int): number of questions to ask
        - previous (pd.DataFrame): Previous quizz scores to load
        """
        
        self.window = tk.Tk()
        # Scale window to screen size.
        w = self.window.winfo_screenwidth()
        h = self.window.winfo_screenheight()
        self.window.geometry('{}x{}'.format(str(w-10), str(h-10)))
        self.window.title('DO NOT CLOSE ME!')
        self.folders = folders
        self.n = n
        self.score = score
        self.res = None  # Required if save_results called before show_results.
        
        # If necessary information not provided, create GUI.
        if not folders or not n:
            root = tk.Tk()
            root.title('Config window')
            if not folders:  # Ask user for photo folders.
                self.folders = []  # Required for append later
                frame1 = tk.Frame(root)
                frame1.pack()
                folder_label = tk.Label(frame1, text="Photo folders:")
                folder_label.pack(side=tk.LEFT)
                folder_button = tk.Button(frame1, text='Select',
                                          command=self.select_folders)
                folder_button.pack(side=tk.LEFT)
            if not n:  # Ask user for number of questions.
                frame2 = tk.Frame(root)
                frame2.pack()
                n_label = tk.Label(frame2, text="Number of questions:")
                n_label.pack(side=tk.LEFT)
                n_var = tk.StringVar()
                n_var.set(20)
                n_entry = tk.Entry(frame2, textvariable=n_var)
                n_entry.pack(side=tk.LEFT)
            if not score:  # Ask user for previous scores to load
                frame3 = tk.Frame(root)
                frame3.pack()
                mat_label = tk.Label(frame3, text="Previous score (optional):")
                mat_label.pack(side=tk.LEFT)
                mat_button = tk.Button(frame3, text='Select',
                                       command=self.select_scores)
                mat_button.pack(side=tk.LEFT)
            #Go button!
            frame4 = tk.Frame(root)
            frame4.pack()
            go_button = tk.Button(frame4, text='Go', command=root.quit)
            go_button.pack(pady=2, padx=5, side=tk.LEFT)
            # Get window running.
            root.mainloop()
            if not n:
                self.n = int(n_var.get())
            root.destroy()
    
    
    def choose_photos(self, ff='.JPG', exclude=None):
        """
        Explore the photo folders provided by the users and gets a list of
        photos and individuals. Can remove unwnated folder or individuals from
        the list
        Arguments
        ---------
        - exclude (list of str): string found in filenames to be removed. All
            pictures which path include exclude elements will be removed from
            the quizz
        """
        pic_list = []
        id_list = []
        for i in self.folders:
            inds, photos = explore_folder(i, ff=ff, exclude=exclude)
            pic_list += photos
            id_list += inds
        # Get list of individuals ids in alphabetical order.
        self.id_list = sorted(list(set(id_list)))
        # Stores photos by individuals in a dictionnary.
        self.resources = {}
        for i in self.id_list:
            self.resources[i] = [pic for pic in pic_list if i in pic]
        self.build_score()
    
    
    def build_score(self):
        """
        Build pd.Dataframe with individual names as index to score
        identification results. Checks if names in self.id_list are already in
        dataframe if previous scores have been loaded.        
        """
        
        if not self.score:  # Build score dataframe from scratch.
            self.score = pd.DataFrame(data=np.zeros(shape=(len(self.id_list),
                                                           len(self.id_list) + 1
                                                           )
                                                    ),
                                      index=self.id_list,
                                      columns=self.id_list + ['Correct'],
                                      dtype=int
                                      )
        else:  # Check for the presence of each individual in previous score.
            for i in self.id_list:
                if i not in self.score.index:
                    # Add row with id i at bottom.
                    row = pd.Series(data=np.zeros(shape=(self.score.shape[1])),
                                    index=self.score.columns, dtype=int)
                    self.score.loc[i] = row
                    # Add column with individual name.
                    col = pd.Series(data=np.zeros(self.score.shape[0]),
                                    index=self.score.index, dtype=int)
                    self.score.loc[:, i] = col
            # Reorder lines
            self.score=self.score.sort_index()
            # Reorder columns to keep 'Correct at the end'
            cols = self.score.columns
            new_cols = sorted([c for c in cols if c != 'Correct']) + ['Correct']
            self.score = self.score[new_cols]
    
    
    def start_quizz(self):
        """
        Starts the photo identification quizz.
        """
        self.q_no = 0
        # Create three frames:
        # Top frame to display question.
        self.top_frame = tk.Frame(self.window)
        self.top_frame.pack()
        # Mid frame to display photo.
        self.mid_frame = tk.Frame(self.window)
        self.mid_frame.pack()
        # Bottom frame for input and validation button.
        self.bot_frame = tk.Frame(self.window)
        self.bot_frame.pack()
        
        # Make a start button.
        start_button = tk.Button(self.mid_frame, text="Start",
                                 command = self.next_question)
        start_button.pack(padx='3m', pady='1m')
    
    
    def next_question(self):
        """
        Empties the frames of the window, then starts the next question.
        """
        
        self.q_no += 1
        
        # Empties all the frames of the window.
        tkclear(self.top_frame)
        tkclear(self.mid_frame)
        tkclear(self.bot_frame)
        
        if self.q_no <= self.n:
            Question(self)
        else:
            self.end_quizz()
    
    
    def end_quizz(self):
        """
        After the last question of the quizz, displays an ending message
        and closes the window.
        """
        n_correct = sum(self.score.loc[:, 'Correct'])
        n_total = np.sum(self.score.values) - n_correct
        success = round(n_correct / n_total * 100)
        
        # End message.
        msg = 'Test finished !\nYour overall success rate is {}%'.format(success)
        label = tk.Label(self.top_frame, text=msg)
        label.pack()
        
        # Button to show and save results.
        button1 = tk.Button(self.mid_frame, text='Show results',
                            command=self.show_results)
        button1.pack()
        button2 = tk.Button(self.mid_frame, text='Save results',
                            command=self.save_results)
        button2.pack()
        
        # End button to close window.
        button = tk.Button(self.bot_frame, text='End', command=self.window.destroy)
        button.pack()
    
    
    def show_results(self, cmap=plt.cm.Blues, show=True):
        """
        Displays the current score matrix with a color code.
        Arguments
        ---------
        cmap (color map): color map to use. Default is Blues. See matplotlib
            for details.
        show (bool): whether to show the plot or not. Default is True and
            shows the plot.
        """
        
        # Keep only individuals with a quizz record.
        idx_row = [i for i in self.score.index if sum(self.score.loc[i] > 0)]
        idx_col = [i for i in self.score.columns if sum(self.score.loc[:, i]) > 0]
        if 'Correct' not in idx_col:
            idx_col.append('Correct')
        score_data = self.score.loc[idx_row, idx_col]
        
        # Transform values in proportion of id per individual for coloring.
        score_colors = pd.DataFrame(data=score_data.copy(), dtype=float)
        for ind in score_colors.index:
            score_colors.loc[ind] /= sum(score_colors.loc[ind].iloc[:-1])
            # Remove last column which scores correct answers.
        
        # Build figure and show id matrix.
        fig = plt.figure(figsize=score_colors.shape)
        ax = fig.add_subplot()
        ax.imshow(score_colors, cmap=cmap, interpolation='nearest')
        
        # Add number of answers in each square.
        rows, cols = score_data.shape
        for r in range(rows):
            for c in range(cols):
                ax.text(x=c, y=r, s=str(round(score_data.iloc[r, c],2)),
                        va='center', ha='center')
        
        # Display ids as axis tick labels.
        ax.set_yticks(range(rows))        
        ax.set_yticklabels(score_data.index)
        ax.set_xticks(range(cols))     
        ax.set_xticklabels(score_data.columns, rotation=90)
        
        # Place axis labels.
        ax.set_ylabel('True identity')
        ax.set_xlabel('Given answers')
        
        self.res = (fig, ax)
        if show:
            plt.show()
        else:
            plt.close()
    
    
    def save_results(self, figname='QuizzResultsFig.png',
                     csvname='QuizzScore.csv'):
        """
        Saves the identification quizz results in a csv file and the results
        plot in an image.
        Arguments
        ---------
        figname (path like): Name of the image to save the results plot.
            None does not save the plot.
        csvname (path like): Name to save the score table. None does not save
            the score table.
        """
        if figname:
            if not self.res:  # Figure not built.
                self.show_results(show=False)
            fig = self.res[0]
            fig.savefig(figname, bbox_inches='tight')
        
        if csvname:
            self.score.to_csv(csvname)
    
    
    def select_folders(self):
        """
        Button command to open file explorer and select folders containing photos.
        If folders are not at the same locations, use the button several times.
        """
        
        dirs = tkf.askopendirnames()
        self.folders.append(dirs[0])
    
    
    def select_scores(self):
        """
        Button command to open the csv file containing the previous scores to 
        load. Previous scores must be dataframes in csv format/
        """
        
        score = tk.askopenfilename()
        self.scores = pd.read_csv(score)


class Question:
    """
    Question of the photo identification quizz.
    
    Attributes
    ----------
    quizz (Quizz): Parent quizz which question originates from
    ind (str): Ground truth name of individual displayed
    photo (path like): path to the displayed photo
    answer (tk.StringVar): answer provided by user
    notif (tk.Tk): Feedback window once answer is verified
    
    Methods
    -------
    __init__: Creates instance
    check_answer: Compares given answer to ground truth
    clicked: Utility to close question feedback and continue quizz
    """
    
    def __init__(self, quizz, ind=None, photo=None):
        """
        Creates a photo identification question.
        Displays the question on the given window.
        """
        
        self.quizz = quizz
        
        if not ind:  # If no individual input, choose randomly from quizz data.
            ind = random.choice(self.quizz.id_list)
        self.ind = ind
        
        if not photo:  # Idem.
            photo = random.choice(self.quizz.resources[self.ind])
        self.photo = photo
        
        # Display question in quizz window top frame.
        question = tk.Label(self.quizz.top_frame, text='Who is this?')
        question.pack(pady='1m')
        # Display photo in quizz window mid frame.
        img_label = tk.Label(self.quizz.mid_frame)
        img_label.pack()
        im = Image.open(self.photo)
        # Make photo square and fit to window size.
        size_str = self.quizz.window.geometry().split('+')[0].split('x')
        winsize = [int(i) for i in size_str]
        im_size = round(2/3 * min(winsize))
        im_pad = ImageOps.pad(im, size=(max(im.size), max(im.size)),
                              color=(100, 100, 100))
        im_fit = ImageOps.fit(im_pad, size=(im_size, im_size))
        # Transfer photo into tkinter compatible format.
        im_tk = ImageTk.PhotoImage(im_fit)
        img_label.image = im_tk
        img_label['image'] = img_label.image
        # Put input box and buttons in bottom frame.
        self.answer = tk.StringVar()
        self.answer.set('Asari')
        input_box = tk.Entry(self.quizz.bot_frame, textvariable=self.answer)
        input_box.pack(side=tk.LEFT, padx=50)
        button = tk.Button(self.quizz.bot_frame, text="Check answer",
                           command=self.check_answer)
        button.pack(side=tk.LEFT)
        self.quizz.window.title("Question {} on {}".format(self.quizz.q_no, self.quizz.n))
        
        
    def check_answer(self):
        """
        Check given answer versus ground truth.
        """
        
        guess = self.answer.get()
        if guess.lower() == self.ind.lower():  # Right answer.
            txt = "Well done!"
            # Updates score.
            self.quizz.score.loc[self.ind, self.ind] += 1
            self.quizz.score.loc[self.ind, 'Correct'] += 1
        else:
            txt = "Wrong! Answer was {}, not {}".format(self.ind, guess)
            try:
                self.quizz.score.loc[self.ind, guess] += 1
            except KeyError:  # Guess not in id_list or typo.
                txt += '\n{} is not even in the list...'.format(guess)
        
        # Give feedback in new window.
        self.notif = tk.Tk()
        message = tk.Label(self.notif, text=txt)
        message.pack(padx='3m', pady='3m')
        button = tk.Button(self.notif, text="Continue", command=self.clicked)
        button.pack()
        self.notif.mainloop()
        
        
    def clicked(self):
        """
        Closes notif window and runs quizz.next_question.
        """
        
        self.notif.destroy()
        self.quizz.next_question()


def photo_quizz(photo_folder, n_question, id_matrix=None):
    """
    Main function to run the photo-identification training quizz.
    
    Arguments:
    ----------
    win (tk.Tk):
        The window in which to run the quizz.
    n_question (int):
        Number of questions to ask.
    photo_folder (str):
        Path to the folder containing the quizz photos. The name of the files
        must start with the identity, followed by an underscore.
    id_matrix (pd.DataFrame):
        Identification matrix to store the quizz results. Default is None and
        builds an empty matrix.
    
    Returns:
    --------
    id_matrix (pd.DataFrame):
        The identication matrix with the quizz results.
    """
    
    root = tk.Tk()
    # Initialise photo quizz.
    quizz = Quizz(root, photo_folder, n_question, id_matrix=id_matrix)
    root.mainloop()
    
    return quizz.id_matrix

def explore_folder(folder, ff='.JPG', exclude=None):
    """
    Explore the folder and all subfolder looking for pictures.
    Arguments
    ---------
    - folder (path like): the folder to explore
    - ff (str): the format of the pictures to look for. Default is '.JPG'
    - exclude (list of str): names or extract of folder names to exclude from
        the search.
    Returns
    -------
    - ind_list (list of str): individuals portrayed in the pictures, sorted in
        alphabetical order
    - pic_list (list of path like): pictures in the folder and subfolders.
    """
    
    # Get all pictures and list of individuals in pictures.
    pic_list = []
    inds = []
    for path, subfolders, files in os.walk(folder):
        if all([elt not in path for elt in exclude]):
            for f in files:
                if ff in f:  # if file is a picture.
                    pic_list.append(os.path.join(path, f))
                    inds.append(f.split('_')[0])
    
    # Get ordered set of individuals.
    ind_list = sorted(list(set(inds)))
    
    return ind_list, pic_list

def tkclear(frame):
    """
    Clears all elements within a tkinter frame.
    """
    for elt in frame.winfo_children():
        elt.destroy()

def load_results(fileName):
    """
    Reads previous identification results from csv file.
    """
    id_matrix = pd.read_csv(fileName, index_col=0)
    return id_matrix

# Behaviour if file is double-clicked.
if __name__ == '__main__':
    folder, n, mat, fn1, fn2 = param_window()
    if mat:
        mat = load_results(mat)
    id_mat = photo_quizz(folder, n, id_matrix=mat)
    fig, ax = show_results(id_mat, fname=fn2)
    if fn1:
        save_results(id_mat, fn1)
    plt.show()
