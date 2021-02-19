from flask import Flask, render_template, url_for, redirect, flash, request
import time, subprocess, os

import sys
sys.path.append('/Users/kramer/Documents/DAT18b/4_semester/python/exam/GitFlask/model')
sys.path.append('/Users/kramer/Documents/DAT18b/4_semester/python/exam/GitFlask/modules')

# modules and classes created that needs to be imported
from modules.download_logos_web_crawler import download_github_logos
from modules.size_formatter import format_size

from model.username_form import UsernameForm
from model.result_table import ResultTable
from model.directory_table import DirectoryTable, DirectoryTableForClone

from model.github_account import GithubAccount
from model.github_handler import GithubHandler
from model.repository import Repository
from model.directory import Directory

app = Flask(__name__)
app.config['SECRET_KEY'] = 'c390c9de932d68e83f5d7a81d85cb5ed' # prevents cross site forgery

github_account = GithubAccount()
github_handler = GithubHandler()

repository = Repository()
directory = Directory()

# decorator which takes in the route from the url
@app.route('/')
def home_page():
    form = UsernameForm()

    if directory.has_error_changing_dir:
        flash(f'You are only allowed to change into folders', 'danger')
        directory.has_error_changing_dir = False


    if github_handler.has_executed_command == 'git-pull':
        if github_handler.folder_size['difference'] > 0:
            flash(f'Pull Succesful! Elements of {format_size(github_handler.folder_size["difference"])}'
                    + 'was added to the local repository which is now a total of '
                    + '{format_size(github_handler.folder_size["end_size"])}', 'success')
        
        elif github_handler.folder_size['difference'] < 0:
            flash(f'Pull Succesful! Elements of {format_size(github_handler.folder_size["difference"]*-1)} was removed from the local repository which is now a total of {format_size(github_handler.folder_size["end_size"])}', 'success')
        
        else:
            flash(f'Already up to date', 'info')
    
    
    elif github_handler.has_executed_command == 'git-add-commit':
        if github_handler.response_message_from_command:
            flash(f'{github_handler.response_message_from_command}', 'success')
        else:
            flash(f'Nothing to commit', 'warning')

    elif github_handler.has_executed_command == 'git-push':
        if 'Everything up-to-date' in github_handler.response_message_from_command:
            flash(f'{github_handler.response_message_from_command}. Try adding and commiting first', 'info')

        elif '.git' in github_handler.response_message_from_command.split('\n')[0][-4:]:
            flash(f'Pushed \'{os.getcwd().split("/")[-1]}\' To GitHub In {github_handler.time_spend} seconds', 'success')

        else:

            print(f'----\n {github_handler.response_message_from_command}')
            github_handler.response_message_from_command.split('\n')[0][-4:]
            flash(f'Maybe a merge confilt', 'danger')

    elif github_handler.has_executed_command == 'git-fetch':
            flash(f'Fetch Succesful', 'success')

    github_handler.has_executed_command = False

    table = DirectoryTable(directory.content)

    return render_template('home.html', title='Home', form=form, table=table, directory=directory) 

@app.route('/<command>')
def github_command_route(command):
    print(command)
    directory.content = os.listdir() # updates the content if any changes has happened
    
    if command == 'one_up':
        directory.change_dir('..')

    elif command == 'git-pull':
        github_handler.folder_size = github_handler.pull()
        
        github_handler.has_executed_command = command

    elif command == 'git-add-commit':
        github_handler.add_commit()

        github_handler.has_executed_command = command

    elif command == 'git-push':
        github_handler.time_spend = github_handler.push()
        
        github_handler.has_executed_command = command

    elif command == 'git-fetch':
        github_handler.fetch()
        
        github_handler.has_executed_command = command

    elif not command == '...':
        # Flask apparently tests the route by using '...',
        # so to avoid errors we check if the command is other than that
        directory.change_dir(command)
        
    return redirect(url_for('home_page'))

@app.route('/user')
def result_page():
    form = UsernameForm()

    # sets the account name to the name of the user
    github_account.username = request.args.get('username')
    
    github_account.fetch_repositories()
    table = ResultTable(github_account.repositories)

    if len(github_account)>0:
        flash(f'Found {len(github_account)} of {github_account.username}\'s repositories', 'success')
    
    
    return render_template('result.html', title='Results', form=form, table=table)


@app.route('/repository/<int:id>', methods=['GET', 'POST'])
def repository_page(id):
    form = UsernameForm()

    if directory.has_error_changing_dir:
        flash(f'You are only allowed to change into folders', 'danger')
        directory.has_error_changing_dir = False

    if github_handler.has_executed_command:
        flash(f'Succesfully cloned {repository.name} of {(format_size(github_handler.folder_size))} in {github_handler.time_spend} seconds', 'success')
        github_handler.has_executed_command = False
    
    # sets the repository to be the one we want to clone
    repository.id, repository.name, repository.created_at, repository.updated_at, repository.language, repository.clone_url = github_account.find_repo_with_gen(id)
    
    table = DirectoryTableForClone(directory.content)
    
    return render_template('repository.html', title=f'Clone \'{repository.name}\' to Folder...', form=form, repo=repository, table=table, directory=directory)


# NEW ROUTE FOR BACK BUTTON AND DIR LINK IN DIRECTORY TABLE'
@app.route('/repository/<string:command>')
def repository_command_route(command):

    if command == 'one_up':
        directory.change_dir('..')

    elif command == 'clone_here':
        github_handler.time_spend = github_handler.clone_repo(repository.clone_url)
        github_handler.folder_size = github_handler.find_size_of_folder(repository.name)
        directory.content = os.listdir()
        github_handler.has_executed_command = True

    elif not command == '...': # Flask apparently tests the route by using '...',
        # so to avoid errors we check if the command is other than that
        directory.change_dir(command)
        #directory += command
    
    return redirect(url_for('repository_page', id=repository.id))


@app.route('/change_logo')
@app.route('/change_logo/changed/<changed>')
def change_logo_page(changed=None):
    form = UsernameForm()

    logo_urls = download_github_logos(directory.base_dir_path)
    
    if changed:
        flash('Succesfully changed the logo. Hit refresh to see it', 'success')

    # generator
    url_for_path_to_downloaded_logos = (url_for('static', filename=f'logo_{i}.png') for i in range(len(logo_urls)))
    
    # list comp
    url_for_button_to_change_logo = [url_for('change_logo_command_page', filename=f'logo_{i}.png') for i in range(len(logo_urls))]

    return render_template('change_logo.html', title='Change Logo', form=form, enumerate=enumerate, 
        url_for_path_to_downloaded_logos=url_for_path_to_downloaded_logos, 
        url_for_button_to_change_logo=url_for_button_to_change_logo)

@app.route('/change_logo/<filename>')
def change_logo_command_page(filename):
        
    os.rename(f'{directory.base_dir_path}/static/{filename}',f'{directory.base_dir_path}/static/selected_logo.png')

    return redirect(url_for('change_logo_page', changed='success'))


# makes it runnable from python by typing 'python git_flask_app.py' in terminal
if __name__ == '__main__':
    app.run(debug=True)