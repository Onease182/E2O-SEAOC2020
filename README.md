# E2O-SEAOC2020
#### Python source code accompanying the Goings et al. (2020) paper published in the SEAOC 2020 proceedings

Hi fellow engineers! This is an open-source library of Python functions for converting the ETABS model included within the `models` directory into a nonlinear OpenSees equivalent and running a response history analysis on the nonlinear OpenSees model.
The ideas implemented in this library are readily extensible to other ETABS models developed with the methodology explained in our paper. However, we 
currently limit the scope of this library to the enclosed model.

#### Recommended steps to use this library:

1. Clone the repository rather than running `git pull` in an ordinary folder:
   ```bat
   git clone https://github.com/Onease182/E2O-SEAOC2020.git
   cd E2O-SEAOC2020
   ```
2. Install the dependencies from the repository root:
   ```bat
   python -m pip install -r requirements.txt
   ```
3. Open the enclosed ETABS model and keep ETABS running while the script executes.
4. Run the application from any directory with:
   ```bat
   python src\main.py
   ```

The application resolves worksheet, ground-motion, and results paths from the repository location, so it no longer depends on the current working directory. ETABS and OpenSeesPy are runtime requirements for the full analysis; importing the modules on another platform now gives a clear dependency error instead of failing during module import.

The dependency versions are intentionally not pinned because OpenSeesPy publishes platform-specific wheels. The required packages are listed in [`requirements.txt`](requirements.txt).
  
If you would like to propose changes, please submit a pull requests from your fork.

#### Helpful links to learn more about GitHub workflow:

  - [Forks](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-forks)
  - [Pull Requests](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests)
  - [Creating Pull Requests from Forks](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork)
  
Feel free to submit bugs or ideas for enhancements as [issues](https://guides.github.com/features/issues/) directly to this repository.

Thanks for your interest in this library!
