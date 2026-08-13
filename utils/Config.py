from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """ Database configuration """
    user: str
    password: str
    database: str
    host: str
    port: int

@dataclass
class LoadConfig:
    """ Load configuration for the intake of audio files """
    root_dir: str
    store_dir: str
    batch_size: int
    batch_id: int

    def __post_init__(self):  # force datatypes
        self.root_dir = str(self.root_dir)
        self.store_dir = str(self.store_dir)
        self.batch_size = int(self.batch_size)
        self.batch_id = int(self.batch_id)

@dataclass
class BirdnetConfig:
    """ BirdNet configuration for making predictions on audio files """
    workers: int
    batch_size: int
    overlap_s: float
    model_version: str

    def __post_init__(self):  # force datatypes
        self.workers = int(self.workers)
        self.batch_size = int(self.batch_size)
        self.overlap_s = float(self.overlap_s)
        self.model_version = str(self.model_version)

@dataclass
class GeoConfig:
    """ Geometric configuration for making generating species lists """
    model_version: str
    min_confidence: float

    def __post_init__(self):  # force datatypes
        self.model_version = str(self.model_version)
        self.min_confidence = float(self.min_confidence)



