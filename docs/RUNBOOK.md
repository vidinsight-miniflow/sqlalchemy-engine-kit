# Operations Runbook

## Common Issues and Solutions

### Issue 1: Connection Pool Exhausted

**Symptoms:**
- Application hangs or times out
- Error: `QueuePool limit exceeded`
- Error: `Timeout waiting for connection from pool`

**Diagnosis:**
```python
from sqlalchemy_engine_kit import DatabaseManager

manager = DatabaseManager.get_instance()
health = manager.get_health_status()

print(f"Pool size: {health['pool']['size']}")
print(f"Active connections: {health['pool']['checked_out']}")
print(f"Idle connections: {health['pool']['checkedin']}")
print(f"Overflow: {health['pool']['overflow']}")
```

**Solutions:**

1. **Immediate Fix (Restart Application)**
   ```bash
   # Gracefully restart application
   kill -SIGTERM <pid>
   
   # Or force restart if necessary
   systemctl restart myapp
   ```

2. **Increase Pool Size**
   ```python
   config = EngineConfig(
       pool_size=30,        # Increase from 20
       max_overflow=15      # Increase from 10
   )
   ```

3. **Find Connection Leaks**
   ```python
   # Enable session tracking
   manager.engine.enable_session_tracking()
   
   # Check for unclosed sessions
   active_sessions = manager.engine.get_active_sessions()
   print(f"Active sessions: {len(active_sessions)}")
   
   # Common causes:
   # - Not using context managers
   # - Exceptions preventing session.close()
   # - Long-running queries
   ```

4. **Code Fix (Always use decorators or context managers)**
   ```python
   # ✅ GOOD: Auto-cleanup
   from sqlalchemy_engine_kit import with_session
   
   @with_session()
   def get_user(session, user_id):
       return session.query(User).get(user_id)
   
   # ✅ GOOD: Explicit cleanup
   with manager.engine.session_context() as session:
       user = session.query(User).get(user_id)
   
   # ❌ BAD: Manual management (risky)
   session = manager.engine.get_session()
   user = session.query(User).get(user_id)
   session.close()  # Might not run if exception occurs!
   ```

**Prevention:**
- Monitor `db_pool_active` metric
- Alert when active connections > 80% of pool_size
- Review code for missing session cleanup
- Use linting to detect manual session management

---

### Issue 2: Database Connection Lost

**Symptoms:**
- Error: `OperationalError: (psycopg2.OperationalError) server closed the connection`
- Error: `MySQL server has gone away`
- Intermittent connection failures

**Diagnosis:**
```python
# Check engine health
health = manager.get_health_status()
print(f"Engine alive: {health['is_alive']}")
print(f"Can connect: {health['can_connect']}")
print(f"Last checked: {health['last_health_check']}")
```

**Solutions:**

1. **Enable Connection Pre-Ping** (Recommended)
   ```python
   config = EngineConfig(
       pool_pre_ping=True,    # Test connections before use
       pool_recycle=3600      # Recycle after 1 hour
   )
   ```

2. **Restart Engine**
   ```python
   try:
       manager.stop()
       manager.start()
       print("Engine restarted successfully")
   except Exception as e:
       print(f"Failed to restart: {e}")
   ```

3. **Check Network Connectivity**
   ```bash
   # Test database connection
   psql -h db.example.com -U app_user -d myapp
   
   # Check firewall rules
   telnet db.example.com 5432
   
   # Check DNS resolution
   nslookup db.example.com
   ```

4. **Review Database Server Logs**
   ```bash
   # PostgreSQL
   tail -f /var/log/postgresql/postgresql-12-main.log
   
   # Look for:
   # - Connection timeouts
   # - Max connections exceeded
   # - Server restarts
   ```

**Prevention:**
- Always set `pool_pre_ping=True` in production
- Set `pool_recycle` to less than database timeout
- Monitor database server health
- Set up database connection alerts

---

### Issue 3: Slow Queries

**Symptoms:**
- Application slow or timing out
- High CPU on database server
- `db_query_duration_seconds` metric elevated

**Diagnosis:**
```python
# Enable query logging temporarily
config = EngineConfig(echo=True)  # Logs all SQL queries

# Monitor query times in application logs
# Look for queries taking >1 second
```

**Solutions:**

