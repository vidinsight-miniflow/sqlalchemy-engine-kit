import enum


class DatabaseType(str, enum.Enum):
    """Desteklenen veritabanı tipleri.

    Bu enum, projede desteklenen veritabanlarını tanımlar ve her tip için
    varsayılan port, kimlik bilgisi gereksinimi, JSONB/ENUM desteği ile
    gösterim/driver adları gibi yardımcı bilgileri sağlar.
    """

    # --------------------------------------------------------------
    # Enum üyeleri — desteklenen veritabanı tipleri
    # --------------------------------------------------------------

    SQLITE = "sqlite"           # Dosya tabanlı, tek dosyalı küçük veritabanı
    MYSQL = "mysql"             # MySQL (veya MariaDB) sunucu tabanlı veritabanı
    POSTGRESQL = "postgresql"   # PostgreSQL — güçlü JSONB desteğiyle bilinir


    # --------------------------------------------------------------
    # Yardımcı metotlar
    # --------------------------------------------------------------

    def default_port(self) -> int:
        """Varsayılan bağlantı portunu döndürür."""
        ports = {
            DatabaseType.SQLITE: 0,         
            DatabaseType.MYSQL: 3306,
            DatabaseType.POSTGRESQL: 5432,
        }
        return ports[self]


    def requires_credentials(self) -> bool:
        """Kullanıcı adı/şifre gerekip gerekmediğini döndürür."""
        return self != DatabaseType.SQLITE


    def supports_jsonb(self) -> bool:
        """JSONB desteği olup olmadığını döndürür (yalnızca PostgreSQL)."""
        return self == DatabaseType.POSTGRESQL


    def supports_native_enum(self) -> bool:
        """Yerel ENUM desteği olup olmadığını döndürür (PostgreSQL, MySQL)."""
        return self in [DatabaseType.POSTGRESQL, DatabaseType.MYSQL]


    # --------------------------------------------------------------
    # Özellikler (properties)
    # --------------------------------------------------------------

    @property
    def display_name(self) -> str:
        """Okunabilir gösterim adını döndürür."""
        names = {
            DatabaseType.SQLITE: "SQLite",
            DatabaseType.POSTGRESQL: "PostgreSQL",
            DatabaseType.MYSQL: "MySQL",
        }
        return names[self]


    @property
    def driver_name(self) -> str:
        """SQLAlchemy ile kullanılacak önerilen driver adını döndürür."""
        drivers = {
            DatabaseType.SQLITE: "sqlite",
            DatabaseType.POSTGRESQL: "postgresql",
            DatabaseType.MYSQL: "mysql+pymysql",
        }
        return drivers[self]

    # --------------------------------------------------------------
    # Class methods for utility operations
    # --------------------------------------------------------------

    @classmethod
    def all_types(cls) -> list['DatabaseType']:
        """Tüm desteklenen veritabanı tiplerini döndürür.
        
        Returns:
            Tüm DatabaseType enum üyelerinin listesi
        
        Examples:
            >>> for db_type in DatabaseType.all_types():
            ...     print(db_type.display_name)
            SQLite
            MySQL
            PostgreSQL
        """
        return list(cls)

    @classmethod
    def network_based(cls) -> list['DatabaseType']:
        """Sadece ağ tabanlı veritabanlarını döndürür (SQLite hariç).
        
        Returns:
            Kimlik bilgisi gerektiren (network-based) veritabanı tiplerinin listesi
        
        Examples:
            >>> network_dbs = DatabaseType.network_based()
            >>> for db_type in network_dbs:
            ...     print(db_type.display_name)
            MySQL
            PostgreSQL
        """
        return [t for t in cls if t.requires_credentials()]