# cBioPortal MCP Server - System Architecture Diagram

## 🏗️ High-Level System Architecture

```mermaid
graph TB
    %% External Interfaces
    subgraph "AI Assistants & Clients"
        Claude[Claude Desktop]
        VSCode[VS Code MCP]
        CLI[Command Line]
        CustomAI[Custom AI Tools]
    end

    %% MCP Protocol Layer
    subgraph "MCP Protocol Layer"
        MCP[Model Context Protocol]
        FastMCP[FastMCP Framework]
    end

    %% Main Server Components
    subgraph "cBioPortal MCP Server"
        direction TB
        Server[CBioPortalMCPServer]
        Config[Configuration System]
        APIClient[APIClient]
        
        %% Endpoint Modules
        subgraph "Endpoint Modules (BaseEndpoint Pattern)"
            Base[BaseEndpoint<br/>• Pagination Logic<br/>• Error Handling<br/>• Validation Decorators]
            Studies[StudiesEndpoints<br/>• Cancer Studies<br/>• Study Search]
            Genes[GenesEndpoints<br/>• Gene Operations<br/>• Mutations<br/>• Batch Processing]
            Samples[SamplesEndpoints<br/>• Sample Data<br/>• Sample Lists]
            Molecular[MolecularProfilesEndpoints<br/>• Clinical Data<br/>• Gene Panels]
        end
        
        %% Utility Modules
        subgraph "Utility Modules"
            Pagination[Pagination Utils<br/>• Async Generators<br/>• Efficient Streaming]
            Validation[Input Validation<br/>• Parameter Checking<br/>• Type Safety]
            Logging[Logging System<br/>• Structured Logs<br/>• Debug Support]
        end
    end

    %% External Data Source
    subgraph "External Data Sources"
        cBioPortal[cBioPortal API<br/>• Cancer Studies<br/>• Genomic Data<br/>• Clinical Data]
    end

    %% Data Flow Connections
    Claude --> MCP
    VSCode --> MCP
    CLI --> MCP
    CustomAI --> MCP
    
    MCP --> FastMCP
    FastMCP --> Server
    
    Server --> Config
    Server --> APIClient
    Server --> Studies
    Server --> Genes
    Server --> Samples
    Server --> Molecular
    
    Studies --> Base
    Genes --> Base
    Samples --> Base
    Molecular --> Base
    
    Base --> Pagination
    Base --> Validation
    Base --> Logging
    
    APIClient --> cBioPortal
    
    %% Styling
    classDef serverClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef endpointClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef utilClass fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef externalClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef protocolClass fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    class Server,Config,APIClient serverClass
    class Studies,Genes,Samples,Molecular,Base endpointClass
    class Pagination,Validation,Logging utilClass
    class Claude,VSCode,CLI,CustomAI,cBioPortal externalClass
    class MCP,FastMCP protocolClass
```

## 🔄 Data Flow Architecture

```mermaid
sequenceDiagram
    participant AI as AI Assistant
    participant MCP as MCP Protocol
    participant Server as CBioPortalMCPServer
    participant Endpoint as Endpoint Module
    participant Base as BaseEndpoint
    participant API as APIClient
    participant cBio as cBioPortal API

    AI->>MCP: Request cancer studies
    MCP->>Server: Tool invocation
    Server->>Endpoint: Delegate to StudiesEndpoints
    Endpoint->>Base: Inherit pagination & validation
    Base->>Base: Validate parameters
    Base->>Base: Apply pagination logic
    Base->>API: Make async HTTP request
    API->>cBio: GET /studies
    cBio-->>API: JSON response
    API-->>Base: Processed data
    Base->>Base: Apply response formatting
    Base-->>Endpoint: Paginated response
    Endpoint-->>Server: Structured data
    Server-->>MCP: MCP response format
    MCP-->>AI: Tool result
```

## 🧩 Component Architecture Details

