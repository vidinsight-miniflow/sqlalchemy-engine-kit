from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from ..core.exceptions import InvalidInputError


@dataclass
class EngineConfig:
    """SQLAlchemy engine ve oturum ayarları.

    Bu sınıf, `sqlalchemy.create_engine()` çağrısında kullanılan havuz/bağlantı
    parametreleri ile ORM oturum (`Session`) davranışlarını tek bir yapı içinde
    toplar. Varsayılan değerler üretim kullanımına uygundur; gerektiğinde
    özelleştirilebilir.
    """

    # --------------------------------------------------------------
    # CONNECTION POOL SETTINGS
    # --------------------------------------------------------------
    pool_size: int = 10  
    #   Aynı anda açık tutulabilecek maksimum bağlantı (connection) sayısı.
    #   Örneğin 10 yaparsan, veritabanına aynı anda 10 aktif bağlantı açılır.
    #   Performans açısından genelde production’da 5-20 arası olur.

    max_overflow: int = 20  
    #   pool_size dolduğunda, ek olarak açılabilecek *geçici* bağlantı sayısı.
    #   pool_size = 10, max_overflow = 20 → toplam 30 bağlantıya kadar çıkabilir.
    #   Bu bağlantılar “overflow” durumlarında (yüksek trafik anlarında) kullanılır.

    pool_timeout: int = 30  
    #   Connection pool doluysa, yeni bir bağlantı almak için maksimum bekleme süresi (saniye cinsinden).
    #   Örneğin 30 saniye içinde bağlantı boşalmazsa TimeoutError fırlatılır.
    #   Uzun işlemler varsa artırılabilir.

    pool_recycle: int = 3600  
    #   Her bağlantının ne kadar süre sonra otomatik olarak yenileneceğini (recycle edileceğini) belirler.
    #   Genelde 3600 (1 saat) kullanılır.
    #   Uzun süreli bağlantıların bozulmasını (örneğin MySQL’de “MySQL has gone away” hatası) önler.

    pool_pre_ping: bool = True  
    #   SQLAlchemy her bağlantıyı kullanmadan önce “ping” (SELECT 1) atarak bağlantının sağlıklı olup olmadığını kontrol eder.
    #   False yapılırsa bozuk bağlantılar fark edilmeden hata verebilir.
    #   Production’da her zaman True olması önerilir.
    

    # --------------------------------------------------------------
    # DEBUG AND LOGGING SETTINGS
    # --------------------------------------------------------------
    echo: bool = False  
    #   True olursa tüm SQL sorgularını konsola loglar.
    #   Geliştirme (development) aşamasında faydalıdır.
    #   Production’da gereksiz log yükü yaratır, o yüzden genelde False tutulur.

    echo_pool: bool = False  
    #   Connection pool aktivitelerini (bağlantı açma, kapama vs.) loglar.
    #   Debug amaçlı kullanılır.
    #   Production’da gereksizdir, False kalmalıdır.


    # --------------------------------------------------------------
    # SESSION MANAGEMENT SETTINGS
    # --------------------------------------------------------------
    autocommit: bool = False  
    #   SQLAlchemy session işlemlerinde her query’nin otomatik commit edilip edilmeyeceğini belirler.
    #   False → Transaction’ları manuel kontrol edersin (recommended).
    #   True → Her query otomatik commit edilir (risklidir).

    autoflush: bool = True  
    #   True olursa, session üzerindeki değişiklikler (INSERT/UPDATE/DELETE) query çalışmadan önce otomatik olarak veritabanına yansıtılır.
    #   False yapılırsa manuel flush gerekir.
    #   Genelde True bırakılır.

    expire_on_commit: bool = True  
    #   Commit sonrası, session’daki objeler “expired” (geçersiz) hale gelir.
    #   Sonraki erişimde DB’den yeniden yüklenir.
    #   True → her zaman en güncel veriyi alırsın.
    #   False → bellekten veri çekebilirsin ama güncel olmayabilir.

    isolation_level: Optional[str] = None  
    #   Transaction isolation seviyesini belirler. (örn: 'READ COMMITTED', 'SERIALIZABLE')
    #   Belirtilmezse veritabanının varsayılan seviyesi kullanılır.
    #   Farklı seviyeler, aynı tabloya eşzamanlı erişimde “kirli okuma” veya “deadlock” riskini etkiler.

    connect_args: Dict[str, Any] = field(default_factory=dict)  
    #   create_engine fonksiyonuna özel ek bağlantı argümanları eklemeni sağlar.
    #   Örnek: {'sslmode': 'require'} gibi özel bağlantı parametreleri.


    # --------------------------------------------------------------
    # METHODS
    # --------------------------------------------------------------
    def __post_init__(self):
        """Havuz ve zaman aşımı alanlarını doğrular.

        - `pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle` tamsayıya
          çevrilir ve negatif değerlere izin verilmez.
        """
        for name in [
            'pool_size', 'max_overflow', 'pool_timeout', 'pool_recycle'
        ]:
            value = getattr(self, name)
            try:
                int_value = int(value)
            except (TypeError, ValueError):
                raise InvalidInputError(field_name=name)
            if int_value < 0:
                raise InvalidInputError(field_name=name)
            setattr(self, name, int_value)

    def __repr__(self) -> str:
        """Temel engine ayarlarını özetleyen metinsel gösterim."""
        return (
            "EngineConfig("
            f"pool_size={self.pool_size}, max_overflow={self.max_overflow}, "
            f"timeout={self.pool_timeout}, recycle={self.pool_recycle}, "
            f"pre_ping={self.pool_pre_ping}, echo={self.echo}, echo_pool={self.echo_pool}, "
            f"isolation_level={self.isolation_level}"
            ")"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Tüm alanların sözlük temsili (engine + session)."""
        return {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': self.pool_pre_ping,
            'echo': self.echo,
            'echo_pool': self.echo_pool,
            'isolation_level': self.isolation_level,
            'connect_args': self.connect_args,
            # Session-related settings are included for completeness; not used by create_engine
            'autocommit': self.autocommit,
            'autoflush': self.autoflush,
            'expire_on_commit': self.expire_on_commit,
        }

    def to_engine_kwargs(self) -> Dict[str, Any]:
        """`sqlalchemy.create_engine` için geçerli anahtarlar."""
        return {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': self.pool_pre_ping,
            'echo': self.echo,
            'echo_pool': self.echo_pool,
            'isolation_level': self.isolation_level,
            'connect_args': self.connect_args,
        }

    def to_session_kwargs(self) -> Dict[str, Any]:
        """`sqlalchemy.orm.sessionmaker` / `Session` için anahtarlar."""
        return {
            'autocommit': self.autocommit,
            'autoflush': self.autoflush,
            'expire_on_commit': self.expire_on_commit,
        }

    def merge(self, other: 'EngineConfig') -> 'EngineConfig':
        """Başka bir EngineConfig ile birleştir (override pattern).
        
        Bu metot, mevcut config'i başka bir config ile birleştirir.
        `other` config'deki değerler, mevcut config'deki değerleri override eder.
        None değerler override edilmez.
        
        Args:
            other: Birleştirilecek EngineConfig (değerleri override eder)
        
        Returns:
            Birleştirilmiş yeni EngineConfig örneği
        
        Examples:
            >>> base = EngineConfig(pool_size=10)
            >>> custom = EngineConfig(pool_size=50, max_overflow=30)
            >>> merged = base.merge(custom)
            >>> merged.pool_size  # 50 (custom'dan)
            >>> merged.max_overflow  # 30 (custom'dan)
            >>> merged.pool_timeout  # 30 (base'den, custom'da None)
        """
        from dataclasses import replace
        
        # Get all fields from other that are not None
        override_fields = {}
        for field_name in ['pool_size', 'max_overflow', 'pool_timeout', 'pool_recycle',
                          'pool_pre_ping', 'echo', 'echo_pool', 'autocommit',
                          'autoflush', 'expire_on_commit', 'isolation_level']:
            other_value = getattr(other, field_name)
            if other_value is not None:
                override_fields[field_name] = other_value
        
        # Merge connect_args
        merged_connect_args = dict(self.connect_args)
        merged_connect_args.update(other.connect_args)
        override_fields['connect_args'] = merged_connect_args
        
        return replace(self, **override_fields)

    @classmethod
    def for_high_concurrency(cls) -> 'EngineConfig':
        """Yüksek eşzamanlılık için optimize edilmiş config.
        
        API sunucuları veya yüksek trafikli uygulamalar için uygundur.
        
        Returns:
            Yüksek eşzamanlılık için optimize edilmiş EngineConfig
        
        Examples:
            >>> config = EngineConfig.for_high_concurrency()
            >>> config.pool_size  # 50
            >>> config.max_overflow  # 50
        """
        return cls(
            pool_size=50,
            max_overflow=50,
            pool_timeout=120,
            pool_recycle=3600,
            pool_pre_ping=True,
            isolation_level='READ_COMMITTED',
        )

    @classmethod
    def for_development(cls) -> 'EngineConfig':
        """Geliştirme ortamı için optimize edilmiş config.
        
        Debugging ve development için uygundur. SQL logging açık.
        
        Returns:
            Geliştirme ortamı için optimize edilmiş EngineConfig
        
        Examples:
            >>> config = EngineConfig.for_development()
            >>> config.echo  # True (SQL logging enabled)
            >>> config.pool_size  # 5 (smaller pool for dev)
        """
        return cls(
            pool_size=5,
            max_overflow=5,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=True,  # Enable SQL logging for debugging
            echo_pool=False,
            isolation_level=None,  # Use database default
        )

    @classmethod
    def for_single_thread(cls) -> 'EngineConfig':
        """Tek thread için optimize edilmiş config.
        
        Batch job'lar veya tek thread uygulamalar için uygundur.
        
        Returns:
            Tek thread için optimize edilmiş EngineConfig
        
        Examples:
            >>> config = EngineConfig.for_single_thread()
            >>> config.pool_size  # 1
            >>> config.max_overflow  # 0
        """
        return cls(
            pool_size=1,
            max_overflow=0,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            isolation_level='READ_COMMITTED',
        )