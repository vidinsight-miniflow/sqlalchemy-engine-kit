#!/usr/bin/env python3
"""
Transaction Example - sqlalchemy-engine-kit

Bu örnek, transaction yönetimini gösterir.
"""

from sqlalchemy_engine_kit import (
    DatabaseManager,
    get_sqlite_config,
    with_transaction,
    with_readonly_session,
    Base,
)
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import Session


# Model Tanımlama
class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    balance = Column(Float, default=0.0, nullable=False)


def init_database():
    """Database'i başlat."""
    import os
    db_file = "transaction_example.db"
    # Önceki database dosyasını sil (temiz başlangıç için)
    if os.path.exists(db_file):
        os.remove(db_file)
    
    config = get_sqlite_config(db_file)
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)
    Base.metadata.create_all(manager.engine._engine)
    return manager


@with_transaction()
def create_account(session: Session, name: str, initial_balance: float = 0.0) -> tuple[int, str, float]:
    """Hesap oluştur ve (id, name, balance) tuple döndür."""
    account = Account(name=name, balance=initial_balance)
    session.add(account)
    session.flush()
    account_id = account.id
    account_name = account.name
    account_balance = account.balance
    print(f"✅ Created account: {account_name} (Balance: ${account_balance:.2f})")
    return (account_id, account_name, account_balance)


@with_transaction()
def transfer_money(
    session: Session,
    from_account_id: int,
    to_account_id: int,
    amount: float
) -> bool:
    """Para transferi yap (atomic transaction)."""
    from_account = session.query(Account).filter_by(id=from_account_id).first()
    to_account = session.query(Account).filter_by(id=to_account_id).first()
    
    if not from_account:
        raise ValueError(f"Account {from_account_id} not found")
    if not to_account:
        raise ValueError(f"Account {to_account_id} not found")
    if from_account.balance < amount:
        raise ValueError(f"Insufficient balance in account {from_account_id}")
    
    # Transfer işlemi
    from_account.balance -= amount
    to_account.balance += amount
    
    print(f"✅ Transferred ${amount:.2f} from {from_account.name} to {to_account.name}")
    print(f"   {from_account.name} balance: ${from_account.balance:.2f}")
    print(f"   {to_account.name} balance: ${to_account.balance:.2f}")
    
    return True


@with_readonly_session()
def get_account_balance(session: Session, account_id: int) -> float:
    """Hesap bakiyesini getir."""
    account = session.query(Account).filter_by(id=account_id).first()
    if account:
        return account.balance
    return 0.0


def main():
    """Ana program."""
    print("=" * 60)
    print("Transaction Example - Atomic Money Transfer")
    print("=" * 60)
    
    # Database başlat
    manager = init_database()
    
    # Hesaplar oluştur
    print("\n1. Creating accounts...")
    account1_id, account1_name, account1_balance = create_account(name="Alice", initial_balance=1000.0)
    account2_id, account2_name, account2_balance = create_account(name="Bob", initial_balance=500.0)
    
    # Bakiye kontrolü
    print("\n2. Initial balances...")
    print(f"   {account1_name}: ${get_account_balance(account1_id):.2f}")
    print(f"   {account2_name}: ${get_account_balance(account2_id):.2f}")
    
    # Para transferi
    print("\n3. Transferring money...")
    try:
        transfer_money(
            from_account_id=account1_id,
            to_account_id=account2_id,
            amount=200.0
        )
    except ValueError as e:
        print(f"❌ Transfer failed: {e}")
    
    # Final bakiyeler
    print("\n4. Final balances...")
    print(f"   {account1_name}: ${get_account_balance(account1_id):.2f}")
    print(f"   {account2_name}: ${get_account_balance(account2_id):.2f}")
    
    # Cleanup
    print("\n5. Cleaning up...")
    manager.stop()
    
    print("\n" + "=" * 60)
    print("Transaction example completed! ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()

