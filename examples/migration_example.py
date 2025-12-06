#!/usr/bin/env python3
"""
Migration Example - sqlalchemy-engine-kit

Bu örnek, Alembic migration'larının nasıl kullanılacağını gösterir.
Not: Alembic yüklü olmalıdır (pip install alembic)
"""

import os
import sys
from pathlib import Path

# Alembic kontrolü
try:
    from alembic import config as alembic_config
    from alembic import command
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False
    print("⚠️  Alembic yüklü değil. Migration örneği için gerekli:")
    print("   pip install alembic")
    sys.exit(1)

from sqlalchemy_engine_kit import (
    DatabaseManager,
    get_sqlite_config,
    Base,
    TimestampMixin,
)
from sqlalchemy import Column, Integer, String, Float, Boolean


# Model Tanımlama
class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class Product(Base, TimestampMixin):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(500))


def setup_alembic(manager, migration_dir: str = "alembic"):
    """Alembic'i başlat ve yapılandır."""
    print(f"\n📦 Setting up Alembic in '{migration_dir}'...")
    
    # Migration dizinini oluştur
    migration_path = Path(migration_dir)
    if migration_path.exists():
        print(f"   ⚠️  '{migration_dir}' dizini zaten var, temizleniyor...")
        import shutil
        shutil.rmtree(migration_path)
    
    # Alembic'i subprocess ile başlat
    try:
        import subprocess
        
        # Alembic init komutunu çalıştır
        result = subprocess.run(
            ["alembic", "init", migration_dir],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Alembic init failed: {result.stderr}")
        
        print(f"   ✅ Alembic initialized in '{migration_dir}'")
        
        # Alembic config'i yapılandır
        from alembic.config import Config
        # alembic.ini ana dizinde oluşturulur
        alembic_ini_path = Path("alembic.ini")
        if not alembic_ini_path.exists():
            # Eğer yoksa migration_dir içinde ara
            alembic_ini_path = Path(migration_dir) / "alembic.ini"
        
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", str(manager.engine._engine.url))
        
        # script_location'ı alembic.ini'den oku veya ayarla
        if not alembic_cfg.get_main_option("script_location"):
            alembic_cfg.set_main_option("script_location", migration_dir)
        
        # env.py'yi güncelle - target_metadata ekle
        env_py_path = Path(migration_dir) / "env.py"
        if env_py_path.exists():
            env_content = env_py_path.read_text()
            # target_metadata'yi ekle
            if "target_metadata = None" in env_content:
                env_content = env_content.replace(
                    "target_metadata = None",
                    "# Import models for autogenerate\n"
                    "from __main__ import Base\n"
                    "target_metadata = Base.metadata"
                )
                env_py_path.write_text(env_content)
                print(f"   ✅ Updated env.py with target_metadata")
        
        return alembic_cfg, migration_dir
        
    except FileNotFoundError:
        print(f"   ❌ Alembic command not found. Make sure alembic is installed:")
        print(f"      pip install alembic")
        return None, None
    except Exception as e:
        print(f"   ❌ Alembic initialization failed: {e}")
        print(f"   📝 Alembic'i manuel olarak başlatabilirsiniz:")
        print(f"      alembic init {migration_dir}")
        return None, None


def create_initial_migration(alembic_cfg, migration_dir: str):
    """İlk migration'ı oluştur."""
    print("\n📝 Creating initial migration...")
    
    try:
        from alembic import command
        
        command.revision(
            alembic_cfg,
            autogenerate=True,
            message="Initial migration"
        )
        print("   ✅ Initial migration created")
        
        # Oluşturulan migration dosyasını göster
        versions_dir = Path(migration_dir) / "versions"
        if versions_dir.exists():
            migration_files = list(versions_dir.glob("*.py"))
            if migration_files:
                print(f"   📄 Migration file: {migration_files[0].name}")
        
    except Exception as e:
        print(f"   ❌ Migration creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def run_migrations(alembic_cfg, connection, target: str = "head"):
    """Migration'ları çalıştır."""
    print(f"\n🚀 Running migrations to '{target}'...")
    
    try:
        from alembic import command
        
        # Alembic upgrade komutunu kullan
        command.upgrade(alembic_cfg, target)
        
        print(f"   ✅ Migrations applied successfully")
        return True
    except Exception as e:
        print(f"   ❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_current_revision(alembic_cfg, connection):
    """Mevcut revision'ı göster."""
    try:
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        
        script = ScriptDirectory.from_config(alembic_cfg)
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
        
        if current_rev:
            print(f"   📌 Current revision: {current_rev}")
        else:
            print(f"   📌 No migrations applied yet")
        
        return current_rev
    except Exception as e:
        print(f"   ⚠️  Could not get current revision: {e}")
        return None


def show_migration_history(alembic_cfg):
    """Migration geçmişini göster."""
    print("\n📚 Migration History:")
    
    try:
        from alembic.script import ScriptDirectory
        
        script = ScriptDirectory.from_config(alembic_cfg)
        revisions = list(script.walk_revisions())
        
        if not revisions:
            print("   (No migrations found)")
            return
        
        for rev in reversed(revisions):  # En yeni önce
            print(f"   - {rev.revision[:8]}... {rev.doc}")
            
    except Exception as e:
        print(f"   ⚠️  Could not get history: {e}")


def main():
    """Ana program."""
    print("=" * 60)
    print("Migration Example - Alembic Integration")
    print("=" * 60)
    
    # Database dosyasını temizle
    db_file = "migration_example.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"✅ Cleaned up old database: {db_file}")
    
    # Database başlat
    print("\n1. Initializing database...")
    config = get_sqlite_config(db_file)
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)
    print("   ✅ Database initialized")
    
    # Alembic setup
    print("\n2. Setting up Alembic...")
    migration_dir = "alembic_migrations"
    alembic_cfg, migration_dir = setup_alembic(manager, migration_dir)
    
    if not alembic_cfg:
        print("\n❌ Alembic setup failed. Exiting.")
        manager.stop()
        return
    
    # İlk migration oluştur
    print("\n3. Creating initial migration...")
    if not create_initial_migration(alembic_cfg, migration_dir):
        print("\n❌ Migration creation failed. Exiting.")
        manager.stop()
        return
    
    # Migration geçmişini göster
    show_migration_history(alembic_cfg)
    
    # Connection'ı al
    connection = manager.engine._engine.connect()
    
    try:
        # Migration'ları çalıştır
        print("\n4. Applying migrations...")
        if not run_migrations(alembic_cfg, connection, "head"):
            print("\n❌ Migration application failed. Exiting.")
            return
        
        # Mevcut revision'ı göster
        print("\n5. Checking current revision...")
        get_current_revision(alembic_cfg, connection)
    finally:
        connection.close()
    
    # Cleanup
    print("\n6. Cleaning up...")
    manager.stop()
    
    # Migration dosyalarını temizle (opsiyonel - non-interactive mode için skip)
    try:
        cleanup = input("\n   Migration dosyalarını silmek ister misiniz? (y/N): ").strip().lower()
        if cleanup == 'y':
            import shutil
            if Path(migration_dir).exists():
                shutil.rmtree(migration_dir)
                print(f"   ✅ Removed '{migration_dir}' directory")
            if Path("alembic.ini").exists():
                os.remove("alembic.ini")
                print(f"   ✅ Removed 'alembic.ini' file")
    except (EOFError, KeyboardInterrupt):
        # Non-interactive mode - dosyaları bırak
        print(f"\n   ℹ️  Migration dosyaları korundu:")
        print(f"      - {migration_dir}/")
        print(f"      - alembic.ini")
    
    print("\n" + "=" * 60)
    print("Migration example completed! ✅")
    print("=" * 60)
    print("\n💡 Notlar:")
    print("   - Migration dosyaları 'alembic_migrations/versions/' klasöründe")
    print("   - Yeni migration oluşturmak için:")
    print("     alembic revision --autogenerate -m 'migration message'")
    print("   - Migration uygulamak için:")
    print("     alembic upgrade head")
    print("   - Migration geri almak için:")
    print("     alembic downgrade -1")


if __name__ == "__main__":
    main()