```mermaid
graph LR
    subgraph "Configuration System"
        CLI_Args[CLI Arguments<br/>Highest Priority]
        Env_Vars[Environment Variables<br/>CBIOPORTAL_*]
        YAML_Config[YAML Config Files<br/>config.yaml]
        Defaults[Default Values<br/>Lowest Priority]
        
        CLI_Args --> Config_Merger[Configuration Merger]
        Env_Vars --> Config_Merger
        YAML_Config --> Config_Merger
        Defaults --> Config_Merger
        Config_Merger --> Final_Config[Final Configuration]
    end

    subgraph "BaseEndpoint Pattern (60% Duplication Reduction)"
        BaseEndpoint[BaseEndpoint Class]
        Decorators[Validation Decorators<br/>@validate_paginated_params<br/>@handle_api_errors]
        Pagination_Logic[Shared Pagination Logic<br/>paginated_request()]
        Error_Handling[Centralized Error Handling]
        
        BaseEndpoint --> Decorators
        BaseEndpoint --> Pagination_Logic
        BaseEndpoint --> Error_Handling
    end

    subgraph "Async Performance Layer"
        AsyncClient[httpx.AsyncClient<br/>480s timeout]
        Concurrent[Concurrent Operations<br/>asyncio.gather()]
        Batching[Smart Batching<br/>Configurable sizes]
        Streaming[Async Generators<br/>Memory efficient]
        
        AsyncClient --> Concurrent
        Concurrent --> Batching
        Batching --> Streaming
    end
```

## 🛡️ Error Handling & Validation Flow

```mermaid
graph TD
    Request[Incoming Request] --> Validation{Parameter Validation}
    Validation -->|Invalid| ValidationError[Validation Error<br/>TypeError/ValueError]
    Validation -->|Valid| APICall[API Request]
    
    APICall --> APIResponse{API Response}
    APIResponse -->|HTTP Error| HTTPError[HTTP Error Handler<br/>4xx/5xx responses]
    APIResponse -->|Network Error| NetworkError[Network Error Handler<br/>Timeouts/Connection]
    APIResponse -->|Success| DataProcessing[Data Processing]
    
    DataProcessing --> Pagination[Pagination Logic]
    Pagination --> Response[Formatted Response]
    
    ValidationError --> ErrorResponse[Error Response]
    HTTPError --> ErrorResponse
    NetworkError --> ErrorResponse
    
    Response --> Client[Return to Client]
    ErrorResponse --> Client
```

## 🚀 Performance Optimization Architecture

```mermaid
graph TB
    subgraph "Performance Layer"
        direction TB
        
        subgraph "Async Concurrency"
            Sequential[Sequential Operations<br/>1.31s for 10 studies]
            Concurrent[Concurrent Operations<br/>0.29s for 10 studies<br/>4.57x improvement]
            Sequential -.->|Optimized to| Concurrent
        end
        
        subgraph "Smart Batching"
            LargeRequest[Large Gene List Request]
            BatchSplitter[Batch Splitter<br/>Configurable size: 100]
            ConcurrentBatches[Concurrent Batch Processing<br/>asyncio.gather()]
            BatchMerger[Result Merger]
            
            LargeRequest --> BatchSplitter
            BatchSplitter --> ConcurrentBatches
            ConcurrentBatches --> BatchMerger
        end
        
        subgraph "Memory Efficiency"
            AsyncGenerator[Async Generators<br/>yield results]
            StreamingPagination[Streaming Pagination<br/>Low memory footprint]
            LazyLoading[Lazy Loading<br/>On-demand processing]
            
            AsyncGenerator --> StreamingPagination
            StreamingPagination --> LazyLoading
        end
    end
```

## 🧪 Testing Architecture

