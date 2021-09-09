import logging

from api.controllers.project_utilities import get_project_members
from api.helpers.email_helpers import get_html
from api.models import Project
from email.message import EmailMessage
from os import environ, link
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
logger = logging.getLogger(__name__)

connection = BlockingConnection(
    ConnectionParameters(
        host=environ.get('MAILER_RABBITMQ_HOST'),
        port=int(environ.get('MAILER_RABBITMQ_PORT')),
        virtual_host=environ.get('MAILER_RABBITMQ_VHOST'),
        credentials=PlainCredentials(
            username=environ.get('MAILER_RABBITMQ_USER'),
            password=environ.get('MAILER_RABBITMQ_PASS')
        )
    )
)

channel = connection.channel()

channel.queue_declare(
    queue=environ.get('MAILER_RABBITMQ_QUEUE')
)


def send_email(msg: EmailMessage) -> bool:
    """
    Helper function to add an EmailMessage to the rabbitmq_queue.
    Requires https://github.com/delta/rabbitmq-smtp-mailer

    Returns True if message was added successfully
    """
    try:
        channel.basic_publish(
            exchange='',
            routing_key=environ.get('MAILER_RABBITMQ_QUEUE'),
            body=msg.as_bytes()
        )
        logger.info('Email(to={}) added to queue:\n'.format(msg['To']))

        return True
    except Exception as e:
        logger.error(e)

        return False


def get_message_with_headers():
    """
    Helper function to get a formatted EmailMessage.
    """
    msg = EmailMessage()
    msg.set_type('text/html; charset=UTF-8')
    msg['From'] = "Research Portal <no-reply@research.nitt.edu>"
    return msg


def send_project_creation_email(project: Project):
    """
    Helper function to send project creation email.
    """
    recepients = list(
        map(
            lambda x: x.email,
            get_project_members(project)
        )
    )

    # Add necessary emails to this list
    recepients.extend(['delta@nitt.edu'])

    msg = get_message_with_headers()
    msg['Subject'] = "A new project has been created!"
    msg['To'] = ', '.join(recepients)

    msg.set_content(f'''A new project has been added to the Research Portal.
Title: {project.name},
Abstract: {project.abstract},
Visit https://research.nitt.edu/project/{project.pk} to learn more.''')

    msg.add_alternative(get_html(
        content=f'''A new project has been added to the Research Portal.<br>
Title: {project.name}<br>
Abstract: {project.abstract}''',
        link=f'https://research.nitt.edu/project/{project.pk}',
        linkText="Click here to learn more"
    ), subtype="html")

    return send_email(msg)


def send_project_edit_email(project: Project):
    """
    Helper function to send project edit email.
    """
    recepients = get_project_members(project)

    # Add necessary emails to this list
    recepients.extend(['delta@nitt.edu'])

    msg = get_message_with_headers()
    msg['Subject'] = "A project has been edited!"
    msg['To'] = ', '.join(recepients)

    msg.set_content(f'''A project has been edited in the Research Portal.
Title: {project.name},
Abstract: {project.abstract},
Visit https://research.nitt.edu/project/{project.pk} to learn more.''')

    msg.add_alternative(get_html(
        content=f'''A project has been edited in the Research Portal.<br>
Title: {project.name}<br>
Abstract: {project.abstract}''',
        link=f'https://research.nitt.edu/project/{project.pk}',
        linkText="Click here to learn more"
    ), subtype="html")

    return send_email(msg)
