"""
GUI for photo identification training.
Can be adapted to any set of photographs.
The only requirement is that each photo's name must start with the id followed
by an underscore.
Score tracking and visualisation system included.

Classes
-------
Quizz
Question

Functions
---------
explore_folder
tkclear
load_results
photo_quizz
param_window
"""

import os
import random

import tkinter as tk
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import tkfilebrowser as tkf
from PIL import Image, ImageOps, ImageTk


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
    - excl (list of str): list of exclusion terms for photo selection.
    - incl (list of str): list of inclusion terms for photo selection.
    - resources (dict): list of available pictures per individual
    - id_list (list of str): list of individuals in the pictures
    - n (int): Number of questions in the quizz.
        Quizz progress
    - score (pd.DataFrame): table storing the quizz results.
    - q_no (int): Index of question number.
    - res (matplotlib.Figure, matplotlib.Axes): Figure showing  quizz results.
        Save parameters
    - fig (path like): Location to save the figure of the quizz results.
    - tab (path like): Location to save the table of the quizz results.
    
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
    
    def __init__(self, folders=[], excl=None, incl=None,
                 score=None, fig=None, tab=None
                 ):
        """
        Initialise quizz instance.
        Parametrisation can be done from the GUI of param_window.
        
        Arguments
        ---------
        - folders (list of path like): path to where the photos are stored.
            Mutliple folders can be selected.
        - excl (list of str): list of exclusion terms for photo selection.
        - incl (list of str): list of inclusion terms for photo selection.
        - score (pd.DataFrame): Previous quizz scores to load. Lines and
            columns will be added for individuals present in the test but
            absent from the input score table.
        - fig (path like): Location to save the figure. Default is None and
            does not save the figure. Initialised now for easier set up of
            tk.Button commands.
        - tab (path like): Location to save the figure. Default is None and
            does not save the figure. Initialised now for easier set up of
            tk.Button commands.
        """
        
        self.folders = folders
        self.incl = incl
        self.excl = excl
        self.n = None
        self.score = score
        self.fig = fig  # Store location to save figure.
        self.tab = tab  # Store location to save table.
        self.res = None  # Required if save_results called before show_results.
    
    
    def choose_photos(self, ff='.JPG', incl=None, excl=None):
        """
        Explore the photo folders provided by the users and gets a list of
        photos and individuals. Can remove unwanted folder or individuals from
        the list. Can limit selection to certain folders and files.
        
        Arguments
        ---------
        - ff (self): Photo format to look for in the folders.
            Default is '.jpg'.
        - incl (list of str): string found in filenames to be included. All
            picture paths must include one of the elements of the list to be 
            included in the quizz. OVERRIDES INITIALISATION IF GIVEN.
        - excl (list of str): string found in filenames to be removed. All
            pictures which path include one of the elements of the list will 
            be removed from the quizz. OVERRIDES INITIALISATION IF GIVEN.
        """
        
        if incl is not None:
            self.incl = incl
        if excl is not None:
            self.excl = excl
        
        pic_list = []
        id_list = []
        for i in self.folders:
            inds, photos = explore_folder(i, ff=ff,
                                          incl=self.incl, excl=self.excl
                                          )
            pic_list += photos
            id_list += inds
        
        # Get list of individuals ids in alphabetical order.
        self.id_list = sorted(list(set(id_list)))
        # Stores photos by individuals in a dictionnary.
        self.resources = {}
        for i in self.id_list:
            self.resources[i] = [pic for pic in pic_list if i in pic]
        
        # Build or update score table based on photo selection.
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
                                      dtype=float
                                      )
        else:  # Check for the presence of each individual in previous score.
            for i in self.id_list:
                if i not in self.score.index:
                    # Add row with id i at bottom.
                    row = pd.Series(data=np.zeros(shape=(self.score.shape[1])),
                                    index=self.score.columns, dtype=float)
                    self.score.loc[i] = row
                    # Add column with individual name.
                    col = pd.Series(data=np.zeros(self.score.shape[0]),
                                    index=self.score.index, dtype=float)
                    self.score.loc[:, i] = col
            # Reorder lines
            self.score=self.score.sort_index()
            # Reorder columns to keep 'Correct at the end'
            cols = self.score.columns
            new_cols = sorted([c for c in cols if c != 'Correct']) + ['Correct']
            self.score = self.score[new_cols]
    
    
    def start_quizz(self, n=None):
        """
        Starts the photo identification quizz.
        
        Argument
        --------
        n (int): Number of questions to ask in the quizz.
        """
        
        # Create quizz GUI window and scale it to screen size.
        self.window = tk.Tk()
        w = self.window.winfo_screenwidth()
        h = self.window.winfo_screenheight()
        self.window.geometry('{}x{}'.format(str(w-10), str(h-10)))
        self.window.title('DO NOT CLOSE ME!')
        
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
        
        if n is not None:
            self.n = n
            self.q_no = 0
            # Make a start button.
            start_button = tk.Button(self.mid_frame, text="Start",
                                     command = self.next_question)
            start_button.pack(padx='3m', pady='1m', expand=True)
    
    
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
        label.pack(side=tk.LEFT)
        
        # Button to show and save results.
        button1 = tk.Button(self.mid_frame, text='Show results',
                            command=self.show_results)
        button1.pack(side=tk.LEFT)
        button2 = tk.Button(self.mid_frame, text='Save results',
                            command=self.save_results)
        button2.pack(side=tk.LEFT)
        
        # End button to close window.
        button = tk.Button(self.bot_frame, text='End', command=self.window.destroy)
        button.pack(side=tk.LEFT)
    
    
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
        idx_col = [i for i in self.score.columns
                   if (i in idx_row or sum(self.score.loc[:, i]) > 0)
                   ]
        if 'Correct' not in idx_col:
            idx_col.append('Correct')
        score_data = self.score.loc[idx_row, idx_col]
        
        # Transform values in proportion of id per individual for coloring.
        score_colors = score_data.copy()
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
            for c in range(cols-1):
                txt = str(int(score_data.iloc[r, c]))
                ax.text(x=c, y=r, s=txt, va='center', ha='center')
            txt = str(int(100*round(score_colors.iloc[r, cols-1], 2))) + '%'
            ax.text(x=cols-1, y=r, s=txt, va='center', ha='center')
        
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
    
    
    def save_results(self, figname=None, csvname=None):
        """
        Saves the identification quizz results in a csv file and the results
        plot in an image.
        Arguments
        ---------
        figname (path like): Name of the image to save the results plot.
            Overrides the initialisation parameter.
        csvname (path like): Name to save the score table.
            Overrides the initialisations parameter.
        """
        
        # Updates output locations
        if figname:
            self.fig = figname
        
        if csvname:
            self.tab = csvname
        
        # Save results if output locations available.
        if self.fig:
            if not self.res:  # Figure not built.
                self.show_results(show=False)
            self.res[0].savefig(self.fig, bbox_inches='tight')
        
        if self.tab:
            self.score.to_csv(self.tab)
    
    
    def select_folder(self):
        """
        Button command to open file explorer and select a photo folder.
        """
        
        f = tkf.askopendirname()
        self.folders.append(f)
    
    
    def select_score(self):
        """
        Button command to open the csv file containing the previous scores to 
        load. Previous scores must be dataframes in csv format.
        """
        
        score = tkf.askopenfilename()
        self.scores = pd.read_csv(score)
    
    
    def config(self):
        """
        GUI for quizz parametrisation. Called if Quizz instance is created without
        arguments.
        
        Returns
        -------
        - folders (list of path like): Path to folders when photos ar stored.
        - incl_lst (list of str): list of inclusion terms for photo selection.
        - excl_lst (list of str): list of exclusion terms for photo selection.
        - tab (pd.DataFrame): previous score table.
        - out_f (path like): location to save quizz results figure. None does not
            save the figure.
        - out_t (path like): location to save quizz results table. None does not
            save the figure.
        """
        
        # Open window and prompts user to enter information.
        w = tk.Tk()
        w.title('Set up photo identification quizz:')
        w.geometry('500x300')
        
        # Ask for location of photo folders. Folder is added to self.folders
        # upon each click.
        f1 = tk.Frame(w)
        f1.pack(pady='1m')
        l1 = tk.Label(f1, text='Photo folders (click several times to use multiple folders): ')
        l1.pack(side=tk.LEFT)
        b1 = tk.Button(f1, text='Browse', command=self.select_folder)
        b1.pack(side=tk.LEFT)
        
        # Ask for list of inclusion terms (optional).
        f2 = tk.Frame(w)
        f2.pack(pady='1m')
        l2 = tk.Label(f2, text='Inclusion terms (optional): ')
        l2.pack(side=tk.LEFT)
        incl_var = tk.StringVar()
        incl_var.set('')
        e2 = tk.Entry(f2, textvar=incl_var)
        e2.pack(side=tk.LEFT)
        
        # Ask for list of exclusion terms (optional).
        f3 = tk.Frame(w)
        f3.pack(pady='1m')
        l3 = tk.Label(f3, text='Exclusion terms (optional): ')
        l3.pack(side=tk.LEFT)
        excl_var = tk.StringVar()
        excl_var.set('')
        e3 = tk.Entry(f3, textvar=excl_var)
        e3.pack(side=tk.LEFT)
        
        # Ask for location of previous score. Score file is opened and loaded
        # in self.score.
        f4 = tk.Frame(w)
        f4.pack(pady='1m')
        l4 = tk.Label(f4, text='Previous score file (optional): ')
        l4.pack(side=tk.LEFT)
        b4 = tk.Button(f4, text='Browse', command=self.select_score)
        b4.pack(side=tk.LEFT)
        
        # Ask for path to result figure (optional).
        f5 = tk.Frame(w)
        f5.pack(pady='1m')
        l5 = tk.Label(f5, text='Save result figure location (optional): ')
        l5.pack(side=tk.LEFT)
        f_var = tk.StringVar()
        f_var.set('')
        e5 = tk.Entry(f5, textvar=f_var)
        e5.pack(side=tk.LEFT)
        
        # Ask for path to result score (optional).
        f6 = tk.Frame(w)
        f6.pack(pady='1m')
        l6 = tk.Label(f6, text='Save score table location (optional): ')
        l6.pack(side=tk.LEFT)
        t_var = tk.StringVar()
        t_var.set('')
        e6 = tk.Entry(f6, textvar=t_var)
        e6.pack(side=tk.LEFT)
        
        # Add button to enter input.
        f7 = tk.Frame(w)
        f7.pack(pady='5m')
        b7 = tk.Button(f7, text='Set up quizz', command=w.quit)
        b7.pack(side=tk.LEFT, ipadx='3m', ipady='1m')
        
        w.mainloop()
        
        # Upon button click, retrieve input and close window.
        # List of inclusion terms.
        tmp = incl_var.get()
        if tmp != '':
            lst = tmp.split(',')  # Split list elements.
            self.incl = [i.replace(' ', '') for i in lst]  # Remove spaces.
        # List of exclusion terms.
        tmp = excl_var.get()
        if tmp != '':
            lst = tmp.split(',')  # Split list elements.
            self.excl = [i.replace(' ', '') for i in lst]  # Remove spaces.
        # Location to save results figure.
        out_f = f_var.get()
        if out_f != '':
            self.fig = out_f
        # Location to save quizz score.
        out_t = t_var.get()
        if out_t != '':
            self.tab = out_t
        
        w.destroy()


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
        img_label.pack(side=tk.LEFT)
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
        if self.quizz.n:  # Question part of a quizz.
            self.quizz.window.title("Question {} on {}".format(self.quizz.q_no,
                                                               self.quizz.n))
        else:
            self.quizz.window.title("Standalone question")
    
    
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
        Closes feedback window and continue quizz or closes question.
        """
        
        self.notif.destroy()
        if self.quizz.n:  # Question is part of a quizz.
            self.quizz.next_question()
        else:  # Standalone question.
            tkclear(self.quizz.top_frame)
            tkclear(self.quizz.mid_frame)
            tkclear(self.quizz.bot_frame)


def explore_folder(folder, ff='.JPG', incl=None, excl=None):
    """
    Explore the folder and all subfolder looking for pictures.
    
    Arguments
    ---------
    - folder (path like): the folder to explore
    - ff (str): the format of the pictures to look for. Default is '.JPG'
    - incl (list of str): names or extract of folder names to include in
        the search.
    - excl (list of str): names or extract of folder names to exclude from
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
        for file in files:
            f = os.path.join(path, file)
            dec = check_file(f, incl, excl)
            if dec:
                pic_list.append(f)
                inds.append(file.split('_')[0])
    
    # Get ordered set of individuals.
    ind_list = sorted(list(set(inds)))
    
    return ind_list, pic_list

