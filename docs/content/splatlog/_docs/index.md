Documentation Generation Support
==============================================================================

> 📝 NOTE
> 
> Much things break after auto-update refresh when running `novella` in 
> `--serve` mode. Has not been looked into yet.

Markdown File Linking Tests
------------------------------------------------------------------------------

We are in a **_docs file_** (`docs/content/**/*.md`) here.

1.  Hash Linking ❌
    
    > Appears to only be supported in source files. Attempts to render create
    > Markdown headers, which screw up the table of contents as they are `h1`
    > level.

2.  `@pylink` Tag Linking
    
    1.  Local `@pylink` tag (resolved by scope) ❌

        {@pylink BacktickPreprocessor}
        
        > There is no local context for markdown files.

    2.  Fully-qualified `@pylink` ✅

        {@pylink splatlog.rich_handler.RichHandler}

    3.  Stdlib `@pylink` tag ✅

        {@pylink typing.IO}

3.  Backtick Linking
    
    1.  Local backtick ❌

        `BacktickPreprocessor`
        
        > There is no local context for markdown files.

    2.  Fully-qualified backtick ✅

        `splatlog.rich_handler.RichHandler`

    3.  Stdlib backtick ✅

        `typing.IO`
        
    4.  Indirect backtick
        
        `splatlog.JSONFormatter`


Module Documentation
------------------------------------------------------------------------------

> Included via `@pydoc <MODULE_NAME>` tag.

***

@pydoc splatlog._docs

***
