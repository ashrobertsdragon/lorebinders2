# LoreBinders Architecture

## Directory Structure

```txt
src/lorebinders/
├── main.py                     # Application Entry Point
├── build_lorebinder.py         # Main Orchestrator responsible for the build process
├── book.py                     # Domain Model: Book and Chapter classes
├── start_ai_initialization.py  # Factory for AI Providers & Rate Limiters
├── user_input.py               # CLI User Input Handling
├── _managers.py                # Abstract Base Classes (RateLimit, AIProvider, etc.)
├── ai/                         # AI interactions
│   ├── ai_interface.py         # Facade for AI Providers
│   └── rate_limiters/          # Rate limiting implementations
├── name_tools/                 # specialized logic modules
│   ├── name_extractor.py       # (Function) Extract names from text
│   ├── name_analyzer.py        # (Function) Analyze character details
│   └── name_summarizer.py      # (Function) Summarize findings
└── file_handling.py            # File I/O utilities
```

## System Workflow Diagram

This flowchart illustrates the high-level process from user input to final PDF generation.

```mermaid
flowchart TD
    User([User]) -->|Input Metadata| Main[main.py]
    Main -->|BookDict| Builder[build_lorebinder.py]

    subgraph BuilderProcess [LoreBinder Builder]
        Start["start()"] --> Convert[convert_book_file]
        Convert --> CreateBook[create_book]
        CreateBook --> InitAI[Initialize AI & RateLimiters]
        InitAI --> BuildBinder[build_binder]

        subgraph Processing Loop [For Each Chapter]
            direction TB
            ExtractNames[perform_ner]
            Analyze[analyze_names]
            UpdateBk[Update Book.binder]

            ExtractNames -->|RoleScript| Extractor[name_extractor]
            Extractor -->|Names| Chapter
            Chapter --> Analyze
            Analyze -->|RoleScript| Analyzer[name_analyzer]
            Analyzer -->|Analysis| UpdateBk
        end

        BuildBinder --> ProcessingLoop
        ProcessingLoop --> Summarize[summarize]
        Summarize --> Clean[data_cleaner.final_reshape]
        Clean --> PDF[make_pdf.create_pdf]
    end

    ProcessingLoop -.->|Uses| AI[AIInterface]
    AI -.->|API Calls| Provider[OpenAI / Other Providers]
```

## Class Diagram

This diagram shows the main classes and their relationships.

```mermaid
classDiagram
    direction TB

    class Main {
        +main()
    }

    class Builder {
        +start(BookDict, dir)
        +build_binder(ner, analyzer, metadata, book)
        +perform_ner(ai, metadata, chapter)
        +analyze_names(ai, metadata, chapter)
    }

    class Book {
        +BookDict metadata
        +List~Chapter~ chapters
        +Dict binder
        +_build_chapters()
        +add_binder()
    }

    class Chapter {
        +int number
        +str text
        +dict names
        +dict analysis
        +add_names(names)
        +add_analysis(analysis)
    }

    class AIInterface {
        +APIProvider provider
        +RateLimitManager limiter
        +generate()
        +call_api()
    }

    class AIProviderManager {
        <<Abstract>>
        +get_provider()
    }

    class RateLimitManager {
        <<Abstract>>
        +read()
        +write()
    }

    %% Relationships
    Main ..> Builder : invokes
    Builder ..> Book : creates & modifies
    Book *-- Chapter : contains

    Builder ..> AIInterface : uses

    AIInterface o-- RateLimitManager : uses
    AIInterface o-- AIProviderManager : via config

    %% Logic Modules (Functional)
    class NameExtractor {
        <<Module>>
        +extract_names()
        +build_role_script()
    }

    class NameAnalyzer {
        <<Module>>
        +analyze_names()
        +build_role_scripts()
    }

    Builder ..> NameExtractor : calls
    Builder ..> NameAnalyzer : calls
```
