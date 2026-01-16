# Tasks Document

- [x] 1. Create Refinement Package Structure
    - File: src/lorebinders/refinement/__init__.py
    - Create the package directory and empty init file
    - Purpose: Establish the module for refinement logic
    - _Leverage: none_
    - _Requirements: Code Architecture_
    - _Prompt: Create the refinement package directory and an empty __init__.py to establish the new module namespace._

- [x] 2. Implement EntityCleaner (TDD)
    - File: src/lorebinders/refinement/cleaner.py
    - File: tests/unit/refinement/test_cleaner.py
    - Implement `clean(binder, narrator_name)` function.
    - Port `remove_titles`, `clean_list`, `clean_str`, `clean_none_found` from v1 `data_cleaner.py`.
    - Port `ReplaceNarrator` logic.
    - Add regex for location standardization.
    - Purpose: Sanitize raw extraction data.
    - _Leverage: v1 src/lorebinders/data_cleaner.py_
    - _Requirements: Requirement 2 (Data Cleaning & Robustness)_
    - _Prompt: Implement the EntityCleaner class/functions in `src/lorebinders/refinement/cleaner.py`. Port the cleaning logic (junk word removal, location standardization, narrator replacement) from v1's `data_cleaner.py`. Follow TDD: Write comprehensive tests in `tests/unit/refinement/test_cleaner.py` covering all regex patterns and edge cases first._

- [x] 3. Implement EntityResolver (TDD)
    - File: src/lorebinders/refinement/resolver.py
    - File: tests/unit/refinement/test_resolver.py
    - Implement `resolve(binder)` function.
    - Port `DeduplicateKeys`, `to_singular`, `_is_similar_key`, `_merge_values` from v1 `data_cleaner.py`.
    - Purpose: Merge duplicate entities and combine their data.
    - _Leverage: v1 src/lorebinders/data_cleaner.py (DeduplicateKeys class)_
    - _Requirements: Requirement 1 (Aggregation & Deduplication)_
    - _Prompt: Implement the EntityResolver in `src/lorebinders/refinement/resolver.py`. Port the deduplication and merging logic from v1. It needs to handle singular/plural matching and attribute merging. Follow TDD: Create tests in `tests/unit/refinement/test_resolver.py` that verify correct merging of complex dicts and lists._

- [ ] 4. Implement EntitySummarizer (TDD)
    - File: src/lorebinders/refinement/summarizer.py
    - File: tests/unit/refinement/test_summarizer.py
    - Implement `summarize(binder, ai)` function.
    - Define prompt generation logic (reusing v1 concepts).
    - Purpose: Generate bio summaries for entities using AI.
    - _Leverage: v1 src/lorebinders/name_tools/name_summarizer.py_
    - _Requirements: Requirement 3 (Summarization)_
    - _Prompt: Implement the EntitySummarizer in `src/lorebinders/refinement/summarizer.py`. It should take a binder and an AIInterface, generate prompts for character summaries, and update the binder with the results. Follow TDD: Write tests in `tests/unit/refinement/test_summarizer.py` mocking the AIInterface to ensure correct prompt construction and response handling._

- [ ] 5. Implement RefinementManager to orchestrate pipeline
    - File: src/lorebinders/refinement/manager.py
    - File: tests/unit/refinement/test_manager.py
    - Create a coordination class/function that runs clean -> resolve -> summarize.
    - Purpose: Provide a single entry point for the builder.
    - _Requirements: Non-Functional (Code Architecture)_
    - _Prompt: Create a RefinementManager (or main entry function) that orchestrates the `clean`, `resolve`, and `summarize` steps in order. Ensure it passes data correctly between steps. Test the flow in `tests/unit/refinement/test_manager.py`._

- [ ] 6. Integrate into LoreBinderBuilder
    - File: src/lorebinders/build_lorebinder.py
    - Inject the refinement step after the processing loop and before PDF generation.
    - Purpose: Enable the feature in the main application flow.
    - _Requirements: Integration_
    - _Prompt: Integrate the refinement pipeline into `LoreBinderBuilder.build_binder` in `src/lorebinders/build_lorebinder.py`. Call the refinement manager after the chapter processing loop completes. Update tests to verify the integration._