1. **Identify Slow Queries**
   ```sql
   -- PostgreSQL: Find slow queries
   SELECT 
       query,
       calls,
       mean_exec_time,
       max_exec_time
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   
   -- MySQL: Find slow queries
   SELECT * FROM mysql.slow_log
   ORDER BY query_time DESC
   LIMIT 10;
   ```

2. **Add Database Indexes**
   ```python
   # Example: Index frequently queried columns
   from sqlalchemy import Index
   
   class User(Base):
       __tablename__ = 'users'
       email = Column(String(255), nullable=False)
       
       # Add index
       __table_args__ = (
           Index('idx_user_email', 'email'),
       )
   ```

3. **Use Eager Loading (Fix N+1 Queries)**
   ```python
   from sqlalchemy_engine_kit import eager_load
   
   # ❌ BAD: N+1 queries
   users = session.query(User).all()
   for user in users:
       print(user.posts)  # Separate query per user!
   
   # ✅ GOOD: Single query with join
   users = eager_load(
       session.query(User),
       'posts', 'posts.comments'  # Load relationships
   ).all()
   ```

4. **Add Query Pagination**
   ```python
   from sqlalchemy_engine_kit import paginate_with_meta
   
   # Instead of loading all records
   result = paginate_with_meta(
       session.query(User),
       page=1,
       page_size=50
   )
   ```

**Prevention:**
- Monitor query performance metrics
- Review ORM-generated SQL in development
- Add database indexes for frequently queried columns
- Use `EXPLAIN ANALYZE` to understand query plans
- Set query timeout limits

---

### Issue 4: Memory Leak

**Symptoms:**
- Application memory usage grows over time
- Eventually crashes with OOM (Out of Memory)
- Server becomes unresponsive

**Diagnosis:**
```python
import tracemalloc
tracemalloc.start()

# Your application code...

# After some time
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

**Solutions:**

1. **Check for Unclosed Sessions**
   ```python
   # Enable session tracking
   manager.engine.enable_session_tracking()
   
   # Periodically check
   active = len(manager.engine.get_active_sessions())
   if active > 10:  # Adjust threshold
       logger.warning(f"High number of active sessions: {active}")
   ```

2. **Review Large Result Sets**
   ```python
   # ❌ BAD: Loading millions of records
   all_users = session.query(User).all()  # Loads everything!
   
   # ✅ GOOD: Stream results
   for user in session.query(User).yield_per(1000):
       process(user)
   
   # ✅ GOOD: Use pagination
   result = paginate_with_meta(query, page=1, page_size=100)
   ```

3. **Clear Session Cache**
   ```python
   # If processing many records in one session
   session.expunge_all()  # Clear session cache
   ```

4. **Restart Application**
   ```bash
   # Immediate fix
   systemctl restart myapp
   ```

**Prevention:**
- Always use context managers or decorators
- Monitor application memory usage
- Use streaming for large result sets
- Set up memory alerts (alert if >80% usage)
- Regular application restarts (daily/weekly)

---

### Issue 5: Deadlocks

**Symptoms:**
- Error: `DeadlockDetected`
- Error: `Lock wait timeout exceeded`
- Transactions hang then fail

**Diagnosis:**
```python
# Check for deadlocks in logs
# PostgreSQL
SELECT * FROM pg_stat_activity
WHERE wait_event_type = 'Lock';

# MySQL
SHOW ENGINE INNODB STATUS\G
```

**Solutions:**

1. **Use Retry Decorator**
   ```python
   from sqlalchemy_engine_kit import with_retry_session
   
   @with_retry_session(max_retries=3, retry_on_deadlock=True)
   def update_balance(session, account_id, amount):
       account = session.query(Account).get(account_id)
       account.balance += amount
       session.commit()
   ```

2. **Consistent Lock Ordering**
   ```python
   # ❌ BAD: Inconsistent ordering causes deadlocks
   # Transaction 1: Lock A → Lock B
   # Transaction 2: Lock B → Lock A
   
   # ✅ GOOD: Always lock in same order
   def transfer(session, from_id, to_id, amount):
       # Always lock lower ID first
       first_id, second_id = sorted([from_id, to_id])
       
       account1 = session.query(Account).with_for_update().get(first_id)
       account2 = session.query(Account).with_for_update().get(second_id)
       
       # Perform transfer...
   ```

3. **Shorter Transactions**
   ```python
   # ❌ BAD: Long transaction holding locks
   with session.begin():
       user = session.query(User).get(user_id)
       send_email(user.email)  # External I/O in transaction!
       process_payment(user.id)  # External API call!
       user.updated_at = datetime.now()
   
   # ✅ GOOD: Short transaction
   send_email(user.email)  # Do I/O outside transaction
   process_payment(user.id)
   
   with session.begin():  # Quick database update only
       user = session.query(User).get(user_id)
       user.updated_at = datetime.now()
   ```

**Prevention:**
- Use `with_retry_session` for write operations
- Keep transactions short
- Lock resources in consistent order
- Avoid external I/O during transactions
- Monitor deadlock occurrences

---

### Issue 6: Migration Failures

**Symptoms:**
- Migration command fails
- Database schema out of sync
- Application crashes on startup

**Diagnosis:**
```python
from sqlalchemy_engine_kit import get_current_revision, get_head_revision

