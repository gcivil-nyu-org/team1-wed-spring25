# Git and Django Command Guide

## Checking Git Status
Check the current status of your Git repository.
```sh
git status
```

## Clearing the Terminal
Clear the terminal screen to improve readability.
```sh
clear
```

## Switching Branches
Switch to a different branch (replace `branch_name` as needed).
```sh
git checkout branch_name
```

Switch specifically to the `develop` branch.
```sh
git checkout develop
```

## Stashing Changes
Save changes temporarily to clean your working directory.
```sh
git stash
```

## Pulling Latest Changes
Ensure your `develop` branch is up-to-date with remote changes.
```sh
git pull
```

## Switching to Your Feature Branch
Switch back to your working branch (replace `asher` with your branch name).
```sh
git checkout asher
```

## Merging `develop` into Your Branch
Merge the latest `develop` branch changes into your feature branch.
```sh
git merge develop
```

## Adding All Changes
Stage all modified and new files for commit.
```sh
git add .
```

## Checking Git Status Again
Verify the staged changes before committing.
```sh
git status
```

## Committing Changes
Commit the staged changes with a descriptive message.
```sh
git commit -m "Asher changed front end"
```

## Pushing Changes
Push your committed changes to the remote repository.
```sh
git push
```

## Running Django Server
Run the Django development server.
```sh
python manage.py runserver
```