```mermaid
graph LR
    subgraph "Test Suite (93 Tests)"
        direction TB
        
        Lifecycle[Lifecycle Tests<br/>• Server startup/shutdown<br/>• Tool registration<br/>• Resource management]
        
        Pagination[Pagination Tests<br/>• Edge cases<br/>• Async generators<br/>• Memory efficiency]
        
        MultiEntity[Multi-Entity Tests<br/>• Concurrent operations<br/>• Batch processing<br/>• Error handling]
        
        Validation[Input Validation Tests<br/>• Parameter checking<br/>• Type safety<br/>• Error messages]
        
        Snapshot[Snapshot Tests<br/>• API response consistency<br/>• Data integrity<br/>• Regression prevention]
        
        CLI[CLI Tests<br/>• Argument parsing<br/>• Configuration<br/>• Error handling]
        
        ErrorHandling[Error Handling Tests<br/>• Network failures<br/>• API errors<br/>• Graceful degradation]
        
        Configuration[Configuration Tests<br/>• Multi-layer config<br/>• Environment variables<br/>• Validation]
    end
    
    subgraph "Quality Infrastructure"
        Ruff[Ruff Linting<br/>• Code quality<br/>• Formatting<br/>• Import sorting]
        
        TypeChecking[Type Checking<br/>• Static analysis<br/>• Type safety<br/>• IDE support]
        
        Coverage[Code Coverage<br/>• pytest-cov<br/>• Comprehensive metrics<br/>• Quality gates]
    end
```

## 🔧 Configuration Architecture

```mermaid
graph TD
    subgraph "Configuration Sources (Priority Order)"
        CLI[1. CLI Arguments<br/>--base-url, --config, etc.]
        ENV[2. Environment Variables<br/>CBIOPORTAL_BASE_URL<br/>CBIOPORTAL_GENE_BATCH_SIZE]
        YAML[3. YAML Configuration<br/>config.yaml files]
        DEFAULT[4. Default Values<br/>Built-in defaults]
    end
    
    subgraph "Configuration Processing"
        Loader[Configuration Loader]
        Validator[Configuration Validator<br/>• Type checking<br/>• Range validation<br/>• Required fields]
        Merger[Configuration Merger<br/>Deep merge with priority]
    end
    
    subgraph "Configuration Categories"
        Server[Server Settings<br/>• base_url<br/>• transport<br/>• timeout]
        Logging[Logging Settings<br/>• level<br/>• format<br/>• file output]
        API[API Settings<br/>• rate limiting<br/>• retry logic<br/>• batch sizes]
        Performance[Performance Settings<br/>• concurrent limits<br/>• timeout values<br/>• cache settings]
    end
    
    CLI --> Loader
    ENV --> Loader
    YAML --> Loader
    DEFAULT --> Loader
    
    Loader --> Validator
    Validator --> Merger
    Merger --> Server
    Merger --> Logging
    Merger --> API
    Merger --> Performance
```

## 📊 Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        Dev[Local Development<br/>uv sync<br/>pytest<br/>ruff check]
    end
    
    subgraph "AI Assistant Integration"
        Claude[Claude Desktop<br/>MCP Configuration]
        VSCode[VS Code Extension<br/>MCP Integration]
        Custom[Custom Applications<br/>MCP SDK]
    end
    
    subgraph "cBioPortal MCP Server"
        Server[Production Server<br/>Configuration-driven<br/>Multi-transport support]
    end
    
    subgraph "External Services"
        Public[Public cBioPortal<br/>www.cbioportal.org]
        Private[Private Instances<br/>Custom deployments]
    end
    
    Dev --> Server
    Claude --> Server
    VSCode --> Server
    Custom --> Server
    
    Server --> Public
    Server --> Private
```

---

## 🎯 Key Architectural Principles

1. **🏗️ BaseEndpoint Pattern**: Inheritance-based architecture eliminating 60% code duplication
2. **⚡ Async-First Design**: Full asynchronous implementation for maximum performance
3. **🔧 Modular Architecture**: Clear separation of concerns with domain-specific modules
4. **🛡️ Robust Error Handling**: Comprehensive validation and error management
5. **🚀 Performance Optimized**: Smart batching, concurrent operations, and memory efficiency
6. **🧪 Test-Driven Quality**: 93 comprehensive tests ensuring reliability
7. **⚙️ Configuration-Driven**: Multi-layer configuration for flexible deployment
8. **📊 Production-Ready**: Enterprise-grade architecture with monitoring and observability

This architecture demonstrates a mature, production-ready bioinformatics platform built through innovative human-AI collaboration.