def check_file(filepath, incl, excl):
    """
    Check if file path contains elements from inclusion and exclusion list.
    Return boolean decision for adding photo in quizz.
    """
    if incl is not None:
        if not any([elt in filepath for elt in incl]):  # No inclusion term.
            return False
    if excl is not None:
        if any ([elt in filepath for elt in excl]):  # Exclusion term
            return False
    
    return True


def tkclear(frame):
    """
    Clears all elements within a tkinter frame.
    """
    for elt in frame.winfo_children():
        elt.destroy()

def load_results(fileName):
    """
    Reads previous identification results from manually input csv file.
    """
    score = pd.read_csv(fileName, index_col=0)
    return score


def photo_quizz(folders=None, incl=None, excl=None, n=None,
                score=None, out_f=None, out_t=None
                ):
    """
    Main function to run the photo identification quizz and save the file and figure.
    Arguments
    ---------
    folders (list of path like): locations where photographs are stored
    score (pandas;DataFrame): previous score to load prior to running the quizz.
    incl (list of str): str present in the path of the photos to include in
        the quizz.
    excl (list of str): str present in the path of the photos to exclude from
        the quizz.
    n (int): number of questions to ask
   out_f (path like): Location to save the figure of the quizz results.
        Default is None and does not save the figure.
    out_t (path like): Location to save the table of the quizz results.
        Default is None and doest not save the table.
    
    Remark
    ------
    out_f and out_t will run irrespective of the user decision on the quizz end
       screen.
    """
    
    # Run quizz.
    my_quizz = Quizz(folders=folders, incl=incl, excl=excl, fig=out_f, tab=out_t)
    my_quizz.choose_photos()
    my_quizz.start_quizz(n=n)
    
    # Save output in designated locations.
    my_quizz.save_results(figname=out_f, csvname=out_t)
