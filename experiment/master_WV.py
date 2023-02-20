
#%%%%%%%%%% IMPORT LIBRARIES %%%%%%%%%%
from psychopy import visual, core, sound, data, gui, logging
from psychopy.visual import TextStim, ImageStim, MovieStim3
from psychopy.hardware import keyboard
from psychopy.constants import FINISHED, NOT_STARTED

import psychopy.event
import pandas as pd
import numpy as np
import random as rd
import os
import serial
import psychtoolbox as ptb
import random as rd

#%%%%%%%%%% Path directories %%%%%%%%%%
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

#%%%%%%%%%% Experiment %%%%%%%%%%


class Experiment:

    def __init__(self, portname, restart=False, blank_rs=True, fullscreen=False):
        self.__port_name = portname
        self.__path = '/Users/emilia/Documents/Dementia task piloting/Lumo'
        self.__restart = restart
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

    #%%%%% SETTING UP EXPERIMENT %%%%%
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
                                         originPath='C:/Users/emilia/Documents/Dementia task piloting/Lumo/dementia_task_piloting/',
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

    #%%%%% SOME USEFUL FUNCTIONS %%%%%
    def __get_restart(self):
        if self.__restart:
            restart_point = {'Task to restart from': ''}
            dlg = gui.DlgFromDict(dictionary=restart_point, sortKeys=False, title='Where do you want to restart from?')
            if not dlg.OK:
                print("User pressed 'Cancel'!")
                core.quit()
            return restart_point['Task to restart from']

    def __baseline(self, duration=30):
        baseline_text = TextStim(self.__win, text='+', height=0.3, color=(-1, -1, 1))
        self.__win.color = [0, 0, 0]
        self.__clock.reset()
        while self.__clock.getTime() < (duration+(rd.random()/10)):  # Randomise the baseline duration
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

    def __ready(self):
        ready_text = ImageStim(self.__win, image=(self.__path + '/ready.png'), units='pix', size=(1440, 900))
        ready_text.draw()
        self.__win.flip()
        psychopy.event.waitKeys()

    def __wait(self, duration=2):
        core.wait(duration+rd.random()/10)

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

    def __showimage(self, image, duration):
        showimg = ImageStim(self.__win, image=(self.__path + image))
        showimg.draw()
        self.__win.flip()
        if duration is not None:
            core.wait(duration)
            self.__win.flip()
        else:
            psychopy.event.waitKeys()

    #%%%%% TASKS %%%%%
    def __overall_instructions(self):
        """
        Overall study instructions

        """

        print(f"Presenting instructions...")
        self.__present_instructions((self.__path + "/Instructions/overall_instructions.csv"))

    def object_recognition(self, stimulus_number=12):
        """
        Task 2: object recognition task.
        Each block contains 12 stimuli, each of which are presented for 2seconds, with an inter-stimulus interval of
        0.5s.

        :param stimulus_number: The number of stimuli presented per block. The default is 12 for a 30-second task block.
        :return: Dataframe with sequence of stimulus presentation.
        """

        print(f'Running object recognition task...')
        # LOAD TRIAL COMPONENTS
        object_stimuli = pd.read_csv(self.__path + '/object_recognition_task/stimuli/P' + str(self.__experiment_info['Participant']) + '_object_recognition_task_stimuli.csv')
        practice_stimuli = object_stimuli.iloc[:2]
        object_stimuli = object_stimuli.iloc[6:stimulus_number*4+6] # Total number of stimuli to choose
        object_stimuli_list = list(object_stimuli['Link'])

        # Create data saving structure
        object_recognition_data = []

        # Chunk stimuli
        object_stimuli = [object_stimuli_list[i:i+stimulus_number] for i in list(range(0, len(object_stimuli), stimulus_number))]

        # INSTRUCTIONS

        self.__present_instructions(self.__path + '/object_recognition_task/object_recognition_instructions.csv')

        self.__win.color = [0, 0, 0]
        ort_practice = ImageStim(self.__win, units='pix', size=(900, 600))
        # TODO: the first background is black

        # PRACTICE TRIALS
        print(f'Starting practice object recognition trials...')
        img_path = '/object_recognition_task/test_stimuli/'
        for j in practice_stimuli['Link']:
            k = self.__path + img_path + j
            ort_practice.setImage(k)
            ort_practice.draw()
            self.__win.flip()
            self.__wait()
            self.__blank.draw()
            self.__win.flip()
            self.__wait(duration=0.5)
        self.__win.color = [1, 1, 1]

        ready = ImageStim(self.__win, (self.__path + '/object_recognition_task/BNT_instructions_3.png'),
                          units='pix', size=(1440, 900))
        ready.draw()
        self.__win.flip()
        psychopy.event.waitKeys()

        self.__wait()

        # # EXPERIMENT BLOCK
        print(f'Starting object recognition testing trials...')
        object_stim = ImageStim(self.__win)

        for k in object_stimuli:
            self.__baseline(15) # Baseline duration
            self.__win.callOnFlip(self.__port.write, 'C'.encode())

            for j in k:
                k = self.__path + img_path + j
                object_stim.setImage(k)
                trigger_sent = False
                self.__clock.reset()
                while self.__clock.getTime() < 2.5:
                    if not trigger_sent:
                        self.__win.callOnFlip(self.__port.write, 'E'.encode())
                        trigger_sent = True
                    if self.__clock.getTime() < 2:
                        object_stim.draw()
                    else:
                        self.__blank.draw()
                    self.__win.flip()
                self.__port.write('F'.encode())
                object_recognition_data.append(j)
                self.__this_exp.addData('OR_stimulus', j)
                self.__this_exp.nextEntry()
            self.__port.write('D'.encode())
            self.__baseline(5)

        # Break
        self.__break()

        # Data saving
        print(f'Saving data...')
        object_recognition_data = pd.DataFrame(object_recognition_data, columns=['stimulus'])
        object_recognition_data.to_csv((self.__path + '/object_recognition_task/participant_data/'
                                        + str(self.__filename_save) + 'object_recognition_task.csv'), header=True)

    def mismatched_negativity(self):
        '''
        Task 3: mismatched negativity task
        This is based on the mismatched negativity task currently used in Milos with MEG and EEG.

        :return: dataframe of tones presented

        '''

        print(f'Running mismatched negativity task...')
        movie_stimuli = pd.read_csv(self.__path + '/mismatched_negativity_task/MMN_movie_stimuli.csv').values.tolist()
        movie_stimuli = [item for y in movie_stimuli for item in y]
        auditory_stimuli = pd.read_csv(self.__path + '/mismatched_negativity_task/auditory_stimuli.csv')
        duration = 1

        # Instructions
        # self.__present_instructions(self.__path + '/mismatched_negativity_task/mismatched_negativity_instructions.csv')

        MMN_data = []

        self.__baseline(30) #TODO: how long to do the baseline for?

        for i in range(0, 6):
            movie = str(movie_stimuli[i])
            movie_stim = MovieStim3(self.__win, movie)
            movie_stim.autodraw = True
            auditory_stim = auditory_stimuli.loc[auditory_stimuli['block'] == i]
            triggers = auditory_stim.loc[:, 'trigger'].values.tolist()
            sounds = auditory_stim.loc[:, 'sound'].values.tolist()
            conditions = auditory_stim.loc[:, 'condition'].values.tolist()

            next_flip = self.__win.getFutureFlipTime(clock='ptb')

            for k in range(len(auditory_stim)):
                trig = triggers[k]
                sound_file = self.__path + '/mismatched_negativity_task/auditory_stimuli/' + \
                                      sounds[k] + '.wav'
                sound_play = sound.Sound(sound_file)

                self.__clock.reset()
                trigger_sent = False
                sound_played = False

                while self.__clock.getTime() < 1:
                    # if not trigger_sent:
                        # self.__win.callOnFlip(self.__port.write, trig.encode())
                        # trigger_sent = True

                    if not sound_played:
                        sound_play.play(when=next_flip)

                    self.__win.flip()
                    movie_stim.autodraw = False

            df = pd.DataFrame({'condition': [conditions[k]], 'sound': sounds[k], \
                               'repetition': [k], 'block': [i]})
            MMN_data.append(df)

        # PRACTICE TRIALS
        self.__ready()

        self.__break()

        # Data saving
        print(f'Saving data...')
        MMN_data = pd.concat(MMN_data)
        MMN_data.to_csv((self.__path + '/mismatched_negativity_task/participant_data/' + str(self.__filename_save)
                         + 'mismatched_negativity_task.csv'), header=True)

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
        while self.__clock.getTime() < (duration * 60+3):
            while self.__clock.getTime() < (duration*60):
                if not trigger_sent:
                        self.__win.callOnFlip(self.__port.write, 'G'.encode())
                        trigger_sent = True
            self.__blank.draw()
            self.__win.flip()
        self.__port.write('H'.encode())

        resting_state_tone.play()

        self.__break()

    def memory_task(self):

        # Encoding phase
        question_text = TextStim(self.__win, text='Indoor or outdoor?')
        encoding_stimuli = pd.read_csv((self.__path + '/memory_task/encoding_stimuli_P' + str(self.__experiment_info['Participant'])))
        encoding_data = []
        for i in range(75):
            stimulus = encoding_stimuli[i]
            self.__clock.reset()
            trigger_sent = False
            while self.__clock.getTime() < 5:

                if self.__clock.getTime() < 2: # Question presented for 2000ms
                    question_text.draw()

                else:
                    stimulus.draw() # Stimulus presented for 3000ms

                self.__win.flip()

            ed = pd.DataFrame{''} # Record stimulus presented, trial number, reaction time, answer, old/new, indoor/outdoor
            encoding_data.append(ed)

        encoding_data = pd.Concat(encoding_data)
        encoding_data.to_csv()

    def visual_stimulation(self):
        '''
        Task 4: visual stimulation paradigm.

        Returns
        -------

        '''

        visual_stim = (self.__path + '/visual_stimulation/grating.png')
        visual_stim = ImageStim(self.__win, visual_stim)
        frequencies = pd.read_csv((self.__path + '/visual_stimulation_task/stimuli_P' + str(self.__experiment_info['Participant'] \
                                                                                  + '.csv'))

        # Baseline
        self.__baseline(30)

        for i in len(frequencies.loc['frequency']):
            visual_grating =
            frequency = frequencies.loc[:,'frequency'][i]
            trigger = frequencies.loc[frequencies[]]
            self.__clock.reset()
            trigger_sent = False
            while self.__clock.getTime() < 10:
                if not trigger_sent:
                    self.__win.callOnFlip(self.__port.write, trigger.encode())
                grating.draw()
                self.__win.flip()

        # Stimulus shown for 10 seconds
        # Frequency of stimulus should be less than sampling frequency of Lumo
        # 15 seconds baseline before and after stimulus
        # 3 stimulus repetitions

        self.__break()

        # Data saving
        print(f'Saving data...')

    def naturalistic_motor_task(self):
        """
        Task 7: Naturalistic motor task

        """

        print(f"Running naturalistic motor task...")

        # Load task components
        naturalistic_motor_stims = pd.read_csv(self.__path +
                                               '/naturalistic_motor_task/naturalistic_motor_task_stimuli.csv')
        naturalistic_motor_data = []
        naturalistic_motor_stim = TextStim(self.__win, text='')

        # Instructions
        print(f'Presenting naturalistic motor task instructions...')

        naturalistic_motor_instructions = MovieStim(self.__win, (self.__path + '/naturalistic_motor_task/naturalistic_motor_task_instructions.mov'))
        naturalistic_motor_instructions.draw()
        self.__win.flip()

        self.__showimage((self.__path + '/naturalistic_motor_task/experimenter.png'))

        self.__ready()

        self.__wait()

        # Start testing trials
        print(f'Starting naturalistic motor task testing...')

        for j in range(len(naturalistic_motor_stims)):
            naturalistic_motor_stim.text = naturalistic_motor_stims['stimulus'].iloc[j]
            trigger = naturalistic_motor_stims['trigger'].iloc[j]
            end_trigger = naturalistic_motor_stims['end_trigger'].iloc[j]
            audio_stim = sound.Sound(naturalistic_motor_stims['instruction'].iloc[j])

            time = 10

            self.__baseline(5)

            trigger_sent = False
            key_pressed = False
            sound_played = False
            next_flip = self.__win.getFutureFlipTime(clock='ptb')
            self.__clock.reset()
            self.__kb.clock.reset()
            while self.__clock.getTime() < time and not key_pressed:
                naturalistic_motor_stim.draw()
                if not trigger_sent:
                    self.__win.callOnFlip(self.__port.write, trigger.encode())
                    trigger_sent = True
                if not sound_played:
                    audio_stim.play(when=next_flip)
                    sound_played = True
                self.__win.flip()
                keys = self.__kb.getKeys(keyList=None, waitRelease=True)
                time += 1
                if len(keys) > 0:
                    break
            self.__port.write(end_trigger.encode())
            df = pd.DataFrame({'Stimulus': [naturalistic_motor_stim.text], 'Duration': [keys[-1].rt]})
            naturalistic_motor_data.append(df)
            self.__this_exp.addData('NMT_stimulus', naturalistic_motor_stim.text)
            self.__this_exp.addData('NMT_duration', keys[-1].rt)
            self.__this_exp.nextEntry()
            self.__wait(1)

        # Break
        self.__break()

        # Data saving
        print(f'Saving data...')
        naturalistic_motor_data = pd.concat(naturalistic_motor_data, ignore_index=True)
        naturalistic_motor_data.to_csv((self.__path + '/naturalistic_motor_task/participant_data/' + str(self.__filename_save)
                                        + 'naturalistic_motor_task.csv'), header=True, index=False)

    def simple_motor_task(self, duration=10):
        """
        Task 6: simple motor task

        :param duration: Duration of each motor trial.
        """

        print(f"Running simple motor task...")

        # Load trial components
        motor_task_stim = pd.read_csv(
            self.__path + '/simple_motor_task/stimuli/' + 'P' + str(self.__experiment_info['Participant']) +
            '_simple_motor_task_stimuli.csv')
        motor_task_data = []
        metronome = sound.Sound((self.__path + '/simple_motor_task/temp.wav'))
        frequency = 50

        # Instructions
        print(f'Presenting simple motor task instructions...')
        simple_motor_task_instructions = MovieStim(self.__win, (self.__path + '/motor_task/motor_instructions_video.mp4'))
        simple_motor_task_instructions.draw()
        self.__win.flip()

        self.__ready()

        self.__wait()

        # Testing trials
        print(f'Print running simple motor task test trials...')

        # for j in range(len(motor_task_stim)): # TODO: create frequency metronome
        #     trigger = motor_task_stim['trigger'].iloc[j]
        #     end_trigger = motor_task_stim['end_trigger'].iloc[j]
        #     motor_stim = TextStim(self.__win, motor_task_stim['stimulus'].iloc[j])
        #
        #     # Baseline
        #     self.__baseline(10)
        #
        #     trigger_sent = False
        #     self.__clock.reset()
        #     next_flip = self.__win.getFutureFlipTime(clock='ptb')
        #     now = ptb.GetSecs()
        #
        #     while self.__clock.getTime() < duration:
        #         motor_stim.draw()
        #         if not trigger_sent:
        #             self.__win.callOnFlip(self.__port.write, trigger.encode())
        #             trigger_sent = True
        #         if ptb.getSecs() = now + (60/frequency):
        #             metronome.play(when=next_flip)
        #             now = ptb.GetSecs()
        #         self.__win.flip()

        #     self.__port.write(end_trigger.encode())
        #     self.__baseline(2)
        #     df = pd.DataFrame({'stimulus': [motor_task_stim['stimulus'].iloc[j]],
        #                        'trigger': [motor_task_stim['trigger'].iloc[j]]})
        #     motor_task_data.append(df)
        #     self.__this_exp.addData('SMT_stimulus', j)
        #     self.__this_exp.nextEntry()
        #
        # # Break
        # self.__break() # TODO: how often to break?
        #
        # motor_task_data = pd.concat(motor_task_data, ignore_index=True)
        #
        # # Data saving
        # print(f'Saving data...')
        # motor_task_data.to_csv((self.__path + '/simple_motor_task/participant_data/' + self.__filename_save
        #                         + 'simple_motor_task.csv'), header=True, index=False)

    #%%%%% END EXPERIMENT ROUTINE %%%%%
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
        #self.__port.close()
        self.__win.close()
        core.quit()

    #%%%%% RUN EXPERIMENT %%%%%%
    def run(self):

        tasks = [
            ("Introduction", self.__overall_instructions, [], {}),
            ("Auditory staircase", self.auditory_staircase, [5], {}),
            ("Object recognition", self.object_recognition, [], {}),
            ("Resting state", self.resting_state, [], {}),
            ("Simple motor task", self.simple_motor_task, [], {}),
            ("Naturalistic motor task", self.naturalistic_motor_task, [], {})
        ]
        this_exp, filename = self.__setup()
        escape_experiment = False
        while not escape_experiment:
            escape_check = self.__kb.getKeys(keyList=['escape'], waitRelease=True)
            if 'escape' in escape_check:
                core.quit()
            for taskname, fn, args, kwargs in tasks:
                if not self.__restart:
                    fn(*args, **kwargs)
                else:
                    start_from = self.__get_restart()
                    if start_from != taskname:
                        pass
                    else:
                        fn(*args, **kwargs)
            self.__end_all_experiment()

    def test(self):
        self.__setup()
        self.mismatched_negativity()
        self.__end_all_experiment()

e = Experiment(portname=None, fullscreen=False)
e.test()