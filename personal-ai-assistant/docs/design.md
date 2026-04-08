# System Design & Architecture

This document outlines the core architecture and workflow of the multi-agent AI system built using the **Google Agent Development Kit (ADK)**. 

## 1. High-Level Architecture

The system utilizes an API-based architecture where users interact with a primary coordinator agent that dynamically assigns sub-tasks to specialized agents.

```mermaid
graph TD
    classDef user fill:#f9d0c4,stroke:#333,stroke-width:2px,color:#000;
    classDef api fill:#f9f0ff,stroke:#cc99ff,stroke-width:2px,color:#000;
    classDef agent fill:#e1f5fe,stroke:#03a9f4,stroke-width:2px,color:#000;
    classDef tool fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#000;
    classDef db fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#000;

    User([User]):::user -->|HTTP POST JSON| FastAPI[FastAPI Server]:::api
    FastAPI --> ADKFramework[Google ADK: Agent System]:::agent
    
    subgraph Google ADK Ecosystem
        Coordinator[Coordinator Agent]:::agent
        WorkspaceAgent[Workspace Sub-Agent]:::agent

        Coordinator -->|transfer_to_agent| WorkspaceAgent
    end

    ADKFramework --> Coordinator

    Coordinator --> Database[(SQLite Database\n- Memory\n- Logs)]:::db

    WorkspaceAgent <--> |MCP Protocol| WorkspaceMCP[Google Workspace MCP Server]:::tool
    
    WorkspaceMCP <--> |API| GoogleAPIs[Google Cloud / Workspace APIs]:::tool
```

## 2. Multi-Agent Workflow Example

This workflow illustrates a Workspace-oriented request (e.g. scheduling on Calendar via MCP):

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI
    participant Coordinator as Coordinator (ADK)
    participant Workspace as WorkspaceAgent (ADK)
    participant MCP as Google Workspace MCP
    participant DB as SQLite DB

    User->>API: POST /chat "Schedule a sync with John tomorrow at 2 PM"
    API->>Coordinator: Forward user prompt

    Coordinator->>DB: Log incoming request and retrieve session context
    DB-->>Coordinator: Context loaded

    Coordinator->>Workspace: transfer_to_agent (Workspace MCP tools)
    Workspace->>MCP: tools/call (e.g. calendar create / list)
    MCP-->>Workspace: Tool result
    Workspace-->>Coordinator: Natural-language reply

    Coordinator->>DB: Save updated session context and agent logs
    Coordinator-->>API: Format final response
    API-->>User: Confirmation
```

## 3. SQLite Database Schema

We use a simple SQLite database to satisfy the requirement for persistent structured data. 

```mermaid
erDiagram
    CONVERSATION {
        string session_id PK
        string user_id
        datetime created_at
        datetime updated_at
    }
    
    MESSAGE {
        string message_id PK
        string session_id FK
        string role "user, assistant, tool"
        text content
        datetime timestamp
    }
    
    AGENT_LOG {
        string log_id PK
        string session_id FK
        string agent_name "coordinator_agent, workspace_agent"
        string action_type
        text details
        datetime timestamp
    }

    CONVERSATION ||--o{ MESSAGE : contains
    CONVERSATION ||--o{ AGENT_LOG : tracks
```

## 4. Why Google ADK?
Using `google-adk` (instead of just passing raw prompts to `google-genai`) provides:
1. **First-class Agent Abstractions:** Built-in `Agent` classes that make tool calling and multi-agent delegation seamless.
2. **Declarative & Imperative Definitions:** Ability to define agents in YAML or Python configurations.
3. **MCP Support:** Easily bind external Model Context Protocol servers to specific agents (like exposing Google Workspace only to the workspace agent).