current = get_current_revision(manager.engine)
head = get_head_revision(manager.engine)

print(f"Current revision: {current}")
print(f"Head revision: {head}")
print(f"Needs upgrade: {current != head}")
```

**Solutions:**

1. **Check Migration Status**
   ```python
   from sqlalchemy_engine_kit import MigrationManager
   
   mig = MigrationManager(manager.engine)
   
   for revision in mig.history():
       print(f"{revision['revision']}: {revision['doc']}")
   ```

2. **Rollback Failed Migration**
   ```python
   # Downgrade to previous version
   mig.downgrade("-1")  # Go back one revision
   
   # Or specific revision
   mig.downgrade("abc123")
   ```

3. **Manual Schema Fix**
   ```bash
   # Connect to database
   psql -h db.example.com -U app_user -d myapp
   
   # Check alembic_version table
   SELECT * FROM alembic_version;
   
   # Manually set version if needed (CAREFUL!)
   DELETE FROM alembic_version;
   INSERT INTO alembic_version VALUES ('correct_revision_id');
   ```

4. **Rebuild from Scratch** (Development Only!)
   ```python
   # ⚠️ WARNING: This destroys all data!
   from myapp.models import Base
   
   Base.metadata.drop_all(manager.engine._engine)
   Base.metadata.create_all(manager.engine._engine)
   
   # Re-stamp with current version
   mig.stamp("head")
   ```

**Prevention:**
- Test migrations in staging first
- Always backup before migrations
- Use `upgrade_safe` for production
- Review generated SQL before applying
- Keep migration reversible (downgrade)

---

## Emergency Procedures

### Complete System Failure

1. **Check Database Server**
   ```bash
   systemctl status postgresql
   # or
   systemctl status mysql
   ```

2. **Check Application Logs**
   ```bash
   tail -f /var/log/myapp/error.log
   # Look for database errors
   ```

3. **Restart Application**
   ```bash
   systemctl restart myapp
   ```

4. **If Database is Down**
   ```bash
   systemctl restart postgresql
   # Wait for database to be ready
   pg_isready -h localhost
   ```

5. **Restore from Backup** (if corrupted)
   ```bash
   # PostgreSQL
   psql -h localhost -U postgres < /backups/myapp_backup.sql
   ```

### Rollback Deployment

```bash
# 1. Stop new version
systemctl stop myapp

# 2. Rollback database migrations
alembic downgrade <previous_revision>

# 3. Deploy previous version
git checkout <previous_tag>
pip install -r requirements.txt

# 4. Start application
systemctl start myapp

# 5. Verify health
curl http://localhost:8000/health
```

## Monitoring Queries

### PostgreSQL Health Check
```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Long running queries
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

-- Database size
SELECT pg_database_size('myapp') / 1024 / 1024 AS size_mb;

-- Lock contention
SELECT * FROM pg_locks WHERE NOT granted;
```

### MySQL Health Check
```sql
-- Active connections
SHOW PROCESSLIST;

-- InnoDB status
SHOW ENGINE INNODB STATUS\G

-- Database size
SELECT table_schema, 
       SUM(data_length + index_length) / 1024 / 1024 AS size_mb
FROM information_schema.tables
GROUP BY table_schema;
```

## Contact Information

- **On-Call Engineer**: [Your Pager Duty/Slack]
- **Database Team**: [Contact Info]
- **Monitoring Dashboard**: [Grafana/Datadog URL]
- **Log Aggregation**: [Kibana/Splunk URL]

## Escalation Path

1. **Level 1**: Application Developer (5 min response)
2. **Level 2**: Database Administrator (15 min response)
3. **Level 3**: Infrastructure Team (30 min response)
4. **Level 4**: Vendor Support (1 hour response)



