# Component Diagrams - Telegram Bot Toko

## System Overview

```mermaid
graph TB
    subgraph External
        DROPBOX[Dropbox API]
        TELEGRAM[Telegram API]
    end

    subgraph Application
        SYNC[Sync Orchestrator]
        DOWN[Downloader Module]
        VALID[Validator Module]
        EXTRACT[Extractor Module]
        BOT[Bot Module]
    end

    subgraph Infrastructure
        DB[(PostgreSQL)]
        FILES[Data Storage]
        LOGS[Logs]
    end

    SYNC -->|1. Download| DOWN
    DOWN -->|2. Request| DROPBOX
    DROPBOX -->|3. Backup File| DOWN
    DOWN -->|4. Save| FILES
    FILES -->|5. Validate| VALID
    VALID -->|6. Valid| EXTRACT
    VALID -->|7. Invalid| SYNC

    EXTRACT -->|8. Restore| DB
    DB -->|9. Query| EXTRACT
    EXTRACT -->|10. Export| FILES

    BOT -->|11. Load| FILES
    BOT -->|12. Handle| TELEGRAM
    BOT -->|13. Log| LOGS
    SYNC -->|14. Log| LOGS
```

## Module Interactions

```mermaid
sequenceDiagram
    participant Cron as Cron/Scheduler
    participant Sync as Sync Orchestrator
    participant Down as Downloader
    participant Dropbox as Dropbox API
    participant Valid as Validator
    participant Extract as Extractor
    participant DB as PostgreSQL
    participant Bot as Bot Module
    participant Telegram as Telegram API

    Cron->>Sync: Trigger sync
    Sync->>Down: download_latest()
    Down->>Dropbox: Request latest backup
    Dropbox-->>Down: Backup file
    Down->>Sync: Backup saved

    Sync->>Valid: validate_backup()
    Valid->>Valid: Check file integrity
    Valid-->>Sync: Validation result

    Sync->>Extract: restore_database()
    Extract->>DB: Drop existing DB
    Extract->>DB: Create new DB
    Extract->>DB: Restore from backup
    DB-->>Extract: Restore complete

    Extract->>DB: Execute export query
    DB-->>Extract: Query results
    Extract->>Extract: Write to CSV

    Sync->>Valid: validate_csv()
    Valid->>Valid: Check CSV structure
    Valid-->>Sync: Validation result

    Sync->>Extract: cleanup_old_files()
    Extract->>Extract: Remove old CSVs

    Sync-->>Cron: Sync complete

    Note over Bot,Telegram: Bot runs independently
    User->>Telegram: Send message
    Telegram->>Bot: Webhook/Update
    Bot->>Bot: Load CSV
    Bot->>Bot: Search products
    Bot-->>Telegram: Send response
```

## Class Structure

```mermaid
classDiagram
    class AppConfig {
        +DropboxConfig dropbox
        +TelegramConfig telegram
        +DatabaseConfig database
        +PathConfig paths
        +int max_csv_files
        +int search_results_limit
    }

    class DropboxConfig {
        +str app_key
        +str app_secret
        +str refresh_token
        +str folder_path
    }

    class TelegramConfig {
        +str bot_token
        +list[int] allowed_users
    }

    class DatabaseConfig {
        +str host
        +int port
        +str database
        +str user
        +str password
    }

    class PathConfig {
        +Path project_root
        +Path data_dir
        +Path backups_dir
        +Path exports_dir
        +Path logs_dir
    }

    class DropboxDownloader {
        -DropboxConfig config
        -str access_token
        +refresh_access_token()
        +list_backups()
        +download_latest()
    }

    class DatabaseExtractor {
        -AppConfig config
        +ensure_database_running()
        +restore_database()
        +export_to_csv()
        +load_csv()
        +cleanup_old_files()
    }

    class DataValidator {
        +validate_backup_file()
        +validate_csv()
    }

    class TelegramBot {
        -AppConfig config
        -DataFrame df
        -Path csv_path
        +start()
        +reload_csv()
        +show_version()
        +search_products()
    }

    class SyncOrchestrator {
        -AppConfig config
        -DropboxDownloader downloader
        -DatabaseExtractor extractor
        -DataValidator validator
        +run_sync()
    }

    AppConfig --> DropboxConfig
    AppConfig --> TelegramConfig
    AppConfig --> DatabaseConfig
    AppConfig --> PathConfig

    DropboxDownloader --> DropboxConfig
    DatabaseExtractor --> AppConfig
    TelegramBot --> AppConfig
    SyncOrchestrator --> AppConfig
    SyncOrchestrator --> DropboxDownloader
    SyncOrchestrator --> DatabaseExtractor
    SyncOrchestrator --> DataValidator
```

## Data Flow Diagram

```mermaid
flowchart TD
    START([Start Sync]) --> AUTH[Authenticate with Dropbox]
    AUTH --> LIST[List backup files]
    LIST --> CHECK_FILES{Files found?}
    CHECK_FILES -->|No| ERROR([Error: No files])
    CHECK_FILES -->|Yes| SELECT[Select latest file]
    SELECT --> DOWNLOAD[Download backup]
    DOWNLOAD --> VALIDATE_BACKUP[Validate backup file]
    VALIDATE_BACKUP --> CHECK_VALID{Valid?}
    CHECK_VALID -->|No| ERROR
    CHECK_VALID -->|Yes| CHECK_DB{DB running?}
    CHECK_DB -->|No| START_DB[Start PostgreSQL]
    START_DB --> WAIT_DB[Wait for ready]
    WAIT_DB --> RESTORE
    CHECK_DB -->|Yes| RESTORE[Restore database]
    RESTORE --> EXPORT[Export to CSV]
    EXPORT --> VALIDATE_CSV[Validate CSV]
    VALIDATE_CSV --> CHECK_CSV{Valid?}
    CHECK_CSV -->|No| ERROR
    CHECK_CSV -->|Yes| CLEANUP[Cleanup old files]
    CLEANUP --> SUCCESS([Sync Complete])

    style SUCCESS fill:#90EE90
    style ERROR fill:#FFB6C1
```

