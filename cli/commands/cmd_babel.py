import os
import subprocess

import click


APP_NAME = 'snakeeyes'
BABEL_I18N_PATH = os.path.join(APP_NAME, 'translations')
MESSAGES_PATH = os.path.join(APP_NAME, 'translations', 'messages.pot')


@click.group()
def cli():
    """ Manage i18n translations. """
    pass


@click.command()
def extract():
    """
    Extract strings into a pot file.

    :return: Subprocess call result
    """
    babel_cmd = 'pybabel extract -F babel.cfg -k lazy_gettext ' \
                '-o {0} {1}'.format(MESSAGES_PATH, APP_NAME)
    return subprocess.call(babel_cmd, shell=True)


@click.option('--language', default=None, help='The output language, ex. de')
@click.command()
def init(language=None):
    """
    Map translations to a different language.

    :return: Subprocess call result
    """
    babel_cmd = 'pybabel init -i {0} -d {1} -l {2}'.format(MESSAGES_PATH,
                                                           BABEL_I18N_PATH,
                                                           language)
    return subprocess.call(babel_cmd, shell=True)


@click.command()
def compile():
    """
    Compile new translations. Remember to remove #, fuzzy lines.

    :return: Subprocess call result
    """
    babel_cmd = 'pybabel compile -d {0}'.format(BABEL_I18N_PATH)
    return subprocess.call(babel_cmd, shell=True)


@click.command()
def update():
    """
    Update existing translations.

    :return: Subprocess call result
    """
    babel_cmd = 'pybabel update -i {0} -d {1}'.format(MESSAGES_PATH,
                                                      BABEL_I18N_PATH)
    return subprocess.call(babel_cmd, shell=True)


cli.add_command(extract)
cli.add_command(init)
cli.add_command(compile)
cli.add_command(update)
