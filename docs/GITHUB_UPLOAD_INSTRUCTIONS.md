# Publish this repository on GitHub

1. Sign in to GitHub and choose **New repository**. Suggested name: `breast-cancer-bounded-workflow`. Choose Public only if you are authorized to release the manuscript-related code and derived data.
2. **Create repository** without adding an initial README, license or gitignore (these are already included).
3. Extract the GitHub-ready ZIP locally. From inside the extracted repository root run:

   ```bash
   git init
   git add .
   git commit -m "Release reproducible breast cancer bounded workflow benchmark"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/breast-cancer-bounded-workflow.git
   git push -u origin main
   ```

4. Replace `YOUR-USERNAME` with your GitHub account. Alternatively choose **Add file > Upload files** in the new GitHub repo and drag in the *contents of the extracted folder* (not the ZIP itself). GitHub web upload has per-file and number-of-file constraints; git push is more reliable.
5. After publication, copy your actual public GitHub URL into the manuscript's code availability statement and reviewer response. Verify access from a signed-out browser window.
6. Optionally archive a tagged release with Zenodo to obtain a version-specific DOI; record the archived version in the manuscript.

Do not claim the repo reproduces the original external molecular analyses without those external inputs.
