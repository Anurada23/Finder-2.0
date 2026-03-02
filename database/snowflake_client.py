import snowflake.connector
from typing import Optional, List, Dict, Any
from config import settings
from utils import logger


class SnowflakeClient:
    """
    Manages Snowflake database connections and operations
    """
    
    def __init__(self):
        self.connection: Optional[snowflake.connector.SnowflakeConnection] = None
        self.config = {
            'account': settings.snowflake_account,
            'user': settings.snowflake_user,
            'password': settings.snowflake_password,
            'database': settings.snowflake_database,
            'schema': settings.snowflake_schema,
            'warehouse': settings.snowflake_warehouse
        }
    
    def connect(self):
        """Establish connection to Snowflake"""
        try:
            self.connection = snowflake.connector.connect(**self.config)
            logger.info("Connected to Snowflake successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise
    
    def disconnect(self):
        """Close Snowflake connection"""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from Snowflake")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of dictionaries representing rows
        """
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor(snowflake.connector.DictCursor)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            cursor.close()
            
            logger.debug(f"Query executed successfully: {len(results)} rows returned")
            return results
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_write(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            Number of rows affected
        """
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows_affected = cursor.rowcount
            self.connection.commit()
            cursor.close()
            
            logger.debug(f"Write query executed: {rows_affected} rows affected")
            return rows_affected
            
        except Exception as e:
            logger.error(f"Write query failed: {e}")
            self.connection.rollback()
            raise
    
    def initialize_tables(self):
        """Create necessary tables if they don't exist"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS research_sessions (
                session_id VARCHAR(100) PRIMARY KEY,
                user_query TEXT,
                agent_response TEXT,
                research_plan TEXT,
                sources_used TEXT,
                tokens_used INTEGER,
                cost FLOAT,
                created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS conversation_history (
                id VARCHAR(100) PRIMARY KEY,
                session_id VARCHAR(100),
                role VARCHAR(20),
                content TEXT,
                metadata VARIANT,
                created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (session_id) REFERENCES research_sessions(session_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agent_traces (
                id VARCHAR(100) PRIMARY KEY,
                session_id VARCHAR(100),
                agent_name VARCHAR(50),
                action TEXT,
                result TEXT,
                duration_ms INTEGER,
                created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (session_id) REFERENCES research_sessions(session_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS hotel_searches (
                search_id VARCHAR(100) PRIMARY KEY,
                session_id VARCHAR(100),
                user_id VARCHAR(100),
                location VARCHAR(255),
                checkin_date DATE,
                checkout_date DATE,
                guests INTEGER,
                budget DECIMAL(10,2),
                preferences TEXT,
                created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS hotel_results (
                result_id VARCHAR(100) PRIMARY KEY,
                search_id VARCHAR(100),
                hotel_name VARCHAR(255),
                price_per_night DECIMAL(10,2),
                total_price DECIMAL(10,2),
                rating DECIMAL(3,2),
                platform VARCHAR(50),
                booking_url TEXT,
                amenities TEXT,
                location_details TEXT,
                created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (search_id) REFERENCES hotel_searches(search_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS hotel_bookings (
                booking_id VARCHAR(100) PRIMARY KEY,
                search_id VARCHAR(100),
                user_id VARCHAR(100),
                hotel_name VARCHAR(255),
                checkin_date DATE,
                checkout_date DATE,
                guests INTEGER,
                total_price DECIMAL(10,2),
                booking_status VARCHAR(50),
                confirmation_code VARCHAR(100),
                payment_status VARCHAR(50),
                created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (search_id) REFERENCES hotel_searches(search_id)
            )
            """
        ]
        
        for query in queries:
            try:
                self.execute_write(query)
                logger.info("Table initialization query executed")
            except Exception as e:
                logger.warning(f"Table might already exist: {e}")


# Global Snowflake client instance
snowflake_client = SnowflakeClient()