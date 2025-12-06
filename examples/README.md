# Usage Examples

Bu klasör, `sqlalchemy-engine-kit` kütüphanesinin kullanım örneklerini içerir.

## Örnekler

### 1. `basic_usage.py` - Temel Kullanım
Temel özellikleri gösterir:
- Database başlatma
- Model tanımlama
- Decorator kullanımı (`@with_session`)
- CRUD işlemleri

**Çalıştırma:**
```bash
# Development ortamında (PYTHONPATH gerekli)
PYTHONPATH=src python examples/basic_usage.py

# Veya paket yüklüyse
python examples/basic_usage.py
```

### 2. `transaction_example.py` - Transaction Yönetimi
Atomic transaction örneği:
- Para transferi senaryosu
- `@with_transaction` decorator kullanımı
- Hata durumunda otomatik rollback

**Çalıştırma:**
```bash
# Development ortamında (PYTHONPATH gerekli)
PYTHONPATH=src python examples/transaction_example.py

# Veya paket yüklüyse
python examples/transaction_example.py
```

### 3. `flask_integration.py` - Flask Entegrasyonu
Flask web framework ile entegrasyon:
- REST API örneği
- Decorator'lar ile route handler'lar
- Health check endpoint

**Çalıştırma:**
```bash
# Development ortamında (PYTHONPATH gerekli)
PYTHONPATH=src python examples/flask_integration.py

# Veya paket yüklüyse
python examples/flask_integration.py
```

### 4. `migration_example.py` - Alembic Migration
Alembic migration kullanımı:
- Alembic başlatma ve yapılandırma
- Migration oluşturma
- Migration uygulama
- Migration geçmişi görüntüleme

**Çalıştırma:**
```bash
# Alembic yüklü olmalı
pip install alembic

# Development ortamında (PYTHONPATH gerekli)
PYTHONPATH=src python examples/migration_example.py

# Veya paket yüklüyse
python examples/migration_example.py
```

Sonra başka bir terminal'de:
```bash
# Ürün listele
curl http://127.0.0.1:5000/products

# Ürün oluştur
curl -X POST http://127.0.0.1:5000/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "price": 999.99, "description": "Gaming laptop"}'

# Health check
curl http://127.0.0.1:5000/health
```

## Gereksinimler

Tüm örnekler için:
```bash
pip install sqlalchemy-engine-kit
```

Flask örneği için ek olarak:
```bash
pip install flask
```

Migration örneği için ek olarak:
```bash
pip install alembic
```

## Notlar

- Örnekler SQLite kullanır (development için)
- Production'da PostgreSQL veya MySQL kullanın
- Tüm örnekler otomatik olarak database dosyalarını oluşturur
- Örnekleri çalıştırdıktan sonra `.db` dosyalarını silebilirsiniz

