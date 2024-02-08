 @startuml
autonumber
actor User
participant API
participant Authentication
participant Connection
participant CRUD
participant Python
participant CClient

note right of User: User input payloads:\n- Qmgr (required)\n- Channel (required)\n- Queue (required)\n- Msg ID\n- CorrelID\n- Limit (default: 1, min: 1, max: 100)

User -> API: Give payload\nand token in header
alt Required inputs missing
    API --> User: Error 400 (Bad Request)\nMissing required inputs
else Required inputs provided
    alt Limit > 100 or Limit < 1
        API --> User: Error 400 (Bad Request)\nLimit must be between 1 and 100
    else Limit within valid range
        API -> Authentication: Generate token
        alt Token not valid
            Authentication --> API: Error 401
            API --> User: Error 401
        else Token valid
            Authentication -> Python: Set environment variable\nwith token
            Python --> Authentication: Environment variable set
            Authentication -> CClient: Consume token from environment variable
            CClient --> Authentication: Token consumed
            Authentication -> Connection: Establish connection
            alt Connection not established
                Connection --> API: Error 401
                API --> User: Error 401
            else Connection established
                Connection -> CRUD: Perform CRUD operations
                CRUD --> Connection: Close queue
                Connection --> API: Disconnect
                API --> User: CRUD operations completed successfully
            end
        end
    end
end
API -> Python: Pop environment variable
@enduml
