# PhotoID

Python-based GUI to train for animal individual identification.
The module can work with any set of photographs, as long as the name of each photograph starts with the individual name followed by an underscore.
The module includes a score tracking and visualisation system.

## Tutorial

Download photoID.py, install the requires packages `pip install -r requirements.txt`, and run python in the same folder as the photoID.py file.

### Full GUI mode

The module include GUI to set up the photoID quizz.
```
import photoID as pid

# Configure output files and photo sorting.
figure_output_name, table_output_name, exclusion_list = param_window()

# Finish configuration and run quizz.
pid.photo_quizz(out_f=figure_output_name, out_t=table_output_name, excl=exclusion_terms)
# This line will open the empty quizz window (do not close it!!) and the configuration window.
# The quizz will start as soon as the configuration window is closed (with the Finish button).
```

For some reason, running `pid.photo_quizz` displays an error message in the console. I will look into matplotlib to understand why.
However, is is possible to continue with the quizz with no issue.

### Manual mode

It is also possible to configure the quizz manually.

```
import photoID as pid

# Set up all parameters manually:
#    - if folders and n are not provided, the GUI will open after initialisation.
#    - score, fig, tab are optionnal. Default is None and doesn't do anything

# Initialise Quizz instance.
my_quizz = pid.Quizz(folders=folders, n=n)  # Minimal version, no previous score is loaded and nothing is saved.
my_quizz = pid.Quizz(folders=folders, n=n, score=score, fig=fig, tab=tab)

# Select photos for the test.
my_quizz.choose_photos()  # Minimal version, will select all photographs in the folders
my_quizz.choose_photos(exclude=exclude)  # Will only select photographs which path do not contain elements of the exclude list.
# I implemented it to remove unindentified photos from the test.
# I may add an include parameter to select subsets of individuals from a folder.

# Run quizz.
my_quizz.start_quizz()

# Manually save results if quizz ended without clicking on 'Save results' button.
my_quizz.save_results(out_f=out_f, out_t=out_t)
```
