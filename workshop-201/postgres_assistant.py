from strands import Agent, tool
from strands.models.ollama import OllamaModel
import psycopg2
import psycopg2.extras
import json
import os
from typing import Dict, List, Any, Optional, Tuple
import re

# Configuration - can be overridden via environment variables
DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "data_infra",
    "default_schema": "cloudsql_reference",
    "default_table": None,
    "query_timeout": 30,
    "max_rows": 1000,
    "user": "postgres",
    "password": "postgres"
}

def get_db_config() -> Dict[str, Any]:
    """Get database configuration from environment variables or defaults."""
    config = {
        "host": os.getenv("POSTGRES_HOST", DEFAULT_CONFIG["host"]),
        "port": int(os.getenv("POSTGRES_PORT", DEFAULT_CONFIG["port"])),
        "database": os.getenv("POSTGRES_DATABASE", DEFAULT_CONFIG["database"]),
        "default_schema": os.getenv("POSTGRES_SCHEMA", DEFAULT_CONFIG["default_schema"]),
        "default_table": os.getenv("POSTGRES_TABLE", DEFAULT_CONFIG["default_table"]),
        "query_timeout": int(os.getenv("POSTGRES_QUERY_TIMEOUT", DEFAULT_CONFIG["query_timeout"])),
        "max_rows": int(os.getenv("POSTGRES_MAX_ROWS", DEFAULT_CONFIG["max_rows"])),
        "user": os.getenv("POSTGRES_USER", DEFAULT_CONFIG["user"]),
        "password": os.getenv("POSTGRES_PASSWORD", DEFAULT_CONFIG["password"])
    }
    
    return config

