# %%%%%%%%%% IMPORT LIBRARIES %%%%%%%%%%
from psychopy import visual, core, sound, data, gui, logging
from psychopy.visual import TextStim, ImageStim, MovieStim
from psychopy.hardware import keyboard
from scipy.io import wavfile
from random import gauss

import psychopy.event
import pandas as pd
import numpy as np
import random as rd
import os
import serial

# %%%%%%%%%% Path directories %%%%%%%%%%
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)


# %%%%%%%%%% Experiment %%%%%%%%%%

class broadbandNIRS:

    def __init__(self, portname, blank_rs=True, fullscreen=False):
        self.__port_name = portname
        self.__path = '/Users/emilia/Documents/Dementia task piloting/Mini-CYRIL'
        self.__win = None
        self.__clock = None
        self.__kb = None
        self.__port = None
        self.__blank = None
        self.__fixation_cross = None
        self.__filename_save = None
        self.__experiment_info = None
        self.__this_exp = None
        self.__rs_format = blank_rs
        self.__fullscreen = fullscreen

    # %%%%% SETTING UP EXPERIMENT %%%%%
    def __setup(self):
        print(f"Setting up experiment...")
        experiment_name = 'Optical Neuroimaging and Cognition (ONAC)'
        self.__experiment_info = {'Participant': ''}
        # dlg = gui.DlgFromDict(dictionary=self.__experiment_info, sortKeys=False, title=experiment_name)
        # if not dlg.OK:
        #     print("User pressed 'Cancel'!")
        #     core.quit()

        self.__experiment_info['date'] = data.getDateStr()
        self.__experiment_info['expName'] = experiment_name
        self.__experiment_info['psychopyVersion'] = '2021.2.3'
        filename = _thisDir + os.sep + u'data/%s_%s_%s' % (self.__experiment_info['Participant'],
                                                           experiment_name, self.__experiment_info['date'])

        self.__this_exp = data.ExperimentHandler(name=experiment_name, extraInfo=self.__experiment_info,
                                                 originPath='C:/Users/emilia/Documents/Dementia task piloting/Mini-CYRIL/',
                                                 savePickle=True, saveWideText=True,
                                                 dataFileName=filename)
        # Setting up a log file
        log_file = logging.LogFile(filename + '.log', level=logging.EXP)
        logging.console.setLevel(logging.WARNING)
        self.__filename_save = '/P' + str(self.__experiment_info['Participant'])

        end_exp_now = False
        frame_tolerance = 0.001

        if self.__port_name is not None:
            self.__port = serial.Serial(self.__port_name, baudrate=9600)

        # Set up window
        self.__win = visual.Window([300, 300], color=[-1, -1, -1], fullscr=self.__fullscreen)

        # Monitor frame rate
        self.__experiment_info['frameRate'] = self.__win.getActualFrameRate()
        if self.__experiment_info['frameRate'] is not None:
            frame_dur = 1.0 / round(self.__experiment_info['frameRate'])
        else:
            frame_dur = 1.0 / 60.0

        # Hide mouse
        self.__win.mouseVisible = False

        # Setting up useful trial components
        self.__clock = core.Clock()
        self.__kb = keyboard.Keyboard()
        self.__blank = TextStim(self.__win, text='')
        self.__fixation_cross = TextStim(self.__win, text='+', color=(-1, -1, 1))

    # %%%%% SOME USEFUL FUNCTIONS %%%%%
    def __baseline(self, duration=30):
        baseline_text = TextStim(self.__win, text='+', height=0.3, color=(-1, -1, 1))
        self.__win.color = [0, 0, 0]
        self.__clock.reset()
        while self.__clock.getTime() < (duration + (rd.random() / 10)):  # Randomise the baseline duration
            baseline_text.draw()
            self.__win.flip()
        self.__win.color = [-1, -1, -1]

    def __break(self):
        print(f'Break time!')
        break_text = (self.__path + '/Instructions/task_finished.png')
        break_stim = ImageStim(self.__win, break_text, units='pix', size=(1440, 900))
        break_stim.draw()
        self.__win.flip()
        psychopy.event.waitKeys()

    def __break_mid(self):
        print(f'Break time!')
        break_text = (self.__path + '/Instructions/break.png')
        break_stim = ImageStim(self.__win, break_text, units='pix', size=(1440, 900))
        break_stim.draw()
        self.__win.flip()
        psychopy.event.waitKeys()

    def __ready(self):
        ready_text = ImageStim(self.__win, image=(self.__path + '/ready.png'), units='pix', size=(1440, 900))
        ready_text.draw()
        self.__win.flip()
        psychopy.event.waitKeys()

    def __wait(self, duration=2):
        core.wait(duration + rd.random() / 10)

    def __blank_screen(self, duration=1):
        self.__blank.draw()
        self.__win.flip()
        core.wait(duration)
        self.__win.flip()

    def __present_instructions(self, filepath):
        """
        Presents instructions of different types.

        :param filepath: The filepath of the instruction csv.
        """

        instructions = pd.read_csv(filepath)
        for j in instructions['path']:
            instruction_stim = ImageStim(self.__win, j, units='pix', size=(1440, 900))
            instruction_stim.draw()
            self.__win.flip()
            psychopy.event.waitKeys()

    # %%%%% TASKS %%%%%
    def resting_state(self, duration=5):
        """
        Task 5: resting state

        :param duration: Duration of resting state.
        """

        print(f"Running resting state...")
        # LOAD TRIAL COMPONENTS
        resting_state_tone = sound.Sound(value='C', secs=0.1)

        # INSTRUCTIONS
        self.__present_instructions(self.__path + '/resting_state/resting_state_instructions.csv')

        # EXPERIMENT BLOCK
        # Pause
        self.__blank.draw()
        self.__win.flip()
        self.__wait()

        # Start resting state
        self.__clock.reset()
        trigger_sent = False
        while self.__clock.getTime() < (duration * 60 + 3):
            while self.__clock.getTime() < (duration * 60):
                if not trigger_sent:
                    self.__win.callOnFlip(self.__port.write, 'G'.encode())
                    trigger_sent = True
            self.__blank.draw()
            self.__win.flip()
        self.__port.write('H'.encode())

        resting_state_tone.play()

        self.__break()

    def breath_holding(self, duration=20):

        """

        Breath holding paradigm - selects randomise order of conditions from randomisation script

        """

        # Present instructions
        self.__present_instructions((self.__path + '/breath_holding/instructions.csv'))

        # Load trial components
        # stimuli = pd.read_csv((self.__path + '/breath_holding/P' + str(self.__experiment_info['Participant']\
        # + 'breath_holding_stimuli.csv'))
        stimuli = pd.read_csv((self.__path + '/breath_holding/breath_holding_stimuli.csv'))
        breath_holding_data = []
        stimulus = TextStim(self.__win, text='')

        for i in range(len(stimuli)):

            self.__baseline(20)

            trigger = stimuli.loc[:, 'trigger'][i]
            condition = stimuli.loc[:, 'condition'][i]
            stimulus.text = condition

            self.__clock.reset()
            trigger_sent = False

            while self.__clock.getTime() < duration:
                if not trigger_sent:
                    self.__win.callOnFlip(self.__port.write, trigger.encode())
                    trigger_sent = True
                stimulus.draw()
                self.__win.flip()

            df = pd.DataFrame({'condition': [condition]})
            breath_holding_data.append(df)

            if i in [4, 8]:
                self.__break_mid()

        self.__break()

        # Data saving
        print(f"Saving data...")
        breath_holding_data = pd.concat(breath_holding_data, ignore_index=True)
        breath_holding_data.to_csv((self.__path + '/breath_holding/participant_data/P' + \
                                    str(self.__experiment_info['Participant'] + '_breath_holding_data.csv')))

    def __end_all_experiment(self, duration=3):
        """
        Begins ending routine

        :param duration: Duration of wait time before exiting.
        """

        print(f"Ending experiment...")
        end_text = (self.__path + '/Instructions/study_finished.png')
        ending = ImageStim(self.__win, end_text)
        ending.draw()
        self.__win.flip()
        self.__wait(duration)
        self.__win.mouseVisible = True
        self.__win.flip()
        # self.__port.close()
        self.__win.close()
        core.quit()

        # %%%%% RUN EXPERIMENT %%%%%%
        def run(self):
            this_exp, filename = self.__setup()
            escape_experiment = False
            while not escape_experiment:
                escape_check = self.__kb.getKeys(keyList=['escape'], waitRelease=True)
                if 'escape' in escape_check:
                    core.quit()
                self.__overall_instructions()
                self.resting_state()
                self.breath_holding()
                self.__end_all_experiment()


e = broadbandNIRS(portname=None, fullscreen=True)
e.run()
