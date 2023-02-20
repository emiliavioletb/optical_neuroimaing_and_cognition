
import pandas as pd
import email, smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class randomisation:

    def __init__(self, participant_number, tasks, password):
        self.__participant_number = participant_number
        self.__tasks = tasks
        self.__password = password
        self.__new_stimuli = None

    def __randomise(self, participant_number, task):
        filepath = '/Users/emilia/Documents/Dementia task piloting/Lumo/'+ task + '/' + task + '_stimuli.csv'
        original_stimuli = pd.read_csv(filepath)

        # Randomise stimuli
        randomised_stimuli = original_stimuli.sample(frac=1)

        # Export randomised stimuli
        path = '/Users/emilia/Documents/Dementia task piloting/Lumo/' + task + '/stimuli'
        new_stimuli = path + '/P' + str(participant_number) + '_' + str(task) + '_stimuli.csv'
        randomised_stimuli.to_csv(new_stimuli, header=True, index=False)

        return new_stimuli

    def __create_randomisation(self):

        attachments = []

        if 'object_recognition_task' in self.__tasks:
            ORT_stim = self.__randomise(self.__participant_number, 'object_recognition_task')
            attachments.append(ORT_stim)

        if 'simple_motor_task' in self.__tasks:
            motor_task_stim = self.__randomise(self.__participant_number, 'simple_motor_task')
            attachments.append(motor_task_stim)

        else:
            raise ValueError('No tasks inputted!')

        return attachments

    def send_email(self):

        # Get attachments
        attachments = self.__create_randomisation()

        # Get server details
        TLS_port = 465
        server_address = 'smpt.gmail.com'

        subject = 'Task stimuli for participant ' + str(self.__participant_number)
        email = 'ONACstudy@gmail.com'
        receiver = 'ONACstudy@gmail.com'

        # Create message
        message = MIMEMultipart()
        message['From'] = email
        message['To'] = receiver
        message['Subject'] = subject

        for j in attachments:
            with open(j, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {j}",
            )

            message.attach(part)
        text = message.as_string()

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", TLS_port, context=context) as server:
            server.login(email, self.__password)
            server.sendmail(email, receiver, text)

exp_setup = randomisation(3, ['object_recognition_task', 'simple_motor_task'], password='qgtzzyskwzmamrqr')
exp_setup.send_email()