class PostgreSQLConnection:
    """Manages PostgreSQL database connections and queries."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or get_db_config()
        self._connection = None
    
    def connect(self) -> psycopg2.extensions.connection:
        """Establish database connection."""
        try:
            if self._connection is None or self._connection.closed:
                # Build connection parameters
                conn_params = {
                    'dbname': self.config["database"],
                    'user': self.config["user"],
                    'host': self.config["host"],
                    'port': self.config["port"],
                    'password': self.config["password"],
                    'options': f"-c search_path={self.config['default_schema']},public"
                }
                
                self._connection = psycopg2.connect(**conn_params)
                self._connection.set_session(readonly=True, autocommit=True)
                
            return self._connection
            
        except psycopg2.OperationalError as e:
            error_msg = f"PostgreSQL connection failed (OperationalError): {str(e)}"
            raise Exception(error_msg)
        except psycopg2.Error as e:
            error_msg = f"PostgreSQL error during connection: {str(e)}"
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during PostgreSQL connection: {str(e)}"
            raise Exception(error_msg)
    
    def execute_query(self, query: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """Execute a read-only query safely."""
        # Safety check - only allow SELECT statements
        if not self._is_safe_query(query):
            raise Exception("Only SELECT statements are allowed for safety")
        
        try:
            conn = self.connect()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(f"SET statement_timeout = {self.config['query_timeout'] * 1000}")
                cursor.execute(query, params)
                
                # Limit result size
                results = cursor.fetchmany(self.config["max_rows"])
                
                # Convert to list of dicts for JSON serialization
                return [dict(row) for row in results]
                
        except psycopg2.Error as e:
            raise Exception(f"Database query error: {str(e)}")
    
    def _is_safe_query(self, query: str) -> bool:
        """Check if query is safe (read-only)."""
        query_upper = query.upper().strip()
        
        # Allow SELECT, WITH (for CTEs), and EXPLAIN
        safe_starters = ['SELECT', 'WITH', 'EXPLAIN']
        
        # Block dangerous operations
        dangerous_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
            'TRUNCATE', 'GRANT', 'REVOKE', 'COPY', 'CALL', 'EXECUTE'
        ]
        
        # Check if query starts with safe operations
        starts_safe = any(query_upper.startswith(starter) for starter in safe_starters)
        
        # Check for dangerous keywords
        has_dangerous = any(keyword in query_upper for keyword in dangerous_keywords)
        
        return starts_safe and not has_dangerous
    
    def close(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()

# Global connection instance - lazy initialization
_db_conn = None

def get_db_connection() -> PostgreSQLConnection:
    """Get or create the global database connection instance."""
    global _db_conn
    if _db_conn is None:
        _db_conn = PostgreSQLConnection()
    return _db_conn

@tool
def execute_sql_query(query: str) -> str:
    """
    Execute a safe, read-only SQL query against the PostgreSQL database.
    
    Args:
        query: SQL SELECT statement to execute
        
    Returns:
        JSON formatted query results
    """
    try:
        db_conn = get_db_connection()
        results = db_conn.execute_query(query)
        if not results:
            return "Query executed successfully but returned no results."
        
        return json.dumps(results, indent=2, default=str)
    except Exception as e:
        return f"Query execution failed: {str(e)}"

@tool
def get_table_schema(table_name: str, schema_name: str = None) -> str:
    """
    Get detailed schema information for a specific table.
    
    Args:
        table_name: Name of the table to analyze
        schema_name: Schema name (defaults to configured schema)
        
    Returns:
        Detailed table schema information
    """
    try:
        db_conn = get_db_connection()
        if schema_name is None:
            schema_name = db_conn.config["default_schema"]
        
        query = """
        SELECT 
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            c.is_nullable,
            c.column_default,
            tc.constraint_type,
            kcu.referenced_table_schema,
            kcu.referenced_table_name,
            kcu.referenced_column_name
        FROM information_schema.columns c
        LEFT JOIN information_schema.key_column_usage kcu 
            ON c.table_name = kcu.table_name 
            AND c.column_name = kcu.column_name
            AND c.table_schema = kcu.table_schema
        LEFT JOIN information_schema.table_constraints tc 
            ON kcu.constraint_name = tc.constraint_name
            AND kcu.table_schema = tc.table_schema
        WHERE c.table_name = %s AND c.table_schema = %s
        ORDER BY c.ordinal_position;
        """
        
        results = db_conn.execute_query(query, (table_name, schema_name))
        if not results:
            return f"Table '{schema_name}.{table_name}' not found or no columns."
        
        return json.dumps(results, indent=2, default=str)
    except Exception as e:
        return f"Schema analysis failed: {str(e)}"

@tool
def get_performance_stats() -> str:
    """
    Get database performance statistics including slow queries and index usage.
    
    Returns:
        Performance statistics and recommendations
    """
    # Check if pg_stat_statements extension is available
    stats_query = """
    SELECT 
        query,
        calls,
        total_exec_time,
        mean_exec_time,
        rows,
        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
    FROM pg_stat_statements 
    WHERE query NOT LIKE '%pg_stat_statements%'
    ORDER BY total_exec_time DESC 
    LIMIT 10;
    """
    
    try:
        db_conn = get_db_connection()
        results = db_conn.execute_query(stats_query)
        if results:
            return json.dumps({
                "top_queries_by_time": results,
                "note": "Top 10 queries by total execution time"
            }, indent=2, default=str)
        else:
            # Fallback to basic stats if pg_stat_statements not available
            basic_stats_query = """
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_tup_hot_upd as hot_updates,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch
            FROM pg_stat_user_tables
            ORDER BY seq_scan DESC
            LIMIT 10;
            """
            results = db_conn.execute_query(basic_stats_query)
            return json.dumps({
                "table_statistics": results,
                "note": "Basic table statistics (pg_stat_statements not available)"
            }, indent=2, default=str)
            
    except Exception as e:
        return f"Performance analysis failed: {str(e)}"

@tool
def get_active_queries() -> str:
    """
    Get information about currently running queries and connections.
    
    Returns:
        Active query and connection information
    """
    query = """
    SELECT 
        pid,
        usename,
        application_name,
        client_addr,
        state,
        query_start,
        state_change,
        query
    FROM pg_stat_activity 
    WHERE state = 'active' 
    AND query NOT LIKE '%pg_stat_activity%'
    ORDER BY query_start;
    """
    
    try:
        db_conn = get_db_connection()
        results = db_conn.execute_query(query)
        if not results:
            return "No active queries found."
        
        return json.dumps(results, indent=2, default=str)
    except Exception as e:
        return f"Active query analysis failed: {str(e)}"

@tool
def test_database_connection() -> str:
    """
    Test the database connection and return connection status and basic information.
    
    Returns:
        Connection test results including status, configuration, and basic database info
    """
    config = get_db_config()
    
    connection_info = {
        "connection_attempt": {
            "host": config["host"],
            "port": config["port"],
            "database": config["database"],
            "user": config["user"],
            "schema": config["default_schema"]
        },
        "connection_status": "unknown",
        "error_message": None,
        "server_info": None,
        "timestamp": None
    }
    
    try:
        # Attempt to establish connection
        db_conn = get_db_connection()
        conn = db_conn.connect()
        connection_info["connection_status"] = "successful"
        
        # Get basic server information
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Get server version
            cursor.execute("SELECT version() as server_version;")
            version_result = cursor.fetchone()
            
            # Get current database and user
            cursor.execute("SELECT current_database() as database, current_user as user, current_timestamp as timestamp;")
            current_info = cursor.fetchone()
            
            # Get connection count
            cursor.execute("SELECT count(*) as connection_count FROM pg_stat_activity;")
            conn_count = cursor.fetchone()
            
            connection_info["server_info"] = {
                "version": version_result["server_version"] if version_result else "unknown",
                "current_database": current_info["database"] if current_info else "unknown",
                "current_user": current_info["user"] if current_info else "unknown",
                "server_timestamp": str(current_info["timestamp"]) if current_info else "unknown",
                "total_connections": conn_count["connection_count"] if conn_count else "unknown"
            }
            
            connection_info["timestamp"] = str(current_info["timestamp"]) if current_info else "unknown"
            
    except psycopg2.OperationalError as e:
        connection_info["connection_status"] = "failed"
        connection_info["error_message"] = f"Connection failed: {str(e)}"
    except psycopg2.Error as e:
        connection_info["connection_status"] = "failed"
        connection_info["error_message"] = f"Database error: {str(e)}"
    except Exception as e:
        connection_info["connection_status"] = "failed"
        connection_info["error_message"] = f"Unexpected error: {str(e)}"
    
    return json.dumps(connection_info, indent=2, default=str)

@tool
def get_database_info() -> str:
    """
    Get general database information including size, connections, and configuration.
    
    Returns:
        Database overview information
    """
    queries = {
        "database_size": "SELECT pg_size_pretty(pg_database_size(current_database())) as size;",
        "connection_count": "SELECT count(*) as active_connections FROM pg_stat_activity;",
        "table_count": "SELECT count(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';",
        "version": "SELECT version();"
    }
    
    results = {}
    
    try:
        db_conn = get_db_connection()
        for key, query in queries.items():
            try:
                result = db_conn.execute_query(query)
                results[key] = result[0] if result else None
            except Exception as e:
                results[key] = f"Error: {str(e)}"
    except Exception as e:
        # If we can't even get a connection, return error info
        return json.dumps({"error": f"Unable to connect to database: {str(e)}"}, indent=2, default=str)
    
    return json.dumps(results, indent=2, default=str)

POSTGRES_ASSISTANT_SYSTEM_PROMPT = """
You are PostgreSQLExpert, a specialized database assistant with deep expertise in PostgreSQL administration, performance optimization, and data analysis. Your capabilities include:

