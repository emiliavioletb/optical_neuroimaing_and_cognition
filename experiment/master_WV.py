# This script is the current working version for the Optical Neuroimaging and Cognition study (ONAC).

# Several things must be checked before running:
#       - Make sure the port lines are not commented out
#       - Make sure that the durations of baselines & the resting state are all correct


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

    def __init__(self, portname, memory_condition, blank_rs=True, fullscreen=False):
        self.__port_name = portname
        self.__path = '/Users/emilia/Documents/Dementia task piloting/Lumo'
        self.__win = None
        self.__clock = None
        self.__kb = None
        self.__port = None
        self.__blank = None
        self.__fixation_cross = None
        self.__filename_save = None
        self.__experiment_info = None
        self.__this_exp = None
        self.__endfilename = None
        self.__rs_format = blank_rs
        self.__fullscreen = fullscreen
        self.__memory_condition = memory_condition

    #%%%%% SETTING UP EXPERIMENT %%%%%
    def __setup(self):
        print(f"Setting up experiment...")
        experiment_name = 'Optical Neuroimaging and Cognition (ONAC)'
        self.__experiment_info = {'Participant': ''}
        dlg = gui.DlgFromDict(dictionary=self.__experiment_info, sortKeys=False, title=experiment_name)
        if not dlg.OK:
            print("User pressed 'Cancel'!")
            core.quit()

        self.__experiment_info['date'] = data.getDateStr()
        self.__experiment_info['expName'] = experiment_name
        self.__experiment_info['psychopyVersion'] = '2021.2.3'
        self.__endfilename = _thisDir + os.sep + u'data/%s_%s_%s' % (self.__experiment_info['Participant'],
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
        # self.__win = visual.Window([1440, 900], color=[-1, -1, -1], fullscr=True)
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

    def __baseline(self, duration=30):
        baseline_text = TextStim(self.__win, text='+', height=0.3, color=(-1, -1, 1))
        self.__win.color = [0, 0, 0]
        self.__clock.reset()
        while self.__clock.getTime() < (duration+(rd.random()/10)):  # Randomise the baseline duration
            baseline_text.draw()
            self.__win.flip()
        self.__win.color = [-1, -1, -1]
        self.__win.flip()

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

    def __blank_screen(self, duration=1, colour='black'):
        if colour == 'black':
            self.__blank.draw()
            self.__win.flip()
            core.wait(duration)
            self.__win.flip()
        elif colour == 'grey':
            self.__win.color = [0, 0, 0]
            self.__win.flip()
            self.__blank.draw()
            self.__win.flip()
            core.wait(duration)
            self.__win.color = [-1, -1, -1]
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

    def __showimage(self, image, duration=None):
        showimg = ImageStim(self.__win, image=(self.__path + image))
        showimg.draw()
        self.__win.flip()
        if duration is not None:
            core.wait(duration)
            self.__win.flip()
        else:
            psychopy.event.waitKeys()

    def __chunking(self, lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

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
        practice_stimuli = object_stimuli.iloc[:7]
        object_stimuli = object_stimuli.iloc[6:stimulus_number*4+6] # Total number of stimuli to choose
        object_stimuli_list = list(object_stimuli['Link'])

        # Create data saving structure
        object_recognition_data = []

        # Chunk stimuli
        object_stimuli = [object_stimuli_list[i:i+stimulus_number] for i in list(range(0, len(object_stimuli), stimulus_number))]

        # INSTRUCTIONS

        # self.__present_instructions(self.__path + '/object_recognition_task/object_recognition_instructions.csv')
        #
        # ort_practice = ImageStim(self.__win, units='pix', size=(900, 600))
        #
        # # PRACTICE TRIALS
        # print(f'Starting practice object recognition trials...')
        img_path = '/object_recognition_task/test_stimuli/'
        # for j in practice_stimuli['Link']:
        #     k = self.__path + img_path + j
        #     ort_practice.setImage(k)
        #     ort_practice.draw()
        #     self.__win.flip()
        #     self.__wait()
        #     self.__blank.draw()
        #     self.__win.flip()
        #     self.__wait(duration=0.5)
        # self.__win.color = [-1, -1, -1]
        #
        # ready = ImageStim(self.__win, (self.__path + '/object_recognition_task/BNT_instructions_3.png'),
        #                   units='pix', size=(1440, 900))
        # ready.draw()
        # self.__win.flip()
        # psychopy.event.waitKeys()
        #
        # self.__wait()

        # # EXPERIMENT BLOCK
        print(f'Starting object recognition testing trials...')
        object_stim = ImageStim(self.__win, units='pix', size=(900, 600))

        for k in object_stimuli:
            self.__baseline(5) # Baseline duration
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
            self.__baseline(1)

        # Break
        self.__break()

        # Data saving
        print(f'Saving data...')
        object_recognition_data = pd.DataFrame(object_recognition_data, columns=['stimulus'])
        object_recognition_data.to_csv((self.__path + '/object_recognition_task/participant_data/'
                                        + str(self.__filename_save) + '_object_recognition_task.csv'), header=True)

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

    def resting_state(self, duration=1):
        """
        Task 5: resting state

        :param duration: Duration of resting state.
        """

        print(f"Running resting state...")
        # LOAD TRIAL COMPONENTS
        resting_state_tone = sound.Sound(value='C', secs=0.1)

        # INSTRUCTIONS
        # self.__present_instructions(self.__path + '/resting_state/resting_state_instructions.csv')

        # EXPERIMENT BLOCK
        self.__blank.draw()
        self.__win.flip()
        self.__wait(duration=2)

        # Start resting state
        self.__clock.reset()
        trigger_sent = False
        while self.__clock.getTime() < (duration * 10+2+(rd.random()/10)):
            while self.__clock.getTime() < (duration*10):
                if not trigger_sent:
                    self.__win.callOnFlip(self.__port.write, 'G'.encode())
                    trigger_sent = True
            self.__blank.draw()
            self.__win.flip()
        self.__port.write('H'.encode())

        resting_state_tone.play()

        self.__break()

    def memory_task(self):

        """

        Implicit memory task

        """
        # Set up trial components
        trial_text = TextStim(self.__win, text='')
        if self.__memory_condition == 'LL':
            encoding_text = 'Indoor or outdoor?'
            testing_text = 'Old or new?'
            trial_text.text = encoding_text
        elif self.__memory_condition == 'RR':
            encoding_text = 'Outdoor or indoor?'
            testing_text = 'New or old?'
            trial_text.text  = encoding_text

        correct_text = TextStim(self.__win, text='Correct!', color=[0, 1, -1])
        incorrect_text = TextStim(self.__win, text='Incorrect', color=[1, 0, 0])
        no_key_pressed = TextStim(self.__win, text='No key pressed!', color=[-1, -1, 1])

        # Load stimuli
        encoding_stimuli = pd.read_csv(self.__path + '/memory_task/encoded_stimuli_' + str(self.__memory_condition) + '.csv')
        new_stimuli = pd.read_csv(self.__path + '/memory_task/new_stimuli_' + str(self.__memory_condition) + '.csv')
        practice_stimuli = pd.read_csv(self.__path + '/memory_task/practice_stimuli_' + str(self.__memory_condition) + '.csv')

        # Determine conditions
        # Will this participant encode more indoor or outdoors?
        k = rd.randint(0, 1)
        if k == 0: # More indoor than outdoor so drop last outdoor
            encoding_stimuli.drop(encoding_stimuli.tail(1).index, inplace=True)
            new_stimuli.drop(new_stimuli.tail(1).index,inplace=True)
        else: # More outdoor than indoor so drop last indoor
            encoding_stimuli.drop(encoding_stimuli.head(1).index, inplace=True)
            new_stimuli.drop(new_stimuli.head(1).index, inplace=True)

        testing_stimuli = pd.concat((encoding_stimuli, new_stimuli))

        # Randomise stimuli
        rand_encoding_stimuli = encoding_stimuli.sample(frac=1, ignore_index=True)
        rand_testing_stimuli = testing_stimuli.sample(frac=1, ignore_index=True)
        rand_practice_stimuli = practice_stimuli.sample(frac=1, ignore_index=True)

        # Present instructions
        # self.__present_instructions((self.__path + '/memory_task/memory_task_instructions_' + str(self.__memory_condition) + '.csv'))

        # Practice trials
        # self.__baseline(5)
        # practice_stim = ImageStim(self.__win, units='pix', size=(960, 600))
        #
        # for k in list(range(6)):
        #     practice_stim.setImage(rand_practice_stimuli['stimulus'][k])
        #     self.__clock.reset()
        #     key_pressed = False
        #     while self.__clock.getTime() < 5:
        #         if self.__clock.getTime() < 3:
        #             practice_stim.draw()
        #         else:
        #             trial_text.draw()
        #             if not key_pressed:
        #                 keys = self.__kb.getKeys(keyList=['left', 'right'], waitRelease=False)
        #                 if len(keys) > 0:
        #                     key_pressed = True
        #         self.__win.flip()
        #
        #     if key_pressed: # If a key is pressed, check if right or wrong
        #         response = str(keys[-1].name)
        #         if response == rand_practice_stimuli['corr_ans'][k]:
        #             correct_text.draw()
        #         else:
        #             incorrect_text.draw()
        #     elif not key_pressed:
        #             no_key_pressed.draw()
        #
        #     self.__win.flip()
        #     self.__wait(2)
        #     self.__blank_screen()
        #
        # self.__ready()
        #
        # self.__wait(2)

        self.__blank_screen(duration=1, colour='grey')

        # Set up trial components
        phases = ['encoding', 'recall']
        prompts = [encoding_text, testing_text]
        stimuli = [rand_encoding_stimuli, rand_testing_stimuli]
        correct_answer_columns = ['corr_ans_encoding', 'corr_ans_recall']
        condition_columns = ['condition_encoding', 'condition_recall']

        text = TextStim(self.__win, text='')
        stimulus = ImageStim(self.__win, units='pix', size=(960, 600))

        for a in range(len(phases)):
            phase = phases[a]
            text.text = prompts[a]
            all_stimuli = list(self.__chunking(stimuli[a], 2))
            correct_answer_column = correct_answer_columns[a]
            condition_column = condition_columns[a]
            block_data = []

            for block in all_stimuli:

                self.__baseline(2)

                block = block.reset_index()

                for j in range(len(block)):
                    stimulus.setImage(block['stimulus'][j])
                    correct_answer = block[str(correct_answer_column)][j]
                    condition = block[str(condition_column)][j]
                    img_trigger = block['trigger'][j]
                    ans_trigger = img_trigger + 'a'
                    if phase == 1:
                        img_trigger = img_trigger + 'r'
                        ans_trigger = ans_trigger + 'r'

                    img_trigger_sent = False
                    ans_trigger_sent = False
                    key_pressed = False
                    clock_reset = False

                    self.__clock.reset()
                    self.__kb.clock.reset()

                    while self.__clock.getTime() < 5:
                        if self.__clock.getTime() < 3:
                            stimulus.draw()
                            if not img_trigger_sent:
                                self.__win.callOnFlip(self.__port.write, img_trigger.encode())
                                img_trigger_sent = True
                        else:
                            text.draw()
                            if not ans_trigger_sent:
                                self.__win.callOnFlip(self.__port.write, ans_trigger.encode())
                                ans_trigger_sent = True
                            if not clock_reset:
                                self.__win.callOnFlip(self.__kb.clock.reset)
                                self.__kb.clearEvents()
                                keys = []
                                clock_reset = True
                            if not key_pressed:
                                keys = self.__kb.getKeys(keyList=['left', 'right'], waitRelease=False)
                                if len(keys) > 0:
                                    key_pressed = True
                        self.__win.flip()

                    if key_pressed:
                        response = str(keys[-1].name)
                        reaction_time = keys[-1].rt
                        if response == correct_answer:
                            result = 1
                        else:
                            result = 0
                    elif not key_pressed:
                        result = np.nan
                        reaction_time = np.nan
                        response = np.nan

                    looped_data = pd.DataFrame({'phase': phase,
                                       'stimulus': text.text,
                                       'condition': [condition],
                                       'trial_number': [block['index'][j]],
                                       'reaction_time': [reaction_time],
                                       'response': [result],
                                       'correct_answer': [correct_answer],
                                       'key_pressed': [response],
                                        'k_num': [k]})
                    block_data.append(looped_data)

                    self.__this_exp.addData('IMT_stimulus', text.text)
                    self.__this_exp.addData('IMT_rt', reaction_time)
                    self.__this_exp.addData('IMT_response', result)
                    self.__this_exp.addData('IMT_corr_ans', correct_answer)
                    self.__this_exp.addData('IMT_key_pressed', response)
                    self.__this_exp.addData('IMT_phase', phase)
                    self.__this_exp.addData('IMT_condition', condition)
                    self.__this_exp.nextEntry()

            if a == 0:
                self.__present_instructions((self.__path + '/memory_task/memory_task_instructions_recall_' + \
            str(self.__memory_condition) + '.csv'))
                self.__wait()
                self.__blank_screen(duration=1, colour='black')

        self.__break()
        data_export = pd.concat(block_data, ignore_index=True)
        data_export.to_csv((self.__path + '/memory_task/participant_data/' + str(self.__filename_save) \
                                        + '_data.csv'), header=True, index=False)

    def visual_stimulation(self):
        '''
        Task 4: visual stimulation paradigm.

        Returns
        -------

        '''

        print(f"Running visual stimulation paradigm")

        # Set up trial components
        wedge_1 = visual.RadialStim(self.__win, tex='sqrXsqr', color=1, size=1,
                                   visibleWedge=[180, 360], radialCycles=6, angularCycles=12, interpolate=False,
                                   autoLog=False, pos=(0, 0))
        wedge_2 = visual.RadialStim(self.__win, tex='sqrXsqr', color=-1, size=1,
                                   visibleWedge=[180, 360], radialCycles=6, angularCycles=12, interpolate=False,
                                   autoLog=False, pos=(0, 0))

        fixation_cross = TextStim(self.__win, text='+', height=0.3, color=[0, 0, 0])

        visual_conditions = pd.read_csv((self.__path + '/visual_stimulation/stimuli/P' + \
                                         str(self.__experiment_info['Participant']) + '_visual_stimulation_stimuli.csv'))

        # Instructions
        self.__present_instructions(self.__path + '/visual_stimulation/instructions.csv')

        t = 0
        visual_stim_data = []

        for i in range(0, len(visual_conditions.loc[:,'frequency'])):
            frequency = 1/visual_conditions.loc[:,'frequency'][i]
            trigger = visual_conditions.loc[:, 'trigger'][i]
            wedge_1.visibleWedge = list((visual_conditions.loc[:,'orientation1'][i],
                                        visual_conditions.loc[:, 'orientation2'][i]))
            wedge_2.visibleWedge = list((visual_conditions.loc[:,'orientation1'][i],
                                        visual_conditions.loc[:, 'orientation2'][i]))
            side = visual_conditions.loc[:, 'side'][i]
            trigger_sent = False

            self.__baseline(2)

            self.__clock.reset()

            while self.__clock.getTime() < 10:
                if not trigger_sent:
                    self.__win.callOnFlip(self.__port.write, trigger.encode())
                    trigger_sent = True
                if self.__clock.getTime() % frequency < frequency / 2.0:
                    stim = wedge_1
                else:
                    stim = wedge_2
                stim.draw()
                fixation_cross.draw()
                self.__win.flip()
            self.__port.write(''.encode())
            self.__baseline(2)
            df = pd.DataFrame({'frequency': [frequency],
                               'side': [side]})
            visual_stim_data.append(df)

        self.__break()

        # Data saving
        print(f'Saving data...')
        visual_stim_data_export = pd.concat(visual_stim_data, ignore_index=True)
        visual_stim_data_export.to_csv((self.__path + '/visual_stimulation/participant_data/' + str(self.__filename_save) \
                            + 'data.csv'), header=True, index=False)

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

        naturalistic_motor_instructions = MovieStim3(self.__win, (self.__path + '/naturalistic_motor_task/instruction_video.mp4'), \
                                                     size = (1440, 900))
        while naturalistic_motor_instructions.status != visual.FINISHED:
            naturalistic_motor_instructions.draw()
            self.__win.flip()

        self.__ready()

        self.__wait()

        # Start testing trials
        print(f'Starting naturalistic motor task testing...')

        for k in list(range(3)):
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
                if trigger =='CN':
                    time = 20
                while self.__clock.getTime() < time and not key_pressed:
                    naturalistic_motor_stim.draw()
                    if not trigger_sent:
                        self.__win.callOnFlip(self.__port.write, trigger.encode())
                        trigger_sent = True
                    if not sound_played:
                        audio_stim.play(when=next_flip)
                        sound_played = True
                    self.__win.flip()
                    if trigger != 'CN':
                        keys = self.__kb.getKeys(keyList=None, waitRelease=True)
                        time += 1
                        if len(keys) > 0:
                            break
                self.__port.write(end_trigger.encode())
                df = pd.DataFrame({'Stimulus': [naturalistic_motor_stim.text],
                                   'Duration': [keys[-1].rt],
                                   'Trial': [k]})
                naturalistic_motor_data.append(df)
                self.__this_exp.addData('NMT_stimulus', naturalistic_motor_stim.text)
                self.__this_exp.addData('NMT_duration', keys[-1].rt)
                self.__this_exp.nextEntry()
                self.__wait(1)
                self.__kb.clearEvents()

            # Break
            self.__break()

        # Data saving
        print(f'Saving data...')
        naturalistic_motor_data = pd.concat(naturalistic_motor_data, ignore_index=True)
        naturalistic_motor_data.to_csv((self.__path + '/naturalistic_motor_task/participant_data/' + str(self.__filename_save)
                                        + 'naturalistic_motor_task.csv'), header=True, index=False)

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
        self.__this_exp.saveAsWideText(self.__endfilename + '.csv', delim='auto')
        self.__this_exp.saveAsPickle(self.__endfilename)
        logging.flush()
        self.__port.close()
        self.__win.close()
        core.quit()

    #%%%%% RUN EXPERIMENT %%%%%%
    def run(self):
        self.__setup()
        escape_experiment = False
        while not escape_experiment:
            escape_check = self.__kb.getKeys(keyList=['escape'], waitRelease=True)
            if 'escape' in escape_check:
                core.quit()
            # self.__overall_instructions()
            # self.object_recognition()
            # self.mismatched_negativity()
            # self.resting_state()
            # self.memory_task()
            # self.visual_stimulation()
            self.naturalistic_motor_task()
            self.__end_all_experiment()

e = Experiment(portname='/dev/tty.usbserial-FTBXN67J', fullscreen=True, memory_condition='LL')
e.run()
