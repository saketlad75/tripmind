# Instructions to Push Code to GitHub Branch UI_Kartik

Since Git is not available in the current terminal, please follow these steps manually:

## Step 1: Open Git Bash or Command Prompt with Git

1. Open Git Bash (if installed) or Command Prompt
2. Navigate to your project directory:
   ```bash
   cd "C:\Users\Admin\OneDrive\Desktop\Princeton"
   ```

## Step 2: Check Git Status

```bash
git status
```

## Step 3: Check Current Branch and Remote

```bash
git branch
git remote -v
```

## Step 4: Add Remote (if not already added)

If the remote is not set up, add it:
```bash
git remote add origin https://github.com/saketlad75/tripmind.git
```

## Step 5: Checkout or Create UI_Kartik Branch

If the branch doesn't exist locally:
```bash
git checkout -b UI_Kartik
```

If the branch exists:
```bash
git checkout UI_Kartik
```

## Step 6: Add All Changes

```bash
git add .
```

## Step 7: Commit Changes

```bash
git commit -m "Update TripMIND UI: Remove AI agent, update logo, improve chat functionality"
```

## Step 8: Push to Remote Branch

```bash
git push origin UI_Kartik
```

Or if it's the first push to this branch:
```bash
git push -u origin UI_Kartik
```

## Alternative: If Repository is in tripmind folder

If the git repository is actually in the `tripmind` folder, navigate there first:

```bash
cd "C:\Users\Admin\OneDrive\Desktop\Princeton\tripmind"
```

Then follow steps 2-8 above.

## Troubleshooting

- **If you get "not a git repository"**: Run `git init` first, then add the remote
- **If you get authentication errors**: You may need to set up GitHub credentials or use a personal access token
- **If branch doesn't exist on remote**: The `-u` flag will create it on first push