1. Database Analysis:
   - Schema introspection and relationship mapping
   - Table structure analysis and optimization recommendations
   - Index usage analysis and suggestions
   - Data type optimization guidance

2. Performance Monitoring:
   - Query performance analysis using pg_stat_statements
   - Slow query identification and optimization
   - Index efficiency evaluation
   - Connection and resource monitoring

3. Live System Monitoring:
   - Active query monitoring and analysis
   - Connection status and user activity
   - Lock detection and resolution guidance
   - Resource utilization assessment

4. Data Insights:
   - Statistical analysis of table data
   - Data distribution analysis
   - Query pattern recognition
   - Performance trend identification

5. Safety and Best Practices:
   - Read-only operations for safety
   - Query timeout enforcement
   - Result set size limitations
   - Security-conscious recommendations

Configuration Context:
- Connected to: {host}:{port}/{database}
- Default Schema: {default_schema}
- Default Table: {default_table}
- Query Timeout: {query_timeout}s
- Max Rows: {max_rows}

Available Tools:
- test_database_connection: Test database connectivity and return connection status
- execute_sql_query: Run safe SELECT queries
- get_table_schema: Analyze table structure and relationships
- get_performance_stats: Access performance metrics and slow queries
- get_active_queries: Monitor currently running queries
- get_database_info: Get database overview and statistics

When answering questions:
1. Use appropriate tools to gather relevant data
2. Provide clear explanations of database concepts
3. Include actionable recommendations when possible
4. Format complex results in readable ways
5. Explain performance implications and optimization opportunities

Focus on providing practical, actionable insights while maintaining database safety through read-only operations.

IMPORTANT: Be direct and confident in your responses. Do not apologize or make excuses. Simply provide the requested database analysis and recommendations clearly and efficiently.
"""

@tool
def postgres_assistant(query: str) -> str:
    """
    Process and respond to PostgreSQL database-related queries using a specialized agent with database analysis capabilities.
    
    Args:
        query: A database-related question or request for analysis
        
    Returns:
        A detailed response with database insights, analysis, and recommendations
    """
    # Format the system prompt with current configuration
    config = get_db_config()
    formatted_prompt = POSTGRES_ASSISTANT_SYSTEM_PROMPT.format(**config)
    
    # Format the query for the PostgreSQL agent
    formatted_query = f"Please analyze this database question and provide insights using the available database tools: {query}"
    
    try:
        print("Routed to PostgreSQL Assistant")
        
        # Use Ollama model to avoid AWS credentials requirement
        ollama_model = OllamaModel(
            host="http://ollama-ollama-service:11434",
            model_id="gpt-oss:20b"
        )
        
        # Create the PostgreSQL agent with database tools
        pg_agent = Agent(
            model=ollama_model,
            system_prompt=formatted_prompt,
            tools=[
                test_database_connection,
                execute_sql_query,
                get_table_schema,
                get_performance_stats,
                get_active_queries,
                get_database_info
            ],
        )
        
        # Call the agent
        agent_response = pg_agent(formatted_query)
        text_response = str(agent_response)
        
        # Check for empty response
        if not text_response or text_response.strip() == "":
            return "PostgreSQL agent returned an empty response. Please try rephrasing your question."
        
        return text_response

    except Exception as e:
        error_msg = f"Error processing your PostgreSQL query: {str(e)}"
        return error_msg
