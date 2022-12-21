splatlog
==============================================================================

Python logger that accepts ** values and prints 'em out.

Because I'll forget, and because I know I'll look here when I do...

Publishing
------------------------------------------------------------------------------

1.  Update the version in `pyproject.toml`.
    
2.  Commit, tag `vX.Y.Z`, push.
    
3.  Log in to [PyPI](https://pypi.org) and go to
    
    https://pypi.org/manage/account/
    
    to generate an API token.
    
4.  Throw `poetry` at it:
    
        poetry publish --build --username __token__ --password <token>
    
5.  Bump patch by 1 and append `a0`, commit and push (now we're on the "alpha"
    of the next patch version).

Bulding Docs
------------------------------------------------------------------------------

    poetry run novella -d ./docs
    
Serving them:

    poetry run novella -d ./docs --serve
    

Running Tests
------------------------------------------------------------------------------

All of them:

    poetry run dr.t ./splatlog/**/*.py ./docs/content/**/*.md

Single file, fail-fast, printing header panel (so you can find where they
start and end easily during repeated runs):

    poetry run dr.t -fp <filename>