## Deployment Architecture

```mermaid
graph TB
    subgraph Production Server
        subgraph Docker
            PG[PostgreSQL Container]
            BOT[Bot Container]
        end

        subgraph Filesystem
            DATA[data/]
            LOGS[logs/]
            CONFIG[.env]
        end

        subgraph Scripts
            SYNC[sync.py]
            CRON[Cron Jobs]
        end
    end

    subgraph External Services
        DROPBOX[Dropbox API]
        TELEGRAM[Telegram API]
    end

    CRON --> SYNC
    SYNC -->|read| CONFIG
    SYNC -->|download| DROPBOX
    SYNC -->|write| DATA
    SYNC -->|restore| PG
    SYNC -->|export| DATA

    BOT -->|read| CONFIG
    BOT -->|read| DATA
    BOT -->|write| LOGS
    BOT -->|communicate| TELEGRAM

    PG -->|mount| DATA
```

## Error Handling Flow

```mermaid
flowchart TD
    START([Operation Start]) --> TRY[Try Operation]
    TRY --> SUCCESS{Success?}
    SUCCESS -->|Yes| LOG_INFO[Log info]
    SUCCESS -->|No| CATCH{Catch Exception}

    CATCH --> TYPE{Exception Type?}

    TYPE -->|Network| RETRY[Retry with backoff]
    TYPE -->|File| LOG_ERROR[Log error]
    TYPE -->|Database| ROLLBACK[Rollback transaction]
    TYPE -->|Validation| SKIP[Skip current item]

    RETRY --> CHECK_RETRY{Max retries?}
    CHECK_RETRY -->|No| TRY
    CHECK_RETRY -->|Yes| LOG_ERROR

    LOG_ERROR --> NOTIFY[Send notification]
    LOG_INFO --> CONTINUE[Continue]
    ROLLBACK --> CONTINUE
    SKIP --> CONTINUE
    NOTIFY --> END([End])

    style NOTIFY fill:#FFB6C1
    style END fill:#90EE90
```

## State Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle: System Start
    Idle --> Downloading: Sync Triggered
    Downloading --> Validating: Download Complete
    Validating --> Restoring: Validation Passed
    Validating --> Idle: Validation Failed
    Restoring --> Exporting: Restore Complete
    Exporting --> Cleaning: Export Complete
    Cleaning --> Idle: Cleanup Complete

    Idle --> Listening: Bot Start
    Listening --> Processing: Message Received
    Processing --> Listening: Response Sent

    note right of Idle
        Ready for operations
    end note

    note right of Downloading
        Fetching from Dropbox
    end note

    note right of Validating
        Checking file integrity
    end note

    note right of Restoring
        Database operations
    end note

    note right of Exporting
        Generating CSV
    end note

    note right of Cleaning
        Removing old files
    end note

    note right of Listening
        Waiting for messages
    end note

    note right of Processing
        Handling user query
    end note
```

## Security Architecture

```mermaid
graph TB
    subgraph Security Layers
        L1[Layer 1: Network Security]
        L2[Layer 2: Application Security]
        L3[Layer 3: Data Security]
    end

    subgraph L1
        FIREWALL[Firewall Rules]
        TLS[TLS Encryption]
    end

    subgraph L2
        AUTH[Authentication]
        AUTHZ[Authorization]
        RATE[Rate Limiting]
    end

    subgraph L3
        ENCRYPT[Data Encryption]
        ACCESS[Access Control]
        AUDIT[Audit Logging]
    end

    FIREWALL --> TLS
    TLS --> AUTH
    AUTH --> AUTHZ
    AUTHZ --> RATE
    RATE --> ENCRYPT
    ENCRYPT --> ACCESS
    ACCESS --> AUDIT

    style L1 fill:#E1F5FE
    style L2 fill:#FFF3E0
    style L3 fill:#E8F5E9
```

## Monitoring & Observability

```mermaid
graph LR
    subgraph Application
        APP[App Code]
    end

    subgraph Logging
        STRUCT[Structured Logs]
        METRICS[Metrics]
        TRACES[Traces]
    end

    subgraph Storage
        LOG_FILES[Log Files]
        METRIC_DB[Time Series DB]
        TRACE_DB[Trace Storage]
    end

    subgraph Visualization
        DASH[Dashboard]
        ALERTS[Alerts]
    end

    APP --> STRUCT
    APP --> METRICS
    APP --> TRACES

    STRUCT --> LOG_FILES
    METRICS --> METRIC_DB
    TRACES --> TRACE_DB

    LOG_FILES --> DASH
    METRIC_DB --> DASH
    TRACE_DB --> DASH

    METRIC_DB --> ALERTS
    LOG_FILES --> ALERTS

    style DASH fill:#90EE90
    style ALERTS fill:#FFB6C1
